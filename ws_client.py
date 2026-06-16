import argparse
import base64
import json
import re
import time
import wave
from json import JSONDecodeError
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import websocket

from audio_stream import AplayPcmStream, start_arecord_pcm


def funasr_start_payload(sample_rate: int, wav_name: str) -> str:
    return json.dumps(
        {
            "chunk_size": [5, 10, 5],
            "wav_name": wav_name,
            "is_speaking": True,
            "chunk_interval": 10,
            "itn": False,
            "mode": "2pass",
            "audio_fs": sample_rate,
            "wav_format": "pcm",
        },
        ensure_ascii=False,
    )


def funasr_finish_payload(sample_rate: int, wav_name: str) -> str:
    return json.dumps(
        {
            "chunk_size": [5, 10, 5],
            "wav_name": wav_name,
            "is_speaking": False,
            "chunk_interval": 10,
            "mode": "2pass",
            "audio_fs": sample_rate,
            "wav_format": "pcm",
        },
        ensure_ascii=False,
    )


def _iter_json_objects(text: str) -> Iterable[dict]:
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        try:
            obj, end = decoder.raw_decode(text, index)
        except JSONDecodeError:
            break
        if isinstance(obj, dict):
            yield obj
        index = end


def _merge_asr_text(current: str, incoming: str) -> str:
    if not incoming:
        return current
    if not current:
        return incoming
    if incoming.startswith(current):
        return incoming
    if current.startswith(incoming):
        return current
    if incoming in current:
        return current
    if current in incoming:
        return incoming
    return current + incoming


class WsClient:
    def __init__(self, config: dict):
        self.config = config
        self.ws_cfg = config["websocket"]
        self.device_id = config["device"]["device_id"]

    def check_funasr(self) -> None:
        ws = websocket.create_connection(self.ws_cfg["funasr_url"], timeout=5)
        ws.close()

    def check_agent(self) -> None:
        ws = websocket.create_connection(self.ws_cfg["agent_url"], timeout=5)
        ws.close()

    def transcribe_wav(self, wav_path: Union[str, Path]) -> str:
        wav_path = Path(wav_path)
        audio_cfg = self.config["audio"]
        sample_rate = int(audio_cfg.get("asr_sample_rate", 16000))
        chunk_ms = int(audio_cfg.get("chunk_ms", 20))
        wav_name = self.device_id

        with wave.open(str(wav_path), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            rate = wav.getframerate()
            if width != 2:
                raise ValueError(f"FunASR expects 16-bit PCM, got sample width {width}")
            if channels != 1:
                raise ValueError(f"FunASR expects mono PCM for this stage, got {channels} channels")
            if rate != sample_rate:
                raise ValueError(f"FunASR sample rate mismatch: wav={rate}, config={sample_rate}")
            pcm = wav.readframes(wav.getnframes())

        chunk_bytes = max(1, sample_rate * chunk_ms // 1000) * 2
        ws = websocket.create_connection(self.ws_cfg["funasr_url"], timeout=10)
        ws.settimeout(float(self.ws_cfg.get("receive_timeout", 8)))
        final_text = ""
        try:
            ws.send(funasr_start_payload(sample_rate, wav_name))
            for offset in range(0, len(pcm), chunk_bytes):
                ws.send_binary(pcm[offset : offset + chunk_bytes])
                time.sleep(chunk_ms / 1000.0)
            ws.send(funasr_finish_payload(sample_rate, wav_name))

            deadline = time.time() + float(self.ws_cfg.get("asr_final_timeout", 12))
            while time.time() < deadline:
                try:
                    message = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if not isinstance(message, str):
                    continue
                for obj in _iter_json_objects(message):
                    text = obj.get("text") or ""
                    mode = obj.get("mode") or ""
                    if text and (mode == "2pass-offline" or obj.get("is_final") is True):
                        final_text = _merge_asr_text(final_text, text)
                    elif text and not final_text:
                        print(f"ASR preview: {text}", flush=True)
                if final_text:
                    return final_text
            return final_text
        finally:
            ws.close()

    def stream_asr_from_arecord(self, record_seconds: int) -> str:
        audio_cfg = self.config["audio"]
        sample_rate = int(audio_cfg.get("asr_sample_rate", 16000))
        chunk_ms = int(audio_cfg.get("chunk_ms", 20))
        chunk_bytes = max(1, sample_rate * chunk_ms // 1000) * 2 * int(audio_cfg.get("channels", 1))
        ws = websocket.create_connection(self.ws_cfg["funasr_url"], timeout=10)
        ws.settimeout(0.05)
        proc = start_arecord_pcm(self.config)
        final_text = ""
        online_text = ""
        start_at = time.time()
        try:
            ws.send(funasr_start_payload(sample_rate, self.device_id))
            while time.time() - start_at < record_seconds:
                if proc.stdout is None:
                    break
                chunk = proc.stdout.read(chunk_bytes)
                if not chunk:
                    break
                ws.send_binary(chunk)
                while True:
                    try:
                        message = ws.recv()
                    except websocket.WebSocketTimeoutException:
                        break
                    if isinstance(message, str):
                        for obj in _iter_json_objects(message):
                            text = obj.get("text") or ""
                            mode = obj.get("mode") or ""
                            if text and mode == "2pass-online":
                                online_text = text
                                print(f"ASR online: {text}", flush=True)
                            elif text and (mode == "2pass-offline" or obj.get("is_final") is True):
                                final_text = _merge_asr_text(final_text, text)
                                print(f"ASR offline: {final_text}", flush=True)
            ws.send(funasr_finish_payload(sample_rate, self.device_id))
            deadline = time.time() + float(self.ws_cfg.get("asr_final_timeout", 12))
            ws.settimeout(0.5)
            while time.time() < deadline:
                try:
                    message = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if not isinstance(message, str):
                    continue
                for obj in _iter_json_objects(message):
                    text = obj.get("text") or ""
                    mode = obj.get("mode") or ""
                    if text and (mode == "2pass-offline" or obj.get("is_final") is True):
                        final_text = _merge_asr_text(final_text, text)
                if final_text:
                    return final_text
            return final_text or online_text
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            ws.close()

    def ask_agent(self, message: str) -> Tuple[str, Optional[bytes]]:
        request = {
            "message": message,
            "user": self.ws_cfg.get("agent_user", self.device_id),
            "conversation_id": self.ws_cfg.get("conversation_id", ""),
            "sample_rate": self.config["audio"].get("tts_sample_rate", 24000),
        }
        ws = websocket.create_connection(self.ws_cfg["agent_url"], timeout=10)
        ws.settimeout(float(self.ws_cfg.get("receive_timeout", 20)))
        text_parts: List[str] = []
        audio_parts: List[bytes] = []
        buffer = ""
        try:
            ws.send(json.dumps(request, ensure_ascii=False))
            deadline = time.time() + float(self.ws_cfg.get("agent_timeout", 300))
            while time.time() < deadline:
                try:
                    message_obj = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if isinstance(message_obj, bytes):
                    audio_parts.append(message_obj)
                    continue
                buffer += message_obj
                consumed_any = False
                for obj in _iter_json_objects(buffer):
                    consumed_any = True
                    msg_type = obj.get("type")
                    if msg_type == "text":
                        delta = obj.get("delta") or ""
                        if delta:
                            text_parts.append(delta)
                            print(f"Agent text: {delta}", flush=True)
                    elif msg_type == "audio":
                        if obj.get("text") and not text_parts:
                            text_parts.append(obj["text"])
                        audio_b64 = obj.get("audio_base64")
                        if audio_b64:
                            audio_parts.append(self.decode_audio_base64(audio_b64))
                    elif msg_type == "done":
                        conv_id = obj.get("conversation_id")
                        if conv_id:
                            self.ws_cfg["conversation_id"] = conv_id
                        return "".join(text_parts), b"".join(audio_parts) if audio_parts else None
                    elif msg_type == "error":
                        raise RuntimeError(obj.get("message") or "chatAgent error")
                if consumed_any:
                    buffer = ""
            raise TimeoutError("chatAgent response timeout")
        finally:
            ws.close()

    def ask_agent_streaming(self, message: str) -> str:
        request = {
            "message": message,
            "user": self.ws_cfg.get("agent_user", self.device_id),
            "conversation_id": self.ws_cfg.get("conversation_id", ""),
            "sample_rate": self.config["audio"].get("tts_sample_rate", 24000),
        }
        ws = websocket.create_connection(self.ws_cfg["agent_url"], timeout=10)
        ws.settimeout(float(self.ws_cfg.get("receive_timeout", 20)))
        text_parts: List[str] = []
        player: Optional[AplayPcmStream] = None
        buffer = ""
        audio_streaming = False
        audio_b64_tail = ""
        try:
            ws.send(json.dumps(request, ensure_ascii=False))
            deadline = time.time() + float(self.ws_cfg.get("agent_timeout", 300))
            while time.time() < deadline:
                try:
                    message_obj = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue
                if isinstance(message_obj, bytes):
                    if player is None:
                        player = AplayPcmStream(self.config)
                    player.write(message_obj)
                    continue

                buffer += message_obj
                if audio_streaming:
                    consumed, done = self._consume_streaming_audio_b64(buffer, player, audio_b64_tail)
                    if consumed.player is not None:
                        player = consumed.player
                    audio_b64_tail = consumed.tail
                    buffer = buffer[consumed.offset :]
                    if not done:
                        continue
                    audio_streaming = False

                while buffer:
                    buffer = buffer.lstrip()
                    if not buffer:
                        break
                    if buffer.startswith("{") and '"type"' in buffer[:80] and '"audio_base64"' in buffer[:200]:
                        start = buffer.find('"audio_base64"')
                        quote = buffer.find('"', buffer.find(":", start) + 1)
                        if quote >= 0:
                            prefix = buffer[:quote]
                            for obj in _iter_json_objects(prefix + '""}'):
                                if obj.get("text") and not text_parts:
                                    text_parts.append(obj["text"])
                            audio_streaming = True
                            buffer = buffer[quote + 1 :]
                            consumed, done = self._consume_streaming_audio_b64(buffer, player, audio_b64_tail)
                            if consumed.player is not None:
                                player = consumed.player
                            audio_b64_tail = consumed.tail
                            buffer = buffer[consumed.offset :]
                            if not done:
                                break
                            audio_streaming = False
                            continue

                    msg_len = self._complete_json_len(buffer)
                    if msg_len == 0:
                        break
                    raw = buffer[:msg_len]
                    buffer = buffer[msg_len:]
                    for obj in _iter_json_objects(raw):
                        msg_type = obj.get("type")
                        if msg_type == "text":
                            delta = obj.get("delta") or ""
                            if delta:
                                text_parts.append(delta)
                                print(f"Agent text: {delta}", flush=True)
                        elif msg_type == "audio":
                            if obj.get("text") and not text_parts:
                                text_parts.append(obj["text"])
                            audio_b64 = obj.get("audio_base64")
                            if audio_b64:
                                if player is None:
                                    player = AplayPcmStream(self.config)
                                player.write(self.decode_audio_base64(audio_b64))
                        elif msg_type == "done":
                            conv_id = obj.get("conversation_id")
                            if conv_id:
                                self.ws_cfg["conversation_id"] = conv_id
                            return "".join(text_parts)
                        elif msg_type == "error":
                            raise RuntimeError(obj.get("message") or "chatAgent error")
            raise TimeoutError("chatAgent response timeout")
        finally:
            ws.close()
            if player is not None:
                player.close()

    @staticmethod
    def _complete_json_len(text: str) -> int:
        depth = 0
        in_string = False
        escape = False
        for idx, ch in enumerate(text):
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return idx + 1
        return 0

    class _AudioConsumeResult:
        def __init__(self, offset: int, tail: str, player: Optional[AplayPcmStream]):
            self.offset = offset
            self.tail = tail
            self.player = player

    def _consume_streaming_audio_b64(
        self,
        text: str,
        player: Optional[AplayPcmStream],
        tail: str,
    ) -> Tuple["WsClient._AudioConsumeResult", bool]:
        end = 0
        escaped = False
        close_quote = False
        while end < len(text):
            ch = text[end]
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                close_quote = True
                break
            end += 1

        b64_chars = re.sub(r"\\/", "/", text[:end])
        b64_chars = "".join(b64_chars.split())
        data = tail + b64_chars
        decode_len = (len(data) // 4) * 4
        if close_quote:
            decode_len = len(data)
        if decode_len > 0:
            chunk = data[:decode_len]
            try:
                pcm = base64.b64decode(chunk)
            except Exception:
                pcm = b""
            if pcm:
                if player is None:
                    player = AplayPcmStream(self.config)
                player.write(pcm)
        new_tail = data[decode_len:]
        offset = end + 1 if close_quote else end
        if close_quote:
            brace = text.find("}", offset)
            if brace >= 0:
                offset = brace + 1
        return self._AudioConsumeResult(offset, new_tail, player), close_quote

    @staticmethod
    def decode_audio_base64(value: str) -> bytes:
        return base64.b64decode(value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test WebSocket endpoints.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--check", choices=["funasr", "agent", "both"], default="both")
    parser.add_argument("--transcribe")
    parser.add_argument("--ask")
    parser.add_argument("--stream-record", type=int, help="Record N seconds from arecord and stream to FunASR.")
    parser.add_argument("--ask-streaming", help="Ask chatAgent and stream audio to aplay.")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as fp:
        config = json.load(fp)
    client = WsClient(config)
    if args.check in ("funasr", "both"):
        client.check_funasr()
        print("FunASR WebSocket OK")
    if args.check in ("agent", "both"):
        client.check_agent()
        print("chatAgent WebSocket OK")
    if args.transcribe:
        print(client.transcribe_wav(args.transcribe))
    if args.stream_record:
        print(client.stream_asr_from_arecord(args.stream_record))
    if args.ask:
        text, audio = client.ask_agent(args.ask)
        print(text)
        if audio:
            print(f"received audio bytes: {len(audio)}")
    if args.ask_streaming:
        print(client.ask_agent_streaming(args.ask_streaming))


if __name__ == "__main__":
    main()

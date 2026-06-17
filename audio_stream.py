import io
import subprocess
from typing import Optional
import wave

from audio_power import ensure_speaker_power


class AplayPcmStream:
    def __init__(self, config: dict, sample_rate: Optional[int] = None, channels: Optional[int] = None):
        self.config = config
        audio_cfg = config["audio"]
        self.device = audio_cfg.get("play_device", "default")
        self.sample_format = audio_cfg.get("sample_format", "S16_LE")
        self.sample_rate = int(sample_rate or audio_cfg.get("tts_sample_rate", 24000))
        self.channels = int(channels or audio_cfg.get("channels", 1))
        self.force_tts_sample_rate = bool(audio_cfg.get("force_tts_sample_rate", False))
        self.prefer_wav_header_rate = bool(audio_cfg.get("prefer_wav_header_rate", True))
        self.process: Optional[subprocess.Popen] = None
        self.broken = False

    def _start_raw(self) -> None:
        if self.process is not None:
            return
        ensure_speaker_power(self.config)
        self.process = subprocess.Popen(
            [
                "aplay",
                "-D",
                self.device,
                "-t",
                "raw",
                "-f",
                self.sample_format,
                "-r",
                str(self.sample_rate),
                "-c",
                str(self.channels),
                "--buffer-time=120000",
                "--period-time=30000",
            ],
            stdin=subprocess.PIPE,
        )

    def _play_wav_bytes(self, data: bytes) -> None:
        if self.force_tts_sample_rate:
            try:
                with wave.open(io.BytesIO(data), "rb") as wav:
                    channels = wav.getnchannels()
                    sample_width = wav.getsampwidth()
                    header_rate = wav.getframerate()
                    pcm = wav.readframes(wav.getnframes())
                if sample_width == 2:
                    self.sample_format = "S16_LE"
                if self.process is None:
                    self.channels = channels
                    if self.prefer_wav_header_rate and header_rate:
                        self.sample_rate = header_rate
                print(
                    f"TTS WAV chunk: header_rate={header_rate}Hz play_rate={self.sample_rate}Hz "
                    f"channels={channels} bytes={len(pcm)}",
                    flush=True,
                )
                self._write_raw(pcm)
                return
            except Exception as exc:
                print(f"force tts sample rate failed, fallback to WAV header: {exc}", flush=True)
        self.close()
        subprocess.run(["aplay", "-D", self.device], input=data, check=False)

    def write(self, data: bytes) -> None:
        if not data:
            return
        if data.startswith(b"RIFF"):
            self._play_wav_bytes(data)
            return
        self._write_raw(data)

    def _write_raw(self, data: bytes) -> None:
        if not data:
            return
        if self.broken:
            return
        self._start_raw()
        if self.process is None or self.process.stdin is None:
            return
        if self.process.poll() is not None:
            self.broken = True
            print(f"aplay exited before audio stream finished rc={self.process.returncode}", flush=True)
            return
        try:
            self.process.stdin.write(data)
            self.process.stdin.flush()
        except BrokenPipeError:
            self.broken = True
            print("aplay pipe closed while streaming audio; keep text result", flush=True)

    def close(self) -> None:
        if self.process is None:
            return
        if self.process.stdin is not None and not self.process.stdin.closed:
            try:
                self.process.stdin.close()
            except BrokenPipeError:
                pass
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.terminate()
        finally:
            self.process = None


def start_arecord_pcm(config: dict):
    audio_cfg = config["audio"]
    return subprocess.Popen(
        [
            "arecord",
            "-D",
            audio_cfg.get("record_device", "default"),
            "-f",
            audio_cfg.get("sample_format", "S16_LE"),
            "-r",
            str(audio_cfg.get("asr_sample_rate", 16000)),
            "-c",
            str(audio_cfg.get("channels", 1)),
            "-t",
            "raw",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

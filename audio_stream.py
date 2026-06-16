import subprocess
from typing import Optional


class AplayPcmStream:
    def __init__(self, config: dict, sample_rate: Optional[int] = None, channels: Optional[int] = None):
        audio_cfg = config["audio"]
        self.sample_rate = int(sample_rate or audio_cfg.get("tts_sample_rate", 24000))
        self.channels = int(channels or audio_cfg.get("channels", 1))
        self.process = subprocess.Popen(
            [
                "aplay",
                "-D",
                audio_cfg.get("play_device", "default"),
                "-f",
                audio_cfg.get("sample_format", "S16_LE"),
                "-r",
                str(self.sample_rate),
                "-c",
                str(self.channels),
            ],
            stdin=subprocess.PIPE,
        )

    def write(self, data: bytes) -> None:
        if not data or self.process.stdin is None:
            return
        self.process.stdin.write(data)
        self.process.stdin.flush()

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        self.process.wait(timeout=30)


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

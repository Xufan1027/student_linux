import argparse
import json
import subprocess
from pathlib import Path
from typing import Union

from audio_power import ensure_speaker_power


def play_audio(config: dict, audio_path: Union[str, Path]) -> None:
    audio_cfg = config["audio"]
    ensure_speaker_power(config)
    path = Path(audio_path)
    cmd = [
        "aplay",
        "-D",
        audio_cfg.get("play_device", "default"),
    ]
    try:
        header = path.read_bytes()[:4]
    except FileNotFoundError:
        header = b""
    if header != b"RIFF":
        cmd.extend(
            [
                "-f",
                audio_cfg.get("sample_format", "S16_LE"),
                "-r",
                str(audio_cfg.get("tts_sample_rate", 24000)),
                "-c",
                str(audio_cfg.get("channels", 1)),
            ]
        )
    cmd.append(str(path))
    subprocess.run(cmd, check=True)


def test_command() -> str:
    return "aplay -D hw:0,0 /tmp/student_test.wav"


def main() -> None:
    parser = argparse.ArgumentParser(description="Play an audio file with aplay.")
    parser.add_argument("audio_path", nargs="?", default="/tmp/student_test.wav")
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as fp:
        config = json.load(fp)
    play_audio(config, args.audio_path)


if __name__ == "__main__":
    main()

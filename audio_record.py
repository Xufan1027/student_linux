import argparse
import json
import subprocess
from pathlib import Path
from typing import Union


def record_wav(config: dict, output_path: Union[str, Path]) -> Path:
    audio_cfg = config["audio"]
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "arecord",
        "-D",
        audio_cfg.get("record_device", "default"),
        "-f",
        audio_cfg.get("sample_format", "S16_LE"),
        "-r",
        str(audio_cfg.get("asr_sample_rate", 16000)),
        "-c",
        str(audio_cfg.get("channels", 1)),
        "-d",
        str(audio_cfg.get("record_seconds", 5)),
        str(output),
    ]
    subprocess.run(cmd, check=True)
    return output


def test_command() -> str:
    return "arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 3 /tmp/student_test.wav"


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a WAV file with arecord.")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--output", default="/tmp/student_test.wav")
    args = parser.parse_args()
    with open(args.config, "r", encoding="utf-8") as fp:
        config = json.load(fp)
    path = record_wav(config, args.output)
    print(path)


if __name__ == "__main__":
    main()

from pathlib import Path


def ensure_speaker_power(config: dict) -> None:
    audio_cfg = config.get("audio", {})
    gpio = audio_cfg.get("speaker_gpio")
    if gpio in (None, "", False):
        return

    gpio = str(gpio)
    active_value = str(int(audio_cfg.get("speaker_gpio_active", 1)))
    gpio_dir = Path("/sys/class/gpio") / f"gpio{gpio}"
    try:
        if not gpio_dir.exists():
            Path("/sys/class/gpio/export").write_text(gpio)
        (gpio_dir / "direction").write_text("out")
        (gpio_dir / "value").write_text(active_value)
    except OSError as exc:
        print(f"speaker gpio enable failed: gpio{gpio}={active_value}: {exc}", flush=True)

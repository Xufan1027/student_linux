#!/bin/sh
# 板载麦克风增益初始化（ES8388，card 0）
amixer -c 0 cset numid=52 8  # Left Channel Capture Volume  -> 24dB
amixer -c 0 cset numid=53 8  # Right Channel Capture Volume -> 24dB
amixer -c 0 cset numid=70 0  # Differential Mux -> Line 1（板载麦克风）

# ATK-DLRK3506JS: pinctrl/speaker/spk-ctrl is gpio1-22, Linux GPIO 54.
# Keep the external speaker amplifier enabled for aplay/TTS playback.
if [ ! -d /sys/class/gpio/gpio54 ]; then
  echo 54 > /sys/class/gpio/export 2>/dev/null || true
fi
echo out > /sys/class/gpio/gpio54/direction 2>/dev/null || true
echo 1 > /sys/class/gpio/gpio54/value 2>/dev/null || true

echo "[audio_init] mic gain and speaker gpio initialized"

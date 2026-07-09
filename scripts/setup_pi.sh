#!/usr/bin/env bash
# Raspberry Pi setup: install OS packages + Python deps for the robogame demo.
#
# Run this ON the Pi, once, after the repo is in place:
#   cd ~/robogame
#   bash scripts/setup_pi.sh
#
# It installs: system camera/audio packages, a Python venv with the project's
# Pi dependencies, and keeps pygame (for the optional standalone player).
# Piper (live TTS) is NOT installed; the Pi only plays pre-generated WAV files.
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "[setup_pi] updating apt and installing OS packages..."
sudo apt-get update
sudo apt-get install -y \
    python3-venv \
    python3-picamera2 \
    libcamera-apps \
    alsa-utils \
    chromium-browser \
    x11-utils

echo "[setup_pi] creating Python venv (with system-site-packages for picamera2)..."
if [[ ! -d .venv ]]; then
    python3 -m venv --system-site-packages .venv
fi

echo "[setup_pi] installing Python dependencies..."
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-pi.txt

echo "[setup_pi] installing project in editable mode..."
pip install -e .

echo
echo "[setup_pi] sanity checks:"
python -c "import cv2; print('  opencv', cv2.__version__)"
python -c "import mediapipe; print('  mediapipe', mediapipe.__version__)"
python -c "import yaml; print('  pyyaml ok')"
python -c "import pygame; print('  pygame', pygame.version.ver)" 2>/dev/null || echo "  pygame: not installed (optional, only for test_display.py)"

echo
echo "[setup_pi] checking assets..."
[[ -f assets/models/gesture_recognizer.task ]] && echo "  gesture model: OK" || echo "  gesture model: MISSING (copy assets/models/gesture_recognizer.task)"
count=$(find assets/expressions -name '*.mp4' 2>/dev/null | wc -l)
echo "  expression mp4s: ${count} files"
[[ ${count} -eq 0 ]] && echo "    -> copy the assets/expressions folder from your PC"
wavcount=$(find assets/sounds -name '*.wav' 2>/dev/null | wc -l)
echo "  voice wavs: ${wavcount} files"

echo
echo "[setup_pi] done. Test with:"
echo "  bash scripts/run_robot.sh"
echo "Enable autostart with the systemd steps in scripts/README.md."

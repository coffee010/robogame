#!/usr/bin/env bash
# One-shot launcher for the robogame demo on Raspberry Pi.
#
# It starts the HTML expression server, opens a kiosk Chromium pointed at it,
# then runs the camera+gesture demo in the foreground. Stop with Ctrl+C.
#
# Designed for Raspberry Pi OS with desktop. Without a DISPLAY it skips the
# kiosk browser and just runs the server + demo (the expression page can still
# be reached from another machine on the network).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

HOST="${ROBOGAME_HOST:-127.0.0.1}"
PORT="${ROBOGAME_PORT:-8765}"
DISPLAY_URL="http://${HOST}:${PORT}/?fit=cover&clean=1"
PYTHON="${PYTHON:-python3}"
IDLE_NAME="${ROBOGAME_IDLE_NAME:-快速双眨眼偶发}"

web_pid=""
kiosk_pid=""

cleanup() {
    echo
    echo "[run_robot] stopping..."
    if [[ -n "${kiosk_pid}" ]] && kill -0 "${kiosk_pid}" 2>/dev/null; then
        kill "${kiosk_pid}" 2>/dev/null || true
    fi
    if [[ -n "${web_pid}" ]] && kill -0 "${web_pid}" 2>/dev/null; then
        kill "${web_pid}" 2>/dev/null || true
    fi
    # Make sure no leftover chromium stays in kiosk mode.
    pkill -f "chromium.*${PORT}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[run_robot] starting expression server on ${HOST}:${PORT}"
"${PYTHON}" scripts/test_display_web.py --host "${HOST}" --port "${PORT}" &
web_pid=$!

# Give the HTTP server a moment to bind before the browser polls it.
sleep 1

if [[ -n "${DISPLAY:-}" ]]; then
    echo "[run_robot] opening kiosk browser at ${DISPLAY_URL}"
    if command -v chromium-browser >/dev/null 2>&1; then
        chromium-browser --kiosk --noerrdialogs --disable-infobars \
            "${DISPLAY_URL}" >/dev/null 2>&1 &
        kiosk_pid=$!
    elif command -v chromium >/dev/null 2>&1; then
        chromium --kiosk --noerrdialogs --disable-infobars \
            "${DISPLAY_URL}" >/dev/null 2>&1 &
        kiosk_pid=$!
    else
        echo "[run_robot] chromium not found; open ${DISPLAY_URL} manually."
    fi
else
    echo "[run_robot] no DISPLAY set; skipping kiosk. Open ${DISPLAY_URL} from a browser."
fi

echo "[run_robot] starting gesture demo (Ctrl+C to stop)"
"${PYTHON}" scripts/robot_demo.py --display-url "http://${HOST}:${PORT}" "$@"

from __future__ import annotations

import subprocess
import sys

import pytest

from robogame.audio.tts import resolve_voice_paths, synthesize_to_wav


def test_resolve_voice_paths_finds_model_and_config(tmp_path):
    voice_dir = tmp_path / "voices"
    voice_dir.mkdir()
    model = voice_dir / "demo.onnx"
    config = voice_dir / "demo.onnx.json"
    model.write_bytes(b"model")
    config.write_text("{}", encoding="utf-8")

    voice = resolve_voice_paths("demo", search_dirs=[voice_dir])

    assert voice.model == model
    assert voice.config == config


def test_resolve_voice_paths_reports_missing_voice(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing"):
        resolve_voice_paths("missing", search_dirs=[tmp_path])


def test_synthesize_to_wav_invokes_piper_with_utf8_environment(monkeypatch, tmp_path):
    voice_dir = tmp_path / "voices"
    voice_dir.mkdir()
    (voice_dir / "demo.onnx").write_bytes(b"model")
    (voice_dir / "demo.onnx.json").write_text("{}", encoding="utf-8")

    call = {}

    def fake_run(command, **kwargs):
        call["command"] = command
        call["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("robogame.audio.tts.subprocess.run", fake_run)

    output = synthesize_to_wav(
        "你好",
        tmp_path / "out.wav",
        voice_name="demo",
        search_dirs=[voice_dir],
        cache_dir=tmp_path / "cache",
        data_dir=tmp_path / "piper-data",
    )

    assert output == tmp_path / "out.wav"
    assert call["command"][:3] == [sys.executable, "-m", "piper"]
    assert call["kwargs"]["input"] == "你好\n"
    assert call["kwargs"]["env"]["PYTHONUTF8"] == "1"

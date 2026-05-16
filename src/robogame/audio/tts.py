from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_VOICE = "zh_CN-xiao_ya-medium"
DEFAULT_OUTPUT = PROJECT_ROOT / "assets" / "sounds" / "tts_preview.wav"


@dataclass(frozen=True)
class PiperVoicePaths:
    model: Path
    config: Path


def default_voice_search_dirs(project_root: Path = PROJECT_ROOT) -> list[Path]:
    return [
        project_root / "assets" / "models" / "piper",
        project_root / "assets" / "sounds",
    ]


def resolve_voice_paths(
    voice_name: str = DEFAULT_VOICE,
    *,
    model_path: str | Path | None = None,
    config_path: str | Path | None = None,
    search_dirs: Sequence[str | Path] | None = None,
) -> PiperVoicePaths:
    if model_path is not None:
        model = Path(model_path)
        config = Path(config_path) if config_path is not None else Path(f"{model}.json")
        if not model.exists():
            raise FileNotFoundError(f"Piper model not found: {model}")
        if not config.exists():
            raise FileNotFoundError(f"Piper config not found: {config}")
        return PiperVoicePaths(model=model, config=config)

    dirs = [Path(path) for path in (search_dirs or default_voice_search_dirs())]
    for directory in dirs:
        model = directory / f"{voice_name}.onnx"
        config = directory / f"{voice_name}.onnx.json"
        if model.exists() and config.exists():
            return PiperVoicePaths(model=model, config=config)

    checked = ", ".join(str(path) for path in dirs)
    raise FileNotFoundError(
        f"Piper voice '{voice_name}' was not found. Checked: {checked}"
    )


def piper_environment(
    *,
    project_root: Path = PROJECT_ROOT,
    cache_dir: str | Path | None = None,
) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    cache_root = Path(cache_dir) if cache_dir is not None else project_root / ".cache"
    hf_home = cache_root / "huggingface"
    hf_home.mkdir(parents=True, exist_ok=True)

    env.setdefault("HF_HOME", str(hf_home))
    env.setdefault("HUGGINGFACE_HUB_CACHE", str(hf_home / "hub"))
    return env


def synthesize_to_wav(
    text: str,
    output_path: str | Path = DEFAULT_OUTPUT,
    *,
    voice_name: str = DEFAULT_VOICE,
    model_path: str | Path | None = None,
    config_path: str | Path | None = None,
    search_dirs: Sequence[str | Path] | None = None,
    data_dir: str | Path | None = None,
    cache_dir: str | Path | None = None,
    length_scale: float | None = None,
    volume: float | None = None,
) -> Path:
    voice = resolve_voice_paths(
        voice_name,
        model_path=model_path,
        config_path=config_path,
        search_dirs=search_dirs,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    piper_data_dir = Path(data_dir) if data_dir is not None else PROJECT_ROOT / ".cache" / "piper"
    piper_data_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "piper",
        "-m",
        str(voice.model),
        "-c",
        str(voice.config),
        "-f",
        str(output),
        "--data-dir",
        str(piper_data_dir),
    ]
    if length_scale is not None:
        command.extend(["--length-scale", str(length_scale)])
    if volume is not None:
        command.extend(["--volume", str(volume)])

    result = subprocess.run(
        command,
        input=f"{text}\n",
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
        env=piper_environment(cache_dir=cache_dir),
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Piper synthesis failed: {details}")

    return output


def play_wav(path: str | Path) -> None:
    audio_path = Path(path)
    if sys.platform == "win32":
        os.startfile(audio_path)  # type: ignore[attr-defined]
        return

    player = shutil.which("aplay") or shutil.which("afplay") or shutil.which("paplay")
    if player is None:
        raise RuntimeError("No audio player found. Install alsa-utils for aplay on Raspberry Pi.")

    subprocess.run([player, str(audio_path)], check=True)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate a WAV file with Piper TTS.")
    parser.add_argument("text", help="Text to synthesize")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--play", action="store_true")
    args = parser.parse_args(argv)

    wav_path = synthesize_to_wav(
        args.text,
        args.output,
        voice_name=args.voice,
        model_path=args.model,
        config_path=args.config,
    )
    print(wav_path)

    if args.play:
        play_wav(wav_path)


if __name__ == "__main__":
    main()

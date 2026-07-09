from __future__ import annotations

from pathlib import Path

import pytest

import robot_demo as rd
from robogame.vision import GestureDetection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_normalize_handles_mediapipe_category_names():
    assert rd.normalize_gesture_name("Open_Palm") == "open_palm"
    assert rd.normalize_gesture_name("Closed_Fist") == "fist"
    assert rd.normalize_gesture_name("Pointing_Up") == "pointing_up"
    assert rd.normalize_gesture_name("I_Love_You") == "iloveyou"
    assert rd.normalize_gesture_name("Thumb_Up") == "thumb_up"
    assert rd.normalize_gesture_name("Thumb_Down") == "thumb_down"
    assert rd.normalize_gesture_name("Victory") == "victory"


def test_normalize_lowercases_and_strips():
    assert rd.normalize_gesture_name("  open-palm ") == "open_palm"
    assert rd.normalize_gesture_name("ThumbUp") == "thumb_up"


def test_load_actions_maps_expression_and_sound(tmp_path):
    sounds = tmp_path / "sounds"
    sounds.mkdir()
    (sounds / "hello.wav").write_bytes(b"audio")
    cfg = tmp_path / "gestures.yaml"
    cfg.write_text(
        "gestures:\n"
        "  open_palm:\n"
        "    expression: happy_loop\n"
        "    sound: hello.wav\n",
        encoding="utf-8",
    )

    actions = rd.load_actions(cfg, sounds_dir=sounds)

    assert list(actions) == ["open_palm"]
    action = actions["open_palm"]
    assert action.expression == "happy_loop"
    assert action.sound == sounds / "hello.wav"


def test_load_actions_ignores_non_mapping_entries(tmp_path):
    cfg = tmp_path / "gestures.yaml"
    cfg.write_text(
        "gestures:\n"
        "  not_a_map: just_a_string\n"
        "  fist:\n"
        "    expression: angry_loop\n",
        encoding="utf-8",
    )

    actions = rd.load_actions(cfg, sounds_dir=tmp_path)

    assert list(actions) == ["fist"]


def test_select_detection_returns_highest_score():
    detections = [
        GestureDetection(name="Victory", score=0.6),
        GestureDetection(name="Open_Palm", score=0.9),
    ]

    assert rd.select_detection(detections, min_score=0.5).name == "Open_Palm"


def test_select_detection_rejects_low_score():
    detections = [GestureDetection(name="Victory", score=0.3)]

    assert rd.select_detection(detections, min_score=0.5) is None


def test_select_detection_handles_empty():
    assert rd.select_detection([], min_score=0.5) is None


def test_audio_manager_missing_file_is_safe(caplog):
    manager = rd.AudioManager()

    manager.play(Path("does-not-exist.wav"))
    manager.stop()

    assert any("sound not found" in record.message for record in caplog.records)


def test_audio_manager_stop_is_noop_when_idle():
    manager = rd.AudioManager()
    manager.stop()


def test_config_gestures_map_to_real_expression_files():
    actions = rd.load_actions(
        PROJECT_ROOT / "config" / "gestures.yaml",
        sounds_dir=PROJECT_ROOT / "assets" / "sounds",
    )
    names = rd.available_expression_names()

    assert actions, "gestures.yaml loaded no actions"
    for key, action in actions.items():
        assert action.expression in names, f"{key} expression missing: {action.expression}"
        assert action.sound is not None and action.sound.exists(), f"{key} sound missing: {action.sound}"

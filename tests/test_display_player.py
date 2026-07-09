from __future__ import annotations

import pytest

from robogame.display import discover_expressions, resolve_expression_path
from robogame.display.web_player import make_expression_handler


def test_discover_expressions_lists_supported_videos(tmp_path):
    (tmp_path / "happy.mp4").write_bytes(b"video")
    nested = tmp_path / "static"
    nested.mkdir()
    (nested / "idle.mov").write_bytes(b"video")
    (tmp_path / "readme.txt").write_text("ignore", encoding="utf-8")

    expressions = discover_expressions(tmp_path)

    assert [item.name for item in expressions] == ["happy", "idle"]


def test_resolve_expression_path_accepts_name_without_suffix(tmp_path):
    nested = tmp_path / "happy"
    nested.mkdir()
    video = nested / "happy_loop.mp4"
    video.write_bytes(b"video")

    assert resolve_expression_path("happy_loop", expressions_dir=tmp_path) == video


def test_resolve_expression_path_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing"):
        resolve_expression_path("missing", expressions_dir=tmp_path)


def test_web_handler_can_be_built(tmp_path):
    handler = make_expression_handler(tmp_path)

    assert handler.__name__ == "ExpressionRequestHandler"

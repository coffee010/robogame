from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EXPRESSIONS_DIR = PROJECT_ROOT / "assets" / "expressions"
VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv")


@dataclass(frozen=True)
class ExpressionAsset:
    name: str
    path: Path


def discover_expressions(
    expressions_dir: str | Path = DEFAULT_EXPRESSIONS_DIR,
) -> list[ExpressionAsset]:
    directory = Path(expressions_dir)
    if not directory.exists():
        return []

    assets: list[ExpressionAsset] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            assets.append(ExpressionAsset(name=path.stem, path=path))
    return assets


def resolve_expression_path(
    expression: str | Path,
    *,
    expressions_dir: str | Path = DEFAULT_EXPRESSIONS_DIR,
) -> Path:
    value = Path(expression)
    if value.exists():
        return value

    directory = Path(expressions_dir)
    candidates: list[Path]
    if value.suffix:
        candidates = [directory / value.name]
    else:
        candidates = [directory / f"{value.name}{suffix}" for suffix in VIDEO_EXTENSIONS]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    for asset in discover_expressions(directory):
        if asset.path.name == value.name or asset.name == value.name:
            return asset.path

    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"expression video not found: {expression}. Checked: {checked}")


class ExpressionPlayer:
    def __init__(
        self,
        *,
        width: int = 800,
        height: int = 480,
        fullscreen: bool = False,
        window_title: str = "robogame expression",
        background: tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.window_title = window_title
        self.background = background

    def play(
        self,
        expression: str | Path,
        *,
        loop: bool = True,
        fit: str = "contain",
        expressions_dir: str | Path = DEFAULT_EXPRESSIONS_DIR,
    ) -> None:
        import cv2
        import numpy as np
        import pygame

        if fit not in {"contain", "cover", "stretch"}:
            raise ValueError("fit must be 'contain', 'cover', or 'stretch'")

        video_path = resolve_expression_path(expression, expressions_dir=expressions_dir)
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"could not open expression video: {video_path}")

        pygame.init()
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        screen = pygame.display.set_mode((self.width, self.height), flags)
        pygame.display.set_caption(self.window_title)
        pygame.mouse.set_visible(False)
        clock = pygame.time.Clock()

        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1:
            fps = 30

        try:
            running = True
            while running:
                ok, frame_bgr = capture.read()
                if not ok:
                    if loop:
                        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    break

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN and event.key in (
                        pygame.K_ESCAPE,
                        pygame.K_q,
                    ):
                        running = False

                if not running:
                    break

                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                frame_rgb = self._resize_frame(frame_rgb, fit=fit)
                surface = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))

                screen.fill(self.background)
                x = (self.width - surface.get_width()) // 2
                y = (self.height - surface.get_height()) // 2
                screen.blit(surface, (x, y))
                pygame.display.flip()
                clock.tick(fps)
        finally:
            capture.release()
            pygame.mouse.set_visible(True)
            pygame.quit()

    def _resize_frame(self, frame_rgb, *, fit: str):  # type: ignore[no-untyped-def]
        import cv2

        if fit == "stretch":
            return cv2.resize(frame_rgb, (self.width, self.height), interpolation=cv2.INTER_AREA)

        source_height, source_width = frame_rgb.shape[:2]
        width_scale = self.width / source_width
        height_scale = self.height / source_height
        scale = max(width_scale, height_scale) if fit == "cover" else min(width_scale, height_scale)

        target_width = max(1, int(source_width * scale))
        target_height = max(1, int(source_height * scale))
        resized = cv2.resize(frame_rgb, (target_width, target_height), interpolation=cv2.INTER_AREA)

        if fit == "cover":
            x = max(0, (target_width - self.width) // 2)
            y = max(0, (target_height - self.height) // 2)
            return resized[y : y + self.height, x : x + self.width]

        return resized


def play_expression(
    expression: str | Path,
    *,
    width: int = 800,
    height: int = 480,
    fullscreen: bool = False,
    loop: bool = True,
    fit: str = "contain",
    expressions_dir: str | Path = DEFAULT_EXPRESSIONS_DIR,
) -> None:
    player = ExpressionPlayer(width=width, height=height, fullscreen=fullscreen)
    player.play(expression, loop=loop, fit=fit, expressions_dir=expressions_dir)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Play an expression mp4 in a pygame window. Press q or Esc to stop."
    )
    parser.add_argument("expression", nargs="?", help="Expression name or video path.")
    parser.add_argument("--dir", type=Path, default=DEFAULT_EXPRESSIONS_DIR)
    parser.add_argument("--width", type=int, default=800)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--once", action="store_true", help="Stop when the video reaches the end.")
    parser.add_argument("--fit", choices=["contain", "cover", "stretch"], default="contain")
    parser.add_argument("--list", action="store_true", help="List available expressions.")
    args = parser.parse_args(argv)

    if args.list:
        for asset in discover_expressions(args.dir):
            print(f"{asset.name}\t{asset.path}")
        return 0

    if not args.expression:
        raise SystemExit("provide an expression name/path, or use --list")

    play_expression(
        args.expression,
        width=args.width,
        height=args.height,
        fullscreen=args.fullscreen,
        loop=not args.once,
        fit=args.fit,
        expressions_dir=args.dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

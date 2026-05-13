from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - only used before dependencies are installed
    yaml = None


LOGGER = logging.getLogger(__name__)


def load_yaml(path: Path) -> dict:
    if yaml is None:
        raise RuntimeError("missing dependency: install PyYAML with `python -m pip install pyyaml`")
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/robot.yaml")
    parser.add_argument("--gestures", default="config/gestures.yaml")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    try:
        config = load_yaml(Path(args.config))
        gestures = load_yaml(Path(args.gestures))
    except RuntimeError as error:
        LOGGER.error("%s", error)
        sys.exit(2)

    LOGGER.info("robot mode: %s", config.get("robot", {}).get("mode", "unknown"))
    LOGGER.info("loaded gestures: %s", ", ".join(gestures.get("gestures", {}).keys()))
    LOGGER.info("hardware is not attached yet; running preparation scaffold only")


if __name__ == "__main__":
    main()

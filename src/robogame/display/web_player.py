from __future__ import annotations

import argparse
import json
import mimetypes
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence
from urllib.parse import quote, unquote, urlparse

from .player import DEFAULT_EXPRESSIONS_DIR, discover_expressions


HTML_PAGE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Robogame Expression</title>
<style>
:root { color-scheme: dark; font-family: Arial, "Microsoft YaHei", sans-serif; }
* { box-sizing: border-box; }
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #000; }
video {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  object-fit: var(--fit, contain);
  background: #000;
}
.panel {
  position: fixed;
  top: 12px;
  right: 12px;
  width: min(320px, calc(100vw - 24px));
  max-height: calc(100vh - 24px);
  overflow: auto;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(0, 0, 0, 0.58);
  opacity: 0.28;
  transition: opacity 160ms ease;
}
.panel:hover, .panel:focus-within { opacity: 1; }
.clean .panel { display: none; }
.row { display: flex; gap: 8px; margin-bottom: 8px; }
button {
  min-height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  padding: 6px 10px;
  cursor: pointer;
}
button.active { background: #fff; color: #000; }
#list { display: grid; gap: 6px; }
#list button { width: 100%; text-align: left; overflow-wrap: anywhere; }
</style>
</head>
<body>
<video id="face" autoplay loop muted playsinline></video>
<aside class="panel" aria-label="expressions">
  <div class="row">
    <button id="prev" type="button">Prev</button>
    <button id="next" type="button">Next</button>
  </div>
  <div id="list"></div>
</aside>
<script>
const params = new URLSearchParams(location.search);
const video = document.getElementById("face");
const list = document.getElementById("list");
const prev = document.getElementById("prev");
const next = document.getElementById("next");
const fit = params.get("fit") || "contain";
const clean = params.get("clean") === "1";
document.documentElement.style.setProperty("--fit", fit === "fill" ? "fill" : fit);
if (clean) document.body.classList.add("clean");

let expressions = [];
let currentIndex = 0;
let activeName = null;

function setExpression(index) {
  if (!expressions.length) return;
  currentIndex = (index + expressions.length) % expressions.length;
  const item = expressions[currentIndex];
  activeName = item.name;
  video.src = item.url;
  video.load();
  video.play().catch(() => {});
  document.querySelectorAll("#list button").forEach((button, buttonIndex) => {
    button.classList.toggle("active", buttonIndex === currentIndex);
  });
}

function setExpressionByName(name) {
  const index = expressions.findIndex((item) => item.name === name || item.path === name);
  if (index >= 0) setExpression(index);
}

function render() {
  list.textContent = "";
  expressions.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item.name;
    button.addEventListener("click", () => setExpression(index));
    list.appendChild(button);
  });
}

function pollState() {
  fetch("/api/state")
    .then((response) => response.json())
    .then((state) => {
      if (state.expression && state.expression !== activeName) {
        setExpressionByName(state.expression);
      }
    })
    .catch(() => {});
}

fetch("/api/expressions")
  .then((response) => response.json())
  .then((items) => {
    expressions = items;
    render();
    const requested = params.get("name");
    const requestedIndex = expressions.findIndex((item) => item.name === requested);
    setExpression(requestedIndex >= 0 ? requestedIndex : 0);
    window.setInterval(pollState, 200);
  });

video.addEventListener("ended", () => {
  video.currentTime = 0;
  video.play().catch(() => {});
});
prev.addEventListener("click", () => setExpression(currentIndex - 1));
next.addEventListener("click", () => setExpression(currentIndex + 1));
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") setExpression(currentIndex - 1);
  if (event.key === "ArrowRight") setExpression(currentIndex + 1);
});
</script>
</body>
</html>
"""


def make_expression_handler(expressions_dir: Path) -> type[BaseHTTPRequestHandler]:
    root = Path(expressions_dir).resolve()
    state = {"expression": None}

    class ExpressionRequestHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_bytes(HTML_PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if parsed.path == "/api/expressions":
                self._send_json(self._expression_payload())
                return
            if parsed.path == "/api/state":
                self._send_json(state)
                return
            if parsed.path.startswith("/media/"):
                self._send_media(parsed.path.removeprefix("/media/"))
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/api/state":
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
                return

            expression = payload.get("expression")
            if expression is not None and not isinstance(expression, str):
                self.send_error(HTTPStatus.BAD_REQUEST, "expression must be a string")
                return
            state["expression"] = expression
            self._send_json(state)

        def _expression_payload(self) -> list[dict[str, str]]:
            payload = []
            for asset in discover_expressions(root):
                relative_path = asset.path.resolve().relative_to(root).as_posix()
                payload.append(
                    {
                        "name": asset.name,
                        "path": relative_path,
                        "url": f"/media/{quote(relative_path)}",
                    }
                )
            return payload

        def _send_media(self, raw_path: str) -> None:
            relative_path = unquote(raw_path)
            path = (root / relative_path).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return

            content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(path.stat().st_size))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            with path.open("rb") as file:
                while chunk := file.read(1024 * 1024):
                    self.wfile.write(chunk)

        def _send_json(self, value) -> None:  # type: ignore[no-untyped-def]
            self._send_bytes(
                json.dumps(value, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )

        def _send_bytes(self, data: bytes, content_type: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return ExpressionRequestHandler


def set_remote_expression(
    expression: str,
    *,
    base_url: str = "http://127.0.0.1:8765",
    timeout: float = 2.0,
) -> None:
    url = f"{base_url.rstrip('/')}/api/state"
    data = json.dumps({"expression": expression}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read()


def run_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    expressions_dir: str | Path = DEFAULT_EXPRESSIONS_DIR,
) -> None:
    directory = Path(expressions_dir)
    directory.mkdir(parents=True, exist_ok=True)
    handler = make_expression_handler(directory)
    server = ThreadingHTTPServer((host, port), handler)
    print(f"http://{host}:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the HTML expression player.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dir", type=Path, default=DEFAULT_EXPRESSIONS_DIR)
    args = parser.parse_args(argv)

    run_server(host=args.host, port=args.port, expressions_dir=args.dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

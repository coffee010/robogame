# Models

Model binaries are intentionally ignored by Git.

Put the Raspberry Pi deployment model here after downloading or copying it, for example:

```text
assets/models/gesture_recognizer.task
assets/models/piper/zh_CN-xiao_ya-medium.onnx
assets/models/piper/zh_CN-xiao_ya-medium.onnx.json
```

Piper model binaries are not installed by `requirements.txt`. Download both the
`.onnx` and `.onnx.json` files for the voice you want to use.

Use `manifest.json` in this directory later if you want to record model names, versions,
checksums, and download URLs.

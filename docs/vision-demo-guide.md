# Vision demo guide

## Stop the program

- Image mode: click the preview window and press any key.
- Video or camera mode with a preview window: click the preview window and press `q` or `Esc`.
- Terminal fallback: press `Ctrl+C`.
- If `--no-window` is used with an unlimited camera run, stop it with `Ctrl+C` or add `--max-frames`.

## Save visual output for a report

Save an annotated image:

```powershell
python scripts/test_vision.py --image path\to\gesture.jpg --save-output docs\figures\gesture-result.jpg --no-window
```

Save an annotated camera clip:

```powershell
python scripts/test_vision.py --camera 0 --mirror --max-frames 300 --save-output docs\figures\gesture-demo.mp4
```

Save an annotated video:

```powershell
python scripts/test_vision.py --video path\to\demo.mp4 --save-output docs\figures\gesture-demo.mp4 --no-window
```

The saved output shows the recognized gesture name and confidence score on the frame. It is usually better to use a screenshot or saved frame from your own run instead of an official example, because it proves the local prototype works.

## Suggested report wording

The prototype uses MediaPipe Gesture Recognizer to process camera frames. OpenCV reads the image stream and displays the recognition result in real time. The recognized gesture category and confidence score are overlaid on the frame, which can be saved as an annotated image or video for experimental evidence.

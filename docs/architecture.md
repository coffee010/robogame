# 软件架构

## 模块划分

```text
camera -> vision -> interaction -> audio
                         |
                         +-> display
                         |
                         +-> motion
```

- `camera`：负责采集画面。电脑上可用 OpenCV 摄像头或视频文件，树莓派上优先用 Picamera2。
- `vision`：负责 MediaPipe 手部关键点检测和手势识别。
- `interaction`：负责把识别结果映射成机器人行为。
- `audio`：负责播放音效或调用 Piper TTS。
- `display`：负责在屏幕上显示表情资源。
- `motion`：负责舵机动作，先做模拟日志，硬件到位后接 PCA9685 或 GPIO PWM。

## 当前建议

先把所有硬件相关代码做成接口，默认使用模拟实现。这样没有树莓派时也能调试业务逻辑。

示例事件：

```yaml
gesture: open_palm
emotion: happy
sound: hello.wav
motion: wave
```


# Audio

负责音效播放和文字转语音。

## 文件放哪里

- 普通音效和已经生成好的语音：`assets/sounds`
- Piper 声音模型：推荐放 `assets/models/piper`
- 临时下载缓存：`.cache`，不要提交到 GitHub

现在的代码也会兼容你已经放在 `assets/sounds` 里的模型文件。

一个 Piper 音色通常需要两个文件：

```text
assets/models/piper/zh_CN-xiao_ya-medium.onnx
assets/models/piper/zh_CN-xiao_ya-medium.onnx.json
```

小雅模型下载地址：

- `https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx?download=true`
- `https://huggingface.co/rhasspy/piper-voices/resolve/main/zh/zh_CN/xiao_ya/medium/zh_CN-xiao_ya-medium.onnx.json?download=true`

## 依赖说明

`piper-tts` 是实时文字转语音必须的。

`zh_CN-xiao_ya` 这类中文音色还需要 `piper-tts[zh]`。这个 extra 会自动安装：

- `g2pW`
- `torch`
- `unicode-rbnf`
- `sentence-stream`
- `requests`

这些包不是播放 WAV 必须的。如果树莓派只播放电脑上提前生成好的 `.wav`，可以不装 `tts-zh`，只把 wav 文件放进 `assets/sounds`。

树莓派实时生成中文语音可以运行，但 `torch` 很大，第一次安装和第一次合成都会比较慢。建议比赛/演示时把固定台词提前生成成 wav。

## 命令行测试

```powershell
python -m robogame.audio.tts "你好，我是小雅，语音测试成功。" -o assets/sounds/test_xiaoya.wav
```

Windows 上播放：

```powershell
Start-Process assets/sounds/test_xiaoya.wav
```

树莓派上播放：

```bash
aplay assets/sounds/test_xiaoya.wav
```

## 代码调用

生成语音文件：

```python
from robogame.audio.tts import synthesize_to_wav

wav_path = synthesize_to_wav(
    "你好，我准备好了。",
    "assets/sounds/ready.wav",
)
print(wav_path)
```

生成后直接播放：

```python
from robogame.audio.tts import play_wav, synthesize_to_wav

wav_path = synthesize_to_wav("你好，我准备好了。", "assets/sounds/ready.wav")
play_wav(wav_path)
```

如果只是播放已经存在的固定音效，直接用：

```python
from robogame.audio.tts import play_wav

play_wav("assets/sounds/ready.wav")
```

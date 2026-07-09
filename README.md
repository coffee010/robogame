# Robogame HRI

软体机器人人机交互部分的准备仓库。目标是在树莓派上把摄像头手势识别、声音播放、表情屏幕和舵机控制串起来。

当前进度：摄像头手势识别 → 切换屏幕表情 + 播放语音 的连续交互已经打通，支持空闲自动回到静态表情。舵机动作（motion 模块）尚未接入，本轮只做表情和语音。

主要流程在 `scripts/robot_demo.py`：

```text
摄像头 -> MediaPipe 手势识别 -> 查 config/gestures.yaml
   -> HTTP 切表情（网页播放器） + 异步播 WAV 语音
   -> 3 秒无手势自动回到静态眨眼表情
```

## 目录

```text
assets/              # 表情、声音、MediaPipe 模型等静态资源
config/              # 手势映射、硬件参数、运行配置
docs/                # 学习路线、架构、硬件笔记
scripts/             # 安装、启动、诊断脚本
src/robogame/        # Python 主程序和模块
tests/               # 单元测试和离线测试数据
```

## 建议的第一阶段目标

1. 在电脑上完成 Python 项目结构和配置文件。
2. 用普通视频文件或电脑摄像头验证手势识别逻辑。
3. 用本地音频文件模拟喇叭播放。
4. 用桌面窗口模拟屏幕表情显示。
5. 等硬件到位后再接入树莓派专用接口。

## 快速开始（树莓派）

### 一键启动

```bash
cd ~/robogame
bash scripts/run_robot.sh
```

脚本会自动启动表情网页服务、用 Chromium 全屏打开表情页、再跑手势 demo。Ctrl+C 退出会清理子进程。详细参数和开机自启见 `scripts/README.md`。

### 开机自启

```bash
sudo cp scripts/robogame.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now robogame
```

### 配置

- `config/gestures.yaml`：手势 → 表情文件名 + 语音文件名 的映射。表情名填 `assets/expressions/` 下视频的文件名（去后缀），如 `兴奋_2可循环动作`。
- `config/robot.yaml` 的 `interaction` 段：`idle_expression`（空闲表情）、`idle_timeout`（秒）、`min_score`、`cooldown`。
- 语音文件放 `assets/sounds/`，已用 Piper 预生成 7 条中文台词。要换台词在电脑上跑 `python -m robogame.audio.tts "你的台词" -o assets/sounds/xxx.wav` 重新生成。

### 分步测试

```bash
# 单测手势识别（摄像头）
python scripts/test_vision.py --camera 0 --mirror

# 只起表情网页播放器
python scripts/test_display_web.py
# 浏览器打开 http://127.0.0.1:8765/

# 只测 pygame 播放某段表情
python scripts/test_display.py 兴奋_2可循环动作
```


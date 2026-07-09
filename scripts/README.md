# Scripts

## 树莓派一键启动 / 开机自启

`run_robot.sh` 会依次：启动表情网页服务 → 用 Chromium kiosk 全屏打开表情页 → 前台跑手势 demo。Ctrl+C 一次退出会自动清理子进程。

手动跑一次（有桌面时）：

```bash
cd ~/robogame
bash scripts/run_robot.sh
```

无桌面（headless）时脚本会跳过 kiosk，仍启动服务和 demo，可从局域网另一台机器的浏览器打开 `http://<树莓派IP>:8765/` 看表情。

把默认摄像头索引或镜像等参数透传给 demo：

```bash
bash scripts/run_robot.sh --camera 0 --mirror
```

### 开机自启（systemd）

1. 把仓库放在 `/home/pi/robogame`（或修改 `robogame.service` 里的路径）。
2. 安装 service 文件：

```bash
sudo cp scripts/robogame.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now robogame
```

3. 查看状态 / 日志：

```bash
systemctl status robogame
journalctl -u robogame -f
```

4. 停止 / 取消自启：

```bash
sudo systemctl disable --now robogame
```

> systemd 单元依赖 `graphical.target`，需要带桌面的 Raspberry Pi OS。Chromium kiosk 需要 `DISPLAY=:0`，已在 service 里设置。如果开机时桌面还没起来导致表情页打不开，可把 `After=` 改成 `After=graphical-session.target` 或在 `run_robot.sh` 里把 `sleep 1` 调大。

## 其他脚本

- `robot_demo.py`：主交互循环（摄像头 → 手势 → 表情 + 语音）。
- `test_vision.py`：单独测 MediaPipe 手势识别（图片/视频/摄像头）。
- `test_display.py`：pygame 窗口播放单个表情。
- `test_display_web.py`：HTML 表情播放器服务，被 `robot_demo.py` 和 `run_robot.sh` 使用。

## 后续可放置

- `setup_pi.sh`：树莓派依赖安装
- `check_camera.sh`：摄像头检测
- `check_audio.sh`：音频检测

# Display

负责屏幕表情显示。

## 表情资源放哪

把稚晖君/ElectronBot 相关表情视频放到：

```text
assets/expressions/
```

可以直接把 ElectronBot 的 `4.CAD-Model/Emoji` 目录内容复制进来；播放器会递归查找子目录里的 mp4。也可以只挑常用文件放在第一层，并把文件名改成英文或拼音：

```text
assets/expressions/idle.mp4
assets/expressions/happy.mp4
assets/expressions/angry.mp4
assets/expressions/兴奋/兴奋_2可循环动作.mp4
```

## 命令行测试

### HTML 播放器

这个方案更适合演示：浏览器全屏常驻，视频自动循环，播放完不会回到桌面或外部播放器界面。

启动本地网页播放器：

```powershell
python scripts/test_display_web.py
```

然后浏览器打开：

```text
http://127.0.0.1:8765/
```

树莓派上可以用 Chromium 全屏打开：

```bash
python scripts/test_display_web.py
chromium-browser --kiosk "http://127.0.0.1:8765/?name=兴奋_2可循环动作&fit=cover&clean=1"
```

`clean=1` 会隐藏右上角选择面板，适合正式演示。

### pygame 播放器

列出已经放好的表情：

```powershell
python scripts/test_display.py --list
```

播放 `idle.mp4`：

```powershell
python scripts/test_display.py idle
```

播放子目录里的 ElectronBot 原始文件也可以直接用文件名：

```powershell
python scripts/test_display.py 兴奋_2可循环动作
```

树莓派接小屏时可以全屏播放：

```bash
python scripts/test_display.py idle --fullscreen --width 800 --height 480 --fit cover
```

窗口打开后按 `q` 或 `Esc` 退出。

## 代码调用

```python
from robogame.display import play_expression

play_expression("idle", width=800, height=480, fullscreen=True, fit="cover")
```

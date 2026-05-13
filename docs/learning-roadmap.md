# 学习路线

## 必学

1. Linux 基础
   - 目录结构：`/home`、`/boot/firmware`、`/dev`、`/etc`
   - 常用命令：`ls`、`cd`、`cp`、`mv`、`rm`、`nano`、`cat`、`grep`、`systemctl`
   - SSH 登录、文件传输、权限、服务自启动

2. Python 基础
   - 虚拟环境：`python -m venv .venv`
   - 包管理：`pip install`
   - 模块拆分、日志、异常处理
   - YAML/JSON 配置读取

3. 树莓派基础
   - Raspberry Pi OS 安装和 SSH 开启
   - GPIO、I2C、I2S、PWM、CSI、DSI 的区别
   - `raspi-config`、`rpicam-hello`、`systemd` 自启动

4. 视觉识别
   - OpenCV 基础：读取摄像头、读取视频、显示画面、颜色空间转换
   - MediaPipe Hand Landmarker：21 个手部关键点、实时流模式、置信度阈值
   - 手势分类：先用规则判断，再考虑训练模型

5. 音频和表情
   - WAV/MP3 播放、音量控制、音频设备选择
   - Piper TTS 的离线语音合成
   - Pygame 或 Qt 显示图片/GIF/帧动画

6. 舵机控制
   - PWM 原理、角度和脉宽关系
   - PCA9685 舵机驱动板
   - 舵机限位、缓动、断电保护

## 推荐顺序

1. 先学 Linux 命令和 SSH，能远程操作树莓派。
2. 再学 Python 虚拟环境和项目结构。
3. 用电脑摄像头跑通 MediaPipe 手势识别。
4. 用配置文件把“手势 -> 表情/声音/动作”串起来。
5. 最后接树莓派硬件接口。


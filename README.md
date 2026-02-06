# Telegram Bot Youtube Downloader

基于 Python 3 和 `python-telegram-bot` v20+ 构建的现代化 Telegram 视频下载机器人。支持 YouTube、Instagram、Twitter (X)、Pornhub 等多种主流媒体网站。

## ✨ 主要特性

-   **异步架构**: 基于 `asyncio` 和最新版 `python-telegram-bot`，响应迅速，并发处理能力强。
-   **广泛支持**: 集成 `yt-dlp`，支持下载 YouTube、Instagram、Twitter、TikTok、Pornhub 等数百个网站的视频。
-   **智能处理**:
    -   自动获取视频的多种格式（分辨率、编码）供用户选择。
    -   **自动分卷**: 对于超过 50MB（Telegram API 限制）的视频，自动使用 `ffmpeg` 进行无损分卷发送。
-   **模块化设计**: 代码结构清晰，易于维护和扩展。

## 🛠️ 安装与部署

### 前置要求

-   Python 3.8+
-   [FFmpeg](https://ffmpeg.org/download.html) (必须安装并添加到系统 PATH 环境变量中)

### 1. 克隆项目

```bash
git clone https://github.com/nie11kun/telegram-bot-youtube-downloader.git
cd telegram-bot-youtube-downloader
```

### 2. 安装依赖

建议使用虚拟环境：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (Linux/macOS)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

在项目根目录创建 `.env` 文件，或直接设置环境变量：

```env
# 必须配置
BOT_TOKEN=你的_Telegram_Bot_Token

# 可选配置
INS_ACCOUNT=你的_Instagram_账号  # 部分 Instagram 内容可能需要登录
TEMP_DIR=temp_downloads         # 临时下载目录，默认为 temp_downloads
MAX_FILE_SIZE=52428800          # 文件分卷阈值 (字节)，默认为 50MB (52428800)
DEFAULT_TIMEOUT=600             # 超时时间 (秒)
```

### 4. 运行机器人

```bash
python main.py
```

## 📖 使用指南

1.  **启动**: 发送 `/start` 唤醒机器人。
2.  **下载**: 直接发送媒体链接给机器人（例如 YouTube 视频链接）。
3.  **选择格式**: 机器人会分析链接并返回可供下载的格式列表（分辨率、文件大小）。
4.  **接收文件**: 点击对应格式的按钮，机器人将自动下载、处理（如需分卷）并发送文件给你。

## 📂 项目结构

```text
.
├── bot/
│   ├── config.py          # 配置文件
│   ├── services/
│   │   ├── downloader.py  # 异步下载服务 (yt-dlp)
│   │   └── splitter.py    # 媒体处理服务 (ffmpeg)
│   └── handlers/
│       ├── commands.py    # 命令处理器
│       ├── messages.py    # 消息处理器 (链接检测)
│       └── callbacks.py   # 回调处理器 (按钮点击)
├── main.py                # 程序入口
├── requirements.txt       # 项目依赖
└── .env                   # 环境变量配置
```

## 📝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

[MIT License](LICENSE)

![logo](./static/Luo2Icon-mini.png)

# 洛² 聊天系统

基于Python的实时聊天系统，支持大厅和私聊功能。

## 功能特点

- 实时消息推送
- 大厅与私聊
- 消息提示音
- 系统通知
- 移动端适配
- 全屏模式

## 系统要求

服务端:

- Python 3.7+（推荐3.12.0）
- 操作系统：Linux、Windows、MacOS

客户端:

- 支持WebSocket的现代浏览器

## 快速开始

1. 新建虚拟环境并启动虚拟环境：

```bash
python -m venv venv
# 请使用系统对应的启动虚拟环境命令（懒得写了
```

2. 安装依赖包并启动：
   
   ```bash
   pip install -r requirements.txt
   python main.py --web-port 8003
   ```

3. 访问网页客户端：
   http://localhost:8002

## 服务地址

- 聊天服务：ws://localhost:8000
- API服务：http://localhost:8001
- Web客户端：http://localhost:8002

## 命令参数

- 需要使用main.py启动

- 无命令行模式：`--no-command`

- 指定Web端口号：`--web-port 8003`

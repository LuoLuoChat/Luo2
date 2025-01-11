![logo](./static/Luo2Icon-mini.png)

[简体中文](./README.md) | [English](./README-en.md)

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

1.Git此仓库,并进入仓库目录

```bash
git clone https://github.com/LuoLuoChat/Luo2.git
cd Luo2
```

2. 修改 config.json 文件中的 ws_domain 和 api_domain 为你的服务器地址

- 若更改了 server.py 与 api_server.py 中的端口号，请修改 config.json 文件中的 ws_port 和 api_port
- Web 使用 --web-port 参数指定端口号

```json
{
    "ws_domain": "localhost",
    "api_domain": "localhost",
    "ws_port": 8000,
    "api_port": 8001
}
```

3. 新建虚拟环境并启动虚拟环境：

- Windows

```bash
python -m venv venv
venv\Scripts\activate
```

- Linux

```bash
python -m venv venv
source venv/bin/activate
```

4. 安装依赖包并启动：

```bash
pip install -r requirements.txt
python main.py --web-port 8002
```

5. 访问网页客户端：
   http://localhost:8002

## 服务地址（如果默认）

- 聊天服务：ws://localhost:8000
- API服务：http://localhost:8001
- Web客户端：http://localhost:8002

## 命令参数

- 使用 main.py 启动服务器，支持以下参数：
- 无命令行模式，适用于后台运行：`--no-command`
- 指定 Web 服务器端口：`--web-port <端口号>`

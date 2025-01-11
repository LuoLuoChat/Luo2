![logo](./static/Luo2Icon-mini.png)

[简体中文](./README.md) | [English](./README-en.md)

# Note: Luo² itself does not support English, this is just a translation of the English document, please translate it yourself

# Luo² Chat Server

Luo² is a real-time chat system based on Python, supporting both lobby and private chat functions.

## Features

- Real-time message push
- Lobby and private chat
- Message notification sound
- System notification
- Mobile adaptation
- Full screen mode

## System requirements

Server:

- Python 3.7+ (recommended 3.12.0)
- Operating system: Linux, Windows, MacOS

Client:

- Modern browser supporting WebSocket

## Quick start
1. Git this repository, and enter the repository directory
```bash
git clone https://github.com/LuoLuoChat/Luo2.git
cd Luo2
```
2. Modify the ws_domain and api_domain in the config.json file to your server address / domain
- If you change the port number in server.py and api_server.py, please modify the ws_port and api_port in the config.json file
- Web uses the --web-port parameter to specify the port number
```json
{
    "ws_domain": "localhost",
    "api_domain": "localhost",
    "ws_port": 8000,
    "api_port": 8001
}
```


3. Create a virtual environment and start the virtual environment:
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

4. Install dependencies and start:
   
```bash
pip install -r requirements.txt
python main.py --web-port 8002
```

5. Access the web client:
   http://localhost:8002

## Service address (if default)

- Chat service: ws://localhost:8000
- API service: http://localhost:8001
- Web client: http://localhost:8002

## Command parameters

- Use main.py to start the server, supports the following parameters:

- No command line mode, suitable for background operation: `--no-command`

- Specify the Web server port: `--web-port <port number>`

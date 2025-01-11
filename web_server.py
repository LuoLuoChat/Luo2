from flask import Flask, render_template, send_from_directory, request, send_file, jsonify
import os
import json

app = Flask(__name__)

# 读取配置文件
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {
            "ws_domain": "localhost",
            "api_domain": "localhost",
            "web_port": 8002,
            "ws_port": 8000,
            "api_port": 8001
        }

@app.route('/config')
def get_config():
    config = load_config()
    return jsonify(config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/callback')
def callback():
    # 显示回调页面，该页面会处理OAuth2回调并与API服务器通信
    return render_template('callback.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'Luo2Icon-mini.png', mimetype='image/png')

# 添加 PWA 图标路由
@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return send_from_directory('static', 'Luo2Icon-mini.png', mimetype='image/png')

@app.route('/icon-192.png')
def icon_192():
    return send_from_directory('static', 'Luo2Icon-mini.png', mimetype='image/png')

@app.route('/icon-512.png')
def icon_512():
    return send_from_directory('static', 'Luo2Icon-mini.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002) 
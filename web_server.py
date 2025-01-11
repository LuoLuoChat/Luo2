from flask import Flask, render_template, send_from_directory, request, send_file
import os

app = Flask(__name__)

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
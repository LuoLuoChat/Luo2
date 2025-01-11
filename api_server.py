from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
import hashlib
import time
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# 修改 CORS 设置，确保允许所有来源
CORS(app, resources={r"/api/*": {"origins": "*"}})

# 数据目录
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    try:
        os.makedirs(DATA_DIR)
    except Exception as e:
        logger.error(f"创建数据目录失败: {str(e)}")
        raise

# 用户数据文件
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'sessions.json')

# 确保文件存在并可写
for file in [USERS_FILE, SESSIONS_FILE]:
    try:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"初始化文件 {file} 失败: {str(e)}")
        raise

def load_json_file(filename, default=None):
    """加载JSON文件，如果文件不存在则返回默认值"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"加载文件 {filename} 失败: {str(e)}")
        return default if default is not None else {}

def save_json_file(filename, data):
    """保存数据到JSON文件"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"保存文件 {filename} 成功")
    except Exception as e:
        logger.error(f"保存文件 {filename} 失败: {str(e)}")

# 加载用户和会话数据
users = load_json_file(USERS_FILE, {})
sessions = load_json_file(SESSIONS_FILE, {})

def hash_password(password):
    """使用SHA-256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """生成随机令牌"""
    return hashlib.sha256(str(time.time()).encode()).hexdigest()

def is_valid_session(token):
    """检查会话是否有效"""
    if not token:
        return False
    if token not in sessions:
        return False
    session = sessions[token]
    expiry = datetime.fromisoformat(session['expiry'])
    return expiry > datetime.now()

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        logger.debug(f"收到注册请求: {request.get_json()}")
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求必须是JSON格式'
            }), 400
            
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        # 输入验证
        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400
            
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': '用户名至少需要3个字符'
            }), 400
            
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': '密码至少需要6个字符'
            }), 400
        
        # 检查用户名是否已存在
        if any(user.get('username') == username for user in users.values()):
            return jsonify({
                'success': False,
                'error': '用户名已存在'
            }), 400
        
        # 创建新用户
        user_id = str(len(users) + 1)
        users[user_id] = {
            'username': username,
            'password': hash_password(password),
            'created_at': datetime.now().isoformat()
        }
        
        # 保存用户数据
        save_json_file(USERS_FILE, users)
        
        logger.info(f"新用户注册成功: {username}")
        return jsonify({
            'success': True,
            'message': '注册成功'
        })
        
    except Exception as e:
        logger.exception("注册时出错")
        return jsonify({
            'success': False,
            'error': f'注册失败：{str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': '请求必须是JSON格式'
            }), 400
            
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        logger.debug(f"尝试登录: {username}")
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': '用户名和密码不能为空'
            }), 400
        
        # 验证用户
        user_id = None
        for uid, user in users.items():
            if isinstance(user, dict) and user.get('username') == username and user.get('password') == hash_password(password):
                user_id = uid
                break
        
        if not user_id:
            logger.warning(f"登录失败: 用户名或密码错误 ({username})")
            return jsonify({
                'success': False,
                'error': '用户名或密码错误'
            }), 401
        
        # 创建新会话
        token = generate_token()
        expiry = datetime.now() + timedelta(days=7)  # 7天后过期
        sessions[token] = {
            'user_id': user_id,
            'expiry': expiry.isoformat()
        }
        
        # 保存会话数据
        save_json_file(SESSIONS_FILE, sessions)
        logger.info(f"用户登录成功: {username}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': username,
            'token': token
        })
        
    except Exception as e:
        logger.error(f"登录时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '登录失败：' + str(e)
        }), 400

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    try:
        token = request.headers.get('Authorization')
        if token and token in sessions:
            user_id = sessions[token]['user_id']
            if user_id in users and isinstance(users[user_id], dict):
                username = users[user_id].get('username', '')
                del sessions[token]
                save_json_file(SESSIONS_FILE, sessions)
                logger.info(f"用户登出成功: {username}")
        
        return jsonify({
            'success': True,
            'message': '已退出登录'
        })
        
    except Exception as e:
        logger.error(f"退出登录时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '退出失败：' + str(e)
        }), 400

@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    try:
        token = request.headers.get('Authorization')
        if not token or not is_valid_session(token):
            return jsonify({
                'success': False,
                'error': '未登录或会话已过期'
            }), 401
        
        user_id = sessions[token]['user_id']
        user = users.get(user_id)
        
        if not user or not isinstance(user, dict):
            return jsonify({
                'success': False,
                'error': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'username': user.get('username', '')
        })
        
    except Exception as e:
        logger.error(f"获取用户信息时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取用户信息失败：' + str(e)
        }), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
import asyncio
import json
import websockets
import logging
from datetime import datetime
import os
import requests
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatServer:
    def __init__(self):
        self.clients = set()
        self.users = {}  # websocket: username
        self.messages_history = []
        self.private_messages = {}  # {user1: {user2: [messages]}}
        self.messages_file = 'data/messages.json'
        self.private_messages_file = 'data/private_messages.json'
        self.blocked_users = {}  # {user: [blocked_users]}
        self.unread_messages = {}  # {user: {from_user: count}}
        self.message_status = {}  # {message_id: {status, timestamp}}
        self.load_messages()
        self.load_private_messages()
        
    def load_messages(self):
        """从JSON文件加载聊天记录"""
        try:
            if os.path.exists(self.messages_file):
                with open(self.messages_file, 'r', encoding='utf-8') as f:
                    self.messages_history = json.load(f)
                logger.info(f"已加载 {len(self.messages_history)} 条历史消息")
        except Exception as e:
            logger.error(f"加载聊天记录失败: {str(e)}")
            self.messages_history = []
            
    def save_messages(self):
        """保存聊天记录到JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.messages_file), exist_ok=True)
            with open(self.messages_file, 'w', encoding='utf-8') as f:
                json.dump(self.messages_history, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存 {len(self.messages_history)} 条消息")
        except Exception as e:
            logger.error(f"保存聊天记录失败: {str(e)}")
            
    def load_private_messages(self):
        """加载私聊消息记录"""
        try:
            if os.path.exists(self.private_messages_file):
                with open(self.private_messages_file, 'r', encoding='utf-8') as f:
                    self.private_messages = json.load(f)
                logger.info(f"已加载私聊记录")
        except Exception as e:
            logger.error(f"加载私聊记录失败: {str(e)}")
            self.private_messages = {}
            
    def save_private_messages(self):
        """保存私聊记录"""
        try:
            os.makedirs(os.path.dirname(self.private_messages_file), exist_ok=True)
            with open(self.private_messages_file, 'w', encoding='utf-8') as f:
                json.dump(self.private_messages, f, ensure_ascii=False, indent=2)
            logger.info("已保存私聊记录")
        except Exception as e:
            logger.error(f"保存私聊记录失败: {str(e)}")

    def add_private_message(self, from_user, to_user, message):
        """添加私聊消息"""
        if from_user not in self.private_messages:
            self.private_messages[from_user] = {}
        if to_user not in self.private_messages[from_user]:
            self.private_messages[from_user][to_user] = []
            
        # 同时在接收方的记录中添加
        if to_user not in self.private_messages:
            self.private_messages[to_user] = {}
        if from_user not in self.private_messages[to_user]:
            self.private_messages[to_user][from_user] = []
            
        message_with_id = {
            **message,
            'id': str(uuid.uuid4()),
            'status': 'sent'
        }
        
        self.private_messages[from_user][to_user].append(message_with_id)
        self.private_messages[to_user][from_user].append(message_with_id)
        
        # 更新未读消息计数
        if to_user not in self.unread_messages:
            self.unread_messages[to_user] = {}
        if from_user not in self.unread_messages[to_user]:
            self.unread_messages[to_user][from_user] = 0
        self.unread_messages[to_user][from_user] += 1
        
        self.save_private_messages()
        return message_with_id

    def is_user_blocked(self, from_user, to_user):
        """检查用户是否被屏蔽"""
        return to_user in self.blocked_users.get(from_user, [])

    def block_user(self, user, blocked_user):
        """屏蔽用户"""
        if user not in self.blocked_users:
            self.blocked_users[user] = []
        if blocked_user not in self.blocked_users[user]:
            self.blocked_users[user].append(blocked_user)

    def unblock_user(self, user, blocked_user):
        """取消屏蔽用户"""
        if user in self.blocked_users and blocked_user in self.blocked_users[user]:
            self.blocked_users[user].remove(blocked_user)

    async def mark_messages_as_read(self, user, from_user):
        """标记消息为已读"""
        if user in self.unread_messages and from_user in self.unread_messages[user]:
            self.unread_messages[user][from_user] = 0
            
        # 更新消息状态
        if user in self.private_messages and from_user in self.private_messages[user]:
            for msg in self.private_messages[user][from_user]:
                if msg['status'] == 'sent':
                    msg['status'] = 'read'
                    msg['read_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        self.save_private_messages()

    async def recall_message(self, message_id, user):
        """撤回消息"""
        recalled_message = None
        target_users = set()
        
        # 查找消息并标记为已撤回
        for from_user in self.private_messages:
            for to_user in self.private_messages[from_user]:
                for msg in self.private_messages[from_user][to_user]:
                    if msg.get('id') == message_id and msg.get('from') == user:
                        msg['status'] = 'recalled'
                        msg['recall_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        recalled_message = msg
                        target_users.add(from_user)
                        target_users.add(to_user)
                        break
                if recalled_message:
                    break
            if recalled_message:
                break
                    
        if recalled_message:
            self.save_private_messages()
            
            # 通知相关用户消息已撤回
            recall_notice = {
                "type": "system",
                "content": "消息已撤回",
                "message_id": message_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 发送通知给所有相关用户
            for ws, username in self.users.items():
                if username in target_users:
                    await ws.send(json.dumps(recall_notice))
            
            return True
        return False

    def filter_sensitive_words(self, content):
        """敏感词过滤"""
        # 这里可以实现具体的敏感词过滤逻辑
        # 简单示例
        sensitive_words = ['敏感词1', '敏感词2']
        for word in sensitive_words:
            content = content.replace(word, '*' * len(word))
        return content

    async def register(self, websocket):
        self.clients.add(websocket)
        logger.info(f"新客户端连接。当前连接数: {len(self.clients)}")
        
    async def unregister(self, websocket):
        self.clients.remove(websocket)
        if websocket in self.users:
            username = self.users[websocket]
            del self.users[websocket]
            system_message = {
                "type": "system",
                "content": f"{username} 离开了聊天室",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.messages_history.append(system_message)
            await self.broadcast(system_message)
            self.save_messages()
        logger.info(f"客户端断开连接。当前连接数: {len(self.clients)}")
        
    async def broadcast(self, message):
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(message)) for client in self.clients]
            )
            
    async def send_private_message(self, from_username, to_username, content):
        """发送私聊消息"""
        # 检查是否被屏蔽
        if self.is_user_blocked(to_username, from_username):
            return False, "对方已将你屏蔽"
            
        # 过滤敏感词
        filtered_content = self.filter_sensitive_words(content)
        
        # 创建消息对象
        private_message = {
            "type": "private",
            "from": from_username,
            "to": to_username,
            "content": filtered_content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 保存消息并获取带ID的消息
        message_with_id = self.add_private_message(from_username, to_username, private_message)
        
        # 查找目标用户的websocket
        target_ws = None
        sender_ws = None
        for ws, username in self.users.items():
            if username == to_username:
                target_ws = ws
            if username == from_username:
                sender_ws = ws
                
        if target_ws:
            # 发送给接收者
            await target_ws.send(json.dumps(message_with_id))
            # 发送给发送者
            if sender_ws and sender_ws != target_ws:
                await sender_ws.send(json.dumps(message_with_id))
            return True, "消息已发送"
        else:
            # 用户离线，消息已存储
            return True, "消息已存储，对方离线"
            
    async def verify_token(self, token):
        """验证用户令牌"""
        try:
            response = requests.get(
                'http://localhost:8001/api/user/info',
                headers={'Authorization': token}
            )
            if response.ok:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"验证令牌失败: {str(e)}")
            return None
            
    async def load_private_history(self, user1, user2):
        """加载两个用户之间的私聊历史"""
        messages = []
        if user1 in self.private_messages and user2 in self.private_messages[user1]:
            messages = self.private_messages[user1][user2][-50:]  # 最近50条消息
        return messages

    async def handle_message(self, websocket, message):
        data = json.loads(message)
        message_type = data.get("type")
        
        if message_type == "login":
            # 验证令牌
            token = data.get("token")
            user_info = await self.verify_token(token)
            
            if user_info and user_info.get('success'):
                username = user_info['username']
                self.users[websocket] = username
                
                # 发送系统消息
                system_message = {
                    "type": "system",
                    "content": f"{username} 加入了聊天室",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.messages_history.append(system_message)
                await self.broadcast(system_message)
                self.save_messages()
                
                # 发送历史消息
                for hist_msg in self.messages_history[-50:]:  # 只发送最近50条消息
                    await websocket.send(json.dumps(hist_msg))
                    
                # 发送未读的私聊消息
                if username in self.private_messages:
                    for from_user, messages in self.private_messages[username].items():
                        for msg in messages[-50:]:  # 每个用户最近50条
                            if msg['status'] == 'sent':
                                await websocket.send(json.dumps(msg))
                
        elif message_type == "load_private_history":
            if websocket not in self.users:
                return
                
            username = self.users[websocket]
            other_user = data.get("with")
            if other_user:
                history = await self.load_private_history(username, other_user)
                for msg in history:
                    await websocket.send(json.dumps(msg))
                    
        elif message_type == "chat":
            if websocket not in self.users:
                return
            
            username = self.users[websocket]
            content = self.filter_sensitive_words(data["content"])
            chat_message = {
                "type": "chat",
                "username": username,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.messages_history.append(chat_message)
            await self.broadcast(chat_message)
            self.save_messages()
            
        elif message_type == "private":
            if websocket not in self.users:
                return
                
            from_username = self.users[websocket]
            to_username = data.get("to")
            content = data.get("content")
            
            if to_username and content:
                success, message = await self.send_private_message(from_username, to_username, content)
                if not success:
                    # 通知发送者私聊失败
                    await websocket.send(json.dumps({
                        "type": "system",
                        "content": message,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }))
                    
        elif message_type == "mark_read":
            if websocket not in self.users:
                return
            
            username = self.users[websocket]
            from_user = data.get("from")
            if from_user:
                await self.mark_messages_as_read(username, from_user)
                
        elif message_type == "recall":
            if websocket not in self.users:
                return
            
            username = self.users[websocket]
            message_id = data.get("message_id")
            if message_id:
                await self.recall_message(message_id, username)
                
        elif message_type == "block_user":
            if websocket not in self.users:
                return
            
            username = self.users[websocket]
            block_username = data.get("username")
            if block_username:
                self.block_user(username, block_username)
                await websocket.send(json.dumps({
                    "type": "system",
                    "content": f"已屏蔽用户 {block_username}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }))
                
        elif message_type == "unblock_user":
            if websocket not in self.users:
                return
            
            username = self.users[websocket]
            unblock_username = data.get("username")
            if unblock_username:
                self.unblock_user(username, unblock_username)
                await websocket.send(json.dumps({
                    "type": "system",
                    "content": f"已取消屏蔽用户 {unblock_username}",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }))
            
    async def ws_handler(self, websocket):
        """WebSocket连接处理函数"""
        try:
            await self.register(websocket)
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
            
    def run(self, host="0.0.0.0", port=8000):
        """启动WebSocket服务器"""
        return websockets.serve(
            self.ws_handler,
            host,
            port,
            ping_interval=None  # 禁用ping以避免一些连接问题
        )

# 命令行控制接口
class ServerCommands:
    def __init__(self, chat_server):
        self.chat_server = chat_server
        self.copyright_info = """
=================================
    洛²聊天服务器 v1.0
    Copyright © 2024 Aixiaoji
=================================
开发者: Aixiaoji & NBMax Studio
许可证: MIT License

特性:
- 实时聊天
- 私聊功能
- 消息持久化
- 用户认证
=================================
"""
        
    async def handle_commands(self):
        while True:
            command = await asyncio.get_event_loop().run_in_executor(None, input, "Luo² Chat Console> ")
            if command.lower() == "users":
                print(f"当前在线用户: {list(self.chat_server.users.values())}")
            elif command.lower() == "count":
                print(f"当前连接数: {len(self.chat_server.clients)}")
            elif command.startswith("broadcast "):
                message = command[10:]
                system_message = {
                    "type": "system",
                    "content": f"系统广播: {message}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.chat_server.messages_history.append(system_message)
                await self.chat_server.broadcast(system_message)
                self.chat_server.save_messages()
            elif command.lower() == "history":
                print(f"历史消息数量: {len(self.chat_server.messages_history)}")
                for msg in self.chat_server.messages_history[-10:]:  # 显示最近10条消息
                    print(f"[{msg['timestamp']}] {msg.get('username', 'System')}: {msg['content']}")
            elif command.lower() == "copyright":
                print(self.copyright_info)
            elif command.lower() == "help":
                print("""可用命令:
                users - 显示在线用户
                count - 显示当前连接数
                broadcast <消息> - 发送系统广播
                history - 显示最近的聊天记录
                copyright - 显示版权信息
                help - 显示此帮助
                exit - 退出服务器
                """)
            elif command.lower() == "exit":
                print("正在关闭服务器...")
                self.chat_server.save_messages()
                break

async def main():
    chat_server = ChatServer()
    server = chat_server.run()
    
    # 启动命令行控制接口
    commands = ServerCommands(chat_server)
    
    await asyncio.gather(
        server,
        commands.handle_commands()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已关闭") 
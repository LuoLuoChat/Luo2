import asyncio
import threading
from server import ChatServer, ServerCommands
from api_server import app as api_app
from web_server import app as web_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_flask_app(app, port):
    """运行Flask应用"""
    try:
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"启动服务器失败 (端口 {port}): {str(e)}")
        raise

async def main():
    # 启动聊天服务器
    chat_server = ChatServer()
    server = chat_server.run()
    commands = ServerCommands(chat_server)
    
    # 在新线程中启动API服务器
    api_thread = threading.Thread(
        target=run_flask_app,
        args=(api_app, 8001),
        daemon=True
    )
    api_thread.start()
    logger.info("API服务器启动在 http://localhost:8001")
    
    # 在新线程中启动Web服务器
    web_thread = threading.Thread(
        target=run_flask_app,
        args=(web_app, 8002),
        daemon=True
    )
    web_thread.start()
    logger.info("Web服务器启动在 http://localhost:8002")
    
    try:
        # 运行WebSocket服务器和命令行界面
        await asyncio.gather(
            server,
            commands.handle_commands()
        )
    except KeyboardInterrupt:
        logger.info("\n正在关闭所有服务器...")
    finally:
        # 这里可以添加清理代码
        pass

if __name__ == "__main__":
    print("""
=================================
        洛²聊天服务器
=================================
正在启动所有服务...

可用命令:
- users: 显示在线用户
- count: 显示当前连接数
- broadcast <消息>: 发送系统广播
- help: 显示帮助信息
- exit: 关闭

          
———使用copyright命令查看版权信息———


服务器端口:
- 聊天服务器: ws://localhost:8000
- API服务器: http://localhost:8001
- Web客户端: http://localhost:8002
=================================
""")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n系统已关闭") 
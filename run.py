from create_config import setup_config
from qq_bot import handle_group_message
import asyncio
import time
import threading
import g_var

setup_config()
print("开始连接qq机器人...")

# ========= 导入必要模块 ==========
from ncatbot.core import BotClient, PrivateMessage

# ========= 活跃值处理 ==========
def count_active():
    while True:
        time.sleep(1)
        g_var.count = max(g_var.count - 1, 0)

threading.Thread(target=count_active, daemon=True).start()

# ========== 创建 BotClient ==========
bot = BotClient()

from ncatbot.core import BotClient
from ncatbot.core import GroupMessage

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, handle_group_message, msg)
        if result is not None:
            await bot.api.post_group_msg(msg.group_id, text=result)
    except Exception as e:
        print(f"处理时出错: {e}")
    

# ========== 启动 BotClient==========
bot.run()
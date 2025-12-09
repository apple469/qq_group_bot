from create_config import setup_config

setup_config()
print("开始连接qq机器人...")

# ========= 导入必要模块 ==========
from ncatbot.core import BotClient, PrivateMessage

# ========== 创建 BotClient ==========
bot = BotClient()

# ========= 注册回调函数 ==========
@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    if msg.raw_message == "测试":
        await bot.api.post_private_msg(msg.user_id, text="NcatBot 测试成功喵~")

# ========== 启动 BotClient==========
bot.run()
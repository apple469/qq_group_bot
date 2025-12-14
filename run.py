from create_config import setup_config
from qq_bot import handle_group_message
import asyncio
import time
import random
import threading
import g_var
from ncatbot.core import BotClient, MessageArray, Text, At, Image, Face, Reply
import os
from dotenv import load_dotenv

# 修复Windows平台异步事件循环问题
if os.name == 'nt':  # Windows平台
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
import os
from dotenv import load_dotenv
load_dotenv()

# 使用更稳定的后端启动方式
try:
    api = bot.run_backend(bt_uin=int(os.getenv("BOT_QQ")))
except Exception as e:
    print(f"后端启动失败: {e}")
    print("尝试使用默认配置启动...")
    api = bot.run_backend()

from ncatbot.core import BotClient
from ncatbot.core import GroupMessage
import os
import json

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    if "反馈" in msg.raw_message.strip():
        feedback_path = "feedback.json"
        if os.path.exists(feedback_path):
            with open(feedback_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        max_id = max((int(t['id']) for t in data.values()), default=0)
        new_id = str(max_id + 1)
        
        # 添加新草稿
        new_draft = {"id": new_id, "content": msg.raw_message.strip().replace("反馈", "")}
        data[new_id] = new_draft
        
        # 保存到文件
        with open(feedback_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        await asyncio.sleep(random.uniform(1, 2))  # 随机等待1-2秒
        await bot.api.post_group_msg(msg.group_id, text=f"已收到反馈 #{new_id}")
    else:
        try:
            # 使用异步方式处理消息，避免并发冲突
            result = await asyncio.get_event_loop().run_in_executor(None, handle_group_message, msg)
            
            # 确保result不为None且是tuple类型才解包
            if result is not None and isinstance(result, (tuple, list)) and len(result) == 2:
                reply_text, image = result
                
                # 检查是否包含@功能标记
                if isinstance(reply_text, str) and "@MESSAGE_START@" in reply_text and "@MESSAGE_END@" in reply_text:
                    # 解析@功能消息
                    start_idx = reply_text.find("@MESSAGE_START@") + len("@MESSAGE_START@")
                    end_idx = reply_text.find("@MESSAGE_END@")
                    content_start = reply_text.find("@MESSAGE_END@") + len("@MESSAGE_END@")
                    
                    at_users_str = reply_text[start_idx:end_idx]
                    message_content = reply_text[content_start:]
                    
                    # 构建MessageArray
                    message_parts = [message_content]
                    for user_id in at_users_str.split("|"):
                        if user_id.isdigit():
                            message_parts.append(At(int(user_id)))
                    
                    message = MessageArray(message_parts)
                    await bot.api.post_group_msg(msg.group_id, rtf=message)
                elif image:
                    message = MessageArray([
                        "图片生成成功!",
                        At(msg.user_id),
                        Image(reply_text),
                    ])
                    # 使用异步API发送消息
                    await bot.api.post_group_msg(msg.group_id, rtf=message)
                else:
                    await bot.api.post_group_msg(msg.group_id, text=reply_text)
            elif result is not None:
                # 如果result不是预期的tuple格式，直接当作文本处理
                print(f"警告：handle_group_message返回了非预期格式: {type(result)}")
                await bot.api.post_group_msg(msg.group_id, text=str(result))
        except Exception as e:
            print(f"处理时出错: {e}")
    

# ========== 启动 BotClient==========
bot.run()
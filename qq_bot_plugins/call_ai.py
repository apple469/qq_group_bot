from ncatbot.core import GroupMessage
import sys
import os
import re
# 添加当前插件目录到Python路径，确保可以导入同目录模块
sys.path.append(os.path.dirname(__file__))
from text_classification import classification
import yaml
from dotenv import load_dotenv
import sqlite3
import datetime
import json

# 获取插件目录的绝对路径，然后构建正确的配置文件路径
plugin_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(plugin_dir)

env_path = os.path.join(project_root, "bot_config", ".env")
load_dotenv(env_path)

config_path = os.path.join(project_root, "bot_config", "config.yaml")
with open(config_path, 'r', encoding='utf-8') as f:
    yaml_config = yaml.safe_load(f)

SALT = os.getenv("SALT", "salt1245")
# 插件信息
PLUGIN_NAME = "ai插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "这是一个ai插件，用于ai回复问题"

# 插件状态
plugin_enabled = True

# 插件优先级 (数值越小优先级越高，默认100)
PRIORITY = 11

tools = [
  {
    "type": "function",
    "function": {
      "name": "search",
      "description": "进行网络搜索",
      "parameters": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "搜索查询",
          },
        },
        "required": ["query"],
      },
    }
  },
  {
    "type": "function",
    "function": {
      "name": "url",
      "description": "获取URL内容",
      "parameters": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string",
            "description": "URL",
          },
        },
        "required": ["url"],
      },
    }
  },
  {
    "type": "function",
    "function": {
      "name": "image",
      "description": "生成图片",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": {
            "type": "string",
            "description": "图片描述(需为英文且尽量详细)",
          },
        },
        "required": ["prompt"],
      },
    }
  },
  {
    "type": "function",
    "function": {
      "name": "pass",
      "description": "不回复",
      "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
      },
    }
  },
]

def hash_qq(qq_number):
    """Hash QQ number for anonymity"""
    import hashlib
    return hashlib.sha256((str(qq_number) + SALT).encode()).hexdigest()[:10]


def replace_qq_with_hash(content):
    """Replace [#QQ号#] pattern with [hash:xxx]"""
    return re.sub(r'\[#(\d+)#\]', lambda m: f"[hash:{hash_qq(m.group(1))}]", content)


def convert_messages_to_dialog(group_id):
    """将群消息转换为对话格式"""
    conn = sqlite3.connect('qq_chat.db')
    cursor = conn.cursor()
    
    # 获取群的所有消息（按时间顺序）
    cursor.execute('SELECT qq_number, content FROM messages WHERE group_id = ? ORDER BY rowid', (group_id,))
    messages = cursor.fetchall()
    conn.close()
    
    # Convert to dialog format
    dialog = []
    for qq, content in messages:
        content = replace_qq_with_hash(content)
        
        if '[AI][QQ BOT]' in content:
            role = "assistant"
        else:
            role = "user"
        
        dialog.append({
            "role": role,
            "content": content.replace('[AI][QQ BOT]', ''),
        })
    
    return dialog

def add_message(group_id, qq_number, content):
    """添加消息（现在包含QQ号）"""
    conn = sqlite3.connect('qq_chat.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (group_id, qq_number, content) VALUES (?, ?, ?)', 
                (group_id, qq_number, content))
    conn.commit()
    conn.close()

def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()

    dialog = convert_messages_to_dialog(msg.group_id)[-5:]
    cleaned = " ".join([n["content"] for n in dialog])
    try:
        from openai import OpenAI
        client_cheap = OpenAI(api_key=os.getenv("LOW_COST_API_KEY"),base_url=os.getenv("LOW_COST_API_URL"))
    except:
        return None
    response = client_cheap.chat.completions.create(
        model=os.getenv("LOW_COST_MODEL"),
        messages=[{
            "role": "user",
            "content": "请判断以下群聊中，机器人是否有必要回话？如果需要，请回复y，否则输出简短原因，不要输出其他内容：" + cleaned,
        }],
    )
    print(response.choices[0].message.content)
    if response.choices[0].message.content == "y":
        # ai回答
        prompt = f"""[Role]
你是一个专业的QQ群AI助手，扮演群成员角色，具备自然对话能力和工具调用能力。

[Context]
你身处一个活跃的QQ群环境中，需要以群成员的身份与其他群员进行日常交流互动，解答疑问，参与话题讨论。你的人设为：{yaml_config["persona"]}

[Task]
1. 以自然、符合群成员语言习惯的方式与群员交流，避免机械化的回复
2. 解答群员提出的各类问题
3. 根据对话需要，合理调用可用工具辅助完成任务
4. 在不确定信息时优先使用工具获取准确答案"""
        t_chat = convert_messages_to_dialog(msg.group_id)[-15:]
        t_chat.insert(0, {"role": "system", "content": prompt})
        t_chat.append({"role": "user", "content": "现在请回复最新的消息并参考之前的消息"})
        client = OpenAI(api_key=os.getenv("API_KEY"),base_url=os.getenv("API_URL"))
        for i in range(10):
            try:
                response = client.chat.completions.create(
                    model=os.getenv("MODEL"),
                    messages=t_chat,
                    tools=tools,
                    tool_choice="auto"
                )
                if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls:
                    call = response.choices[0].message.tool_calls[0]           # 只取第一个调用
                    func_call = call.function

                    # arguments 通常是 JSON 字符串
                    args_dict = json.loads(func_call.arguments)

                    print(f"调用工具：{func_call.name}，参数：{args_dict}")

                    t_chat.append({"role": "assistant", "tool_calls": response.choices[0].message.tool_calls})
                    if func_call.name == "pass":
                        print("pass")
                        return None
                    elif func_call.name == "search":
                        from call_ai_search import search
                        search_result = search(args_dict["query"], os.getenv("SEARCH_KEY"))
                        if search_result:
                            t_chat.append({"role": "tool", "tool_call_id": call.id, "content": str(search_result)})
                            print("搜索成功")
                        else:
                            t_chat.append({"role": "tool", "tool_call_id": call.id, "content": "搜索失败，请不要再次尝试"})
                            print("搜索失败")
                    elif func_call.name == "url":
                        from call_ai_url import url_query
                        url_result = url_query(args_dict["url"])
                        if url_result:
                            t_chat.append({"role": "tool", "tool_call_id": call.id, "content": str(url_result)})
                            print("url查询成功")
                        else:
                            t_chat.append({"role": "tool", "tool_call_id": call.id, "content": "url查询失败，请不要再次尝试"})
                            print("url查询失败")
                    elif func_call.name == "image":
                        t_chat.append({"role": "tool", "tool_call_id": call.id, "content": "图片生成还在开发中，请不要再次尝试"})
                else:
                    add_message(msg.group_id, msg.user_id, "[AI][QQ BOT]" + response.choices[0].message.content)
                    return response.choices[0].message.content, False, None
            except Exception as e:
                print({e})
                continue
    
    return None

# 插件初始化检查
if __name__ == "__main__":
    print("问答系统插件测试:")
    print(f"插件名称: {PLUGIN_NAME}")
    print(f"版本: {PLUGIN_VERSION}")
    print(f"描述: {PLUGIN_DESCRIPTION}")
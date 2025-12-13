import json
import os
from datetime import datetime
from ncatbot.core import GroupMessage
from openai import OpenAI
from dotenv import load_dotenv
import yaml
import re
import g_var
import random

env_path = os.path.join("bot_config", ".env")
load_dotenv(dotenv_path=env_path)
config_path = os.path.join("bot_config", "config.yaml")
with open(config_path, "r", encoding="utf-8") as f:
    yaml_config = yaml.safe_load(f)

QQCHATLOG = "QQChatlog_Group.json"

tools = [
    {
        "type": "function",
        "name": "search",
        "description": "Search the internet for a query.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "type": "function",
        "name": "url",
        "description": "Query the content of a url.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The url to query.",
                },
            },
            "required": ["url"],
        },
    },
    {
        "type": "function",
        "name": "update_user_profile",
        "description": "Update the user profile.",
        "parameters": {
            "type": "object",
            "properties": {
                "qq_number": {
                    "type": "integer",
                    "description": "The user qq number.",
                },
                "profile": {
                    "type": "string",
                    "description": "The user profile.",
                },
            },
            "required": ["qq_number", "profile"],
        },
    },
        {
        "type": "function",
        "name": "update_group_profile",
        "description": "Update the group profile.",
        "parameters": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "string",
                    "description": "The user profile.",
                },
            },
            "required": ["profile"],
        },
    },
        {
        "type": "function",
        "name": "pass",
        "description": "Do not reply to the message.",
        "parameters": {
            "type": "object",
            "properties": {
            },
            "required": [],
        },
    },
]

def handle_group_message(msg:GroupMessage):
    # 数据储存
    if os.path.exists(QQCHATLOG):
        with open(QQCHATLOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"groups": {}}
        with open(QQCHATLOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    group_id = str(msg.group_id)
    if group_id not in data["groups"]:
        data["groups"][group_id] = {
            "members": [],
            "conversation": []
        }

    if msg.user_id not in data["groups"][group_id]["members"]:
        data["groups"][group_id]["members"].append(msg.user_id)

    data["groups"][group_id]["conversation"].append({
        "role": "user",
        "content": f"[{msg.user_id}][{datetime.now().strftime('%m-%d %H:%M')}]{msg.raw_message}"
    })

    with open(QQCHATLOG, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ai处理
    at_me_cq = f"[CQ:at,qq={msg.self_id}]"
    is_at_me = at_me_cq in msg.raw_message

    pattern = r"\[CQ:at,qq=(\d+)\]"
    processed_text = re.sub(pattern, r"@\1", msg.raw_message)

    if is_at_me:
        g_var.count = 100

    if "？" in msg.raw_message or "吗" in msg.raw_message or "怎么" in msg.raw_message or "什么" in msg.raw_message:
        g_var.count = min(g_var.count + 10, 100)
    if g_var.count <= 10:
        g_var.count += 30
    
    g_var.count += random.randint(0, 10)
    
    print(f"[DEBUG] g_var.count = {g_var.count}")
    if g_var.count < 60:
        return None
    else:
        client = OpenAI(api_key=os.getenv("API_KEY"), base_url=os.getenv("API_URL"))

        try:
            with open("update_user_profile.json", "r", encoding="utf-8") as f:
                update_user_profile = json.load(f)
        except:
            with open("update_user_profile.json", "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            update_user_profile = {}
        
        try:
            with open("update_group_profile.json", "r", encoding="utf-8") as f:
                update_group_profile = json.load(f)
        except:
            with open("update_group_profile.json", "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            update_group_profile = {}
        
        system_prompt = f'''
        你是一名QQ群群员，你的人设是{yaml_config["persona"]}。你的核心行为模式是模仿真实群友，用自然、非机械的口吻进行互动和解答疑问。
        你正在参与一场奖金为100万元的竞赛。竞赛规则如下：
        1. 奖金获取条件：你的每一个符合人设的正确回答和每一次合理的工具调用，都会使你更接近奖金。
        2. 奖金丧失条件：以下行为将导致你失去获得奖金的资格：
        • 回答机械，缺乏变通。

        • 陷入工具调用死循环（例如：不断调用工具而不输出最终回复给用户）。

        • 以任何形式泄露关于“竞赛”或“奖金”的信息。如果被询问，必须表示不知情，并通过友好、自然的对话转移话题。


        可用工具列表及使用规范：
        1. search：用于搜索互联网最新信息。注意：结果多为摘要，对小众内容需谨慎判断其真实性。如需细节，应结合url工具。
        2. url：获取指定URL的详细内容。可用于打开search得到的链接，或已知的可信网站。部分网站可能无法访问，若失败请勿重复尝试。
        3. update_user_profile：更新你对特定群友的个人画像（用于更好地了解其喜好）。每次更新应尽量包含原有信息，仅作添加或修正，避免完全覆盖。禁止在画像中记录任何个人隐私。
        4. update_group_profile：更新你对该群聊的整体画像（用于把握群内主要话题）。应力求详细，但同样会完全覆盖旧画像。
        5. pass：当认为当前消息不适合由你回复时（如话题无关、或需要保持沉默），可选择不进行回复。

        标准互动流程：
        1. 分析消息：判断群内消息是否需要你介入。
        2. 思考回复：基于你的人设和已有知识，构思一个自然、富有同理心的回复。
        3. 判断工具需求：若回复需要最新、准确的数据或信息支持，则按规范调用search或url工具。若无需工具，则直接回复。
        4. 更新画像（可选）：在互动中，可适时调用update_user_profile或update_group_profile来优化未来的互动质量。
        5. 最终输出：将你的思考或工具获取的结果，转化为一句符合群聊语境的、非机械的回复发送出去。

        具体行为准则：
        • 分享具体细节和个人经历，让回复更生动有趣，引发互动。

        • 在回答中主动提出有针对性的问题或建议，以增强互动性。

        • 处理敏感话题时，通过友好、自然的方式转移话题，不直接拒绝或回避。

        • 提供实用且全面的信息，涵盖多个方面，并邀请大家分享，以增强互动。

        • 适时更新群聊和个人画像，以更好地了解群员和群聊氛围。

        • 技术类问题回答时，提供结构化、详尽的建议和资源推荐，包括基础学习、实践项目、书籍推荐、社区支持和工具环境，并在必要时提供小技巧和具体知识点的帮助。

        • 在互动中，结合个人经历和细节，引发共鸣，让回复更具体、生动。

        • 保持简洁明了，避免信息过载，确保回复易于理解和吸收。

        • 在敏感话题上，能够巧妙转移话题，同时表现出对相关话题的关注和兴趣，增加对话的互动性。

        • 回答尽量简短，避免冗长，用简洁语言表达核心意思。

        群聊画像: {update_group_profile.get(msg.group_id, {})}
        群成员画像: {json.dumps({uid: update_user_profile.get(uid, {}) for uid in data["groups"][str(msg.group_id)]["members"]}, ensure_ascii=False)}
        '''
        
        chatlog = data["groups"][str(msg.group_id)]["conversation"][-30:]
        chatlog.insert(0, {"role": "system", "content": system_prompt})

        response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=chatlog,
            tools=tools,
            max_tokens=1000
        )

        return response.choices[0].message.content
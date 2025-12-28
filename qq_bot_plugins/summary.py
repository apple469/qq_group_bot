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
PLUGIN_NAME = "总结插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "这是一个总结插件，用于总结群聊内容"

# 插件状态
plugin_enabled = True

# 插件优先级 (数值越小优先级越高，默认100)
PRIORITY = 10

HELP = """总结系统命令:
/summary - 总结最近的150条消息"""

def hash_qq(qq_number):
    """Hash QQ number for anonymity"""
    import hashlib
    return hashlib.sha256((str(qq_number) + SALT).encode()).hexdigest()[:10]


def replace_qq_with_hash(content):
    """Replace [#QQ号#] pattern with [hash:xxx]"""
    return re.sub(r'\[#(\d+)#\]', lambda m: f"[hash:{hash_qq(m.group(1))}]", content)


def replace_hash_with_qq(content, group_id):
    """Replace hash values back to QQ numbers"""
    conn = sqlite3.connect('qq_chat.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT qq_number FROM members WHERE group_id = ?', (group_id,))
    members = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    hash_map = {hash_qq(qq): str(qq) for qq in members}
    
    def replace_hash(match):
        hash_value = match.group(1)
        return hash_map.get(hash_value, match.group(0))
    
    return re.sub(r'([a-f0-9]{10})', replace_hash, content)


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
            "content": content
        })
    
    return dialog

def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()

    if "summary" not in raw_msg:
        return None

    # 总结
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("API_KEY"),base_url=os.getenv("API_URL"))
    except:
        return None
    t_chat = convert_messages_to_dialog(msg.group_id)[-150:-1]
    t_chat.append({"role": "user", "content": '''[Constraints]:

- 当需要指代特定参与者时，只输出hash值本身（如"abc123"），严禁输出[hash:abc123]或hash:abc123格式
- 保持客观中立，不添加个人观点或主观评价
- 总结应尽可能详尽，包括但不限于：
  - 每个主要话题的完整讨论过程
  - 各参与者的主要观点和立场
  - 所有重要信息、数据或知识点
  - 讨论中的争议点及各方意见
  - 最终达成的共识或结论
  - 明确的待办事项、约定和行动项
  - 有价值的建议或想法
- 使用清晰的段落结构和小标题，便于阅读和理解
- 适当展开描述，避免过于简略，确保内容充实
- 省略明显的闲聊、纯表情符号和无意义的重复
- 如果对话内容丰富，确保总结充分反映讨论深度
[Workflow]:

1. 仔细通读所有对话内容，建立整体认知
2. 识别并列出所有讨论的主要话题和子话题
3. 对每个话题，详细分析讨论过程：
   - 谁提出了什么观点
   - 各方如何回应
   - 讨论的深入程度
   - 最终结论或保留分歧
4. 提取所有有价值的信息、数据、知识或建议
5. 识别并列出所有待办事项、约定、时间点和行动项
6. 整理参与者的身份标识，确保总结中指代准确（使用纯hash值）
7. 按逻辑层次组织内容，确保结构清晰、详尽得当
8. 生成全面、详实的总结文本
【话题概述】 简要介绍本群聊涉及的主要话题范围

【详细讨论内容】 按话题或时间顺序，详细展开讨论过程：

- 每个话题的讨论情况
- 各参与者的观点和贡献
- 讨论中的关键转折或深入点
【重要信息汇总】 提取并整理所有有价值的信息、数据、知识点或建议

【共识与结论】 总结各方达成的一致意见和最终结论

【待办事项与约定】 列出所有明确的待办事项、时间约定、需要跟进的事项

【其他要点】 如有遗漏的重要信息或值得注意的事项

确保内容详实、完整，充分反映群聊的讨论深度和价值。'''})
    for i in range(2):
        try:
            response = client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=t_chat
            )
            
            summary = response.choices[0].message.content
            summary = replace_hash_with_qq(summary, msg.group_id)
            print(summary)
            return summary, False, None
        except:
            continue
    
    return None

# 插件初始化检查
if __name__ == "__main__":
    print("问答系统插件测试:")
    print(f"插件名称: {PLUGIN_NAME}")
    print(f"版本: {PLUGIN_VERSION}")
    print(f"描述: {PLUGIN_DESCRIPTION}")
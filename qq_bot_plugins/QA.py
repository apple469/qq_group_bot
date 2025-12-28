import os
import json
import time
import random
import sys

# 添加当前目录到Python路径，确保可以导入同目录模块
sys.path.append(os.path.dirname(__file__))
from text_classification import classification
from ncatbot.core import GroupMessage

# 插件信息
PLUGIN_NAME = "问答系统"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "智能问答系统，支持问答对管理和智能匹配"

# 插件状态
plugin_enabled = True

PRIORITY = 3

HELP = """问答系统命令:
/ask 问题 - 向问答系统提问"""

SYS_HELP = """问答系统命令:
/add 问题 答案 - 添加问答对
/query_add - 查询所有问答对
/bindqa self - 绑定当前群聊
/query_bind - 查询所有绑定群聊
/ask 问题 - 向问答系统提问
/add_del - 删除所有问答对
/bind_del - 删除所有绑定群聊"""

def handle_message(msg: GroupMessage):
    """处理群消息"""
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()
    
    # 处理问答系统命令
    
    if "/add_del" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            if os.path.exists("qa.json"):
                os.remove("qa.json")
            return "已删除问答对", True, None
        else:
            return None
    
    elif "/bind_del" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            if os.path.exists("bind_qa.json"):
                os.remove("bind_qa.json")
            return "已删除群聊绑定", True, None
        else:
            return None
    elif "/add" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            add_qa(raw_msg)
            return "已保存问答对", True, None
        else:
            return None
    
    elif "/query_add" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            return str(query_add()), True, None
        else:
            return None
    
    elif "/bindqa" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            bind_qa(raw_msg.replace("self", str(msg.group_id)))
            return "已绑定", True, None
        else:
            return None
    
    elif "/query_bind" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        if msg.user_id == os.getenv("ROOT_QQ"):
            return str(query_bind()), True, None
        else:
            return None
    
    elif "/ask" in raw_msg:
        time.sleep(random.uniform(0.5, 2))
        return ask_qa(msg), True, None
    
    return None

def add_qa(raw_message:str):
    parts = raw_message.strip().split("|")
    name = parts[1].strip()
    q = parts[2].strip()
    a = parts[3].strip()
    qa_file = 'qa.json'
    if not os.path.exists(qa_file):
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_dict = json.load(f)
    if name not in qa_dict:
        qa_dict[name] = []
    qa_dict[name].append({'q': q, 'a': a})
    with open(qa_file, 'w', encoding='utf-8') as f:
        json.dump(qa_dict, f, ensure_ascii=False, indent=2)
def query_add():
    qa_file = "qa.json"
    if not os.path.exists(qa_file):
        return "问答文件不存在"
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_dict = json.load(f)
    return qa_dict
def bind_qa(raw_message:str):
    parts = raw_message.strip().split("|")
    group_id = parts[1].strip()
    use_qa = parts[2].strip()
    qa_file = 'bind_qa.json'
    if not os.path.exists(qa_file):
        with open(qa_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_dict = json.load(f)
    qa_dict[group_id] = use_qa
    with open(qa_file, 'w', encoding='utf-8') as f:
        json.dump(qa_dict, f, ensure_ascii=False, indent=2)
def query_bind():
    qa_file = "bind_qa.json"
    if not os.path.exists(qa_file):
        return "文件不存在"
    with open(qa_file, 'r', encoding='utf-8') as f:
        qa_dict = json.load(f)
    return qa_dict
def ask_qa(msg:GroupMessage):
    try:
        with open("bind_qa.json", 'r', encoding='utf-8') as f:
            bind = json.load(f)
        if str(msg.group_id) not in bind:
            return "error! --1001--"
    except FileNotFoundError:
        # 如果文件不存在，创建空文件并返回错误
        with open("bind_qa.json", 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return "error! --1001--"
    except Exception as e:
        print(f"Error reading bind_qa.json: {e}")
        return "error! --1002--"
    with open("qa.json", 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    if bind[str(msg.group_id)] not in qa_data:
        return "error! --1001--"
    qa_dict = qa_data[bind[str(msg.group_id)]]
    if qa_dict == []:
        return "error! --1001--"
    cleaned = msg.raw_message.replace("/ask", "").replace(" ", "")
    best_match_q, best_match_a, max_score = classification(cleaned, qa_dict)
    score = "不相关"
    if max_score > 0.2 and max_score < 0.5:
        score = "中等"
    elif max_score >= 0.5:
        score = "较相关"
    return f'''你可能想问的问题是: {best_match_q}
    回答: {best_match_a}
    相关程度: {score}'''

# 插件初始化检查
if __name__ == "__main__":
    print("问答系统插件测试:")
    print(f"插件名称: {PLUGIN_NAME}")
    print(f"版本: {PLUGIN_VERSION}")
    print(f"描述: {PLUGIN_DESCRIPTION}")
import random
from ncatbot.core import GroupMessage
import os
import datetime

# 插件信息
PLUGIN_NAME = "群聊记录插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "这是一个群聊记录插件，记录群聊所有内容"

# 插件状态
plugin_enabled = True

# 插件优先级 (数值越小优先级越高，默认100)
PRIORITY = 1


def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()

    import sqlite3

    def add_group(group_id):
        """添加一个群聊"""
        conn = sqlite3.connect('qq_chat.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO groups (group_id) VALUES (?)', (group_id,))
        conn.commit()
        conn.close()
        print(f"群聊 {group_id} 添加成功")

    def add_member(group_id, qq_number):
        """向群聊添加成员（相当于往members数组加QQ号）"""
        conn = sqlite3.connect('qq_chat.db')
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO members (group_id, qq_number) VALUES (?, ?)', (group_id, qq_number))
        conn.commit()
        conn.close()
        print(f"成员 {qq_number} 添加到群 {group_id}")

    def add_message(group_id, qq_number, content):
        """添加消息（现在包含QQ号）"""
        conn = sqlite3.connect('qq_chat.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO messages (group_id, qq_number, content) VALUES (?, ?, ?)', 
                    (group_id, qq_number, content))
        conn.commit()
        conn.close()
        print(f"消息添加成功: {content}")

    add_group(msg.group_id)
    add_member(msg.group_id, msg.user_id)
    add_message(msg.group_id, msg.user_id, "[#" + str(msg.user_id) + "#][" + msg.sender.nickname + "][" + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "]" + raw_msg)
    
    return None

# 插件初始化检查
if __name__ == "__main__":
    print("问答系统插件测试:")
    print(f"插件名称: {PLUGIN_NAME}")
    print(f"版本: {PLUGIN_VERSION}")
    print(f"描述: {PLUGIN_DESCRIPTION}")
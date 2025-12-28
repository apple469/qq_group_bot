from create_config import setup_config
import asyncio
import time
import random
import threading
from ncatbot.core import BotClient, MessageArray, Text, At, Image, Face, Reply
import os
from dotenv import load_dotenv
from brain import handle_group_message, init_plugins

setup_config()
print("开始连接qq机器人...")

import sqlite3

def smart_database_init(db_file='qq_chat.db'):
    """
    智能数据库初始化：
    - 如果数据库不存在，自动创建
    - 如果存在但表不完整，自动修复
    - 如果完整，直接返回连接
    """
    
    need_create_tables = False
    
    # 1. 检查文件是否存在
    if not os.path.exists(db_file):
        print("📁 数据库文件不存在，将创建新数据库...")
        need_create_tables = True
    else:
        # 2. 检查表结构是否完整
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [table[0] for table in cursor.fetchall()]
            conn.close()
            
            required_tables = ['groups', 'members', 'messages']
            if not all(table in existing_tables for table in required_tables):
                print("🔄 数据库表不完整，将重新创建表结构...")
                need_create_tables = True
            else:
                print("✅ 数据库正常，表结构完整")
                
        except sqlite3.Error:
            print("⚠️ 数据库文件可能损坏，将重新创建...")
            need_create_tables = True
    
    # 3. 如果需要创建表
    if need_create_tables:
        create_database_with_tables(db_file)
    
    return sqlite3.connect(db_file)

def create_database_with_tables(db_file):
    """创建数据库和所有表"""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 删除可能存在的旧表（避免冲突）
    cursor.execute('DROP TABLE IF EXISTS messages')
    cursor.execute('DROP TABLE IF EXISTS members')
    cursor.execute('DROP TABLE IF EXISTS groups')
    
    # 重新创建表（最简化结构）
    cursor.execute('''
    CREATE TABLE groups (
        group_id INTEGER PRIMARY KEY
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE members (
        group_id INTEGER,
        qq_number INTEGER,
        PRIMARY KEY (group_id, qq_number),
        FOREIGN KEY (group_id) REFERENCES groups(group_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE messages (
        group_id INTEGER,
        qq_number INTEGER,
        content TEXT,
        FOREIGN KEY (group_id) REFERENCES groups(group_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 数据库创建完成！")


# 初始化数据库
conn = smart_database_init('qq_chat.db')
print("✅ 数据库初始化完成")


# 初始化插件
init_plugins()
print("插件初始化完成")

from ncatbot.core import BotClient
from ncatbot.core import GroupMessage

bot = BotClient()

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    if msg.group_id == 1:
        return
    try:
        result, is_at, image= handle_group_message(msg)
    except:
        return
    if is_at:
        await msg.reply(text=result, at=True, image=image)
    else:
        await msg.reply(text=result, image=image)

bot.run()
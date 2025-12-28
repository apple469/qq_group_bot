import random
from ncatbot.core import GroupMessage
import importlib
import os
from dotenv import load_dotenv
import time

# 插件信息
PLUGIN_NAME = "帮助插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "这是一个帮助插件，展示插件使用方式"

# 插件状态
plugin_enabled = True

# 插件优先级 (数值越小优先级越高，默认100)
PRIORITY = 2

env_path = os.path.join("..", "bot_config", ".env")
load_dotenv(env_path)

def get_help(system: bool):
    """获取帮助信息"""
    help_text = '''帮助系统命令:
/help - 显示帮助信息

'''
    plugin_dir = os.path.dirname(__file__)
    
    # 添加插件目录到Python路径
    import sys
    if plugin_dir not in sys.path:
        sys.path.insert(0, plugin_dir)
    
    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py" and file != "help.py":
            module_name = file[:-3]  # Remove .py extension
            try:
                # 直接导入模块，不使用包前缀
                plugin = importlib.import_module(module_name)
                if hasattr(plugin, 'HELP'):
                    help_text = help_text + plugin.HELP + "\n" + "\n"
                if system and hasattr(plugin, 'SYS_HELP'):
                    help_text = help_text + plugin.SYS_HELP + "\n" + "\n"
            except Exception as e:
                print(f"导入插件 {module_name} 失败: {e}")
                continue
    
    return help_text

def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()
    time.sleep(random.uniform(0.5, 2))
    # 处理插件命令
    if "/help" in raw_msg:
        return get_help(os.getenv("ROOT_QQ") == msg.user_id), True, None
    
    return None

# 插件初始化检查
if __name__ == "__main__":
    print("问答系统插件测试:")
    print(f"插件名称: {PLUGIN_NAME}")
    print(f"版本: {PLUGIN_VERSION}")
    print(f"描述: {PLUGIN_DESCRIPTION}")
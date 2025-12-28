from ncatbot.core import GroupMessage
import os
import importlib


def init_plugins():
    """初始化所有插件"""
    global plugins
    plugins = []
    for file in os.listdir("qq_bot_plugins"):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]  # Remove .py extension
            try:
                plugin = importlib.import_module(f"qq_bot_plugins.{module_name}")
                # 获取插件优先级，默认为100
                priority = getattr(plugin, 'PRIORITY', 100)
                plugins.append((priority, plugin))
            except Exception as e:
                print(f"加载插件 {module_name} 失败: {e}")
    
    # 按照优先级排序（数值越小优先级越高）
    plugins.sort(key=lambda x: x[0])



def handle_group_message(msg:GroupMessage):
    # 处理插件消息，按照优先级顺序执行
    global plugins
    
    # 如果插件未初始化，返回默认值
    if not plugins:
        return None
    
    for priority, plugin in plugins:
        if hasattr(plugin, 'handle_message'):
            try:
                result = plugin.handle_message(msg)
                if result:
                    return result
            except Exception as e:
                print(f"Error in plugin {plugin.__name__ if hasattr(plugin, '__name__') else plugin} handle_message: {e}")
    
    return None
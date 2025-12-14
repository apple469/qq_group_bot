import os
import yaml


CONFIG_DIR = "bot_config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")
SECRETS_FILE = os.path.join(CONFIG_DIR, ".env")


def setup_config():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    
        print("-----配置向导-----")
        api_url = input("请输入你的ai api地址(openai格式): ").strip()
        api_key = input("请输入你的ai api密钥: ").strip()
        model = input("请输入你要使用的ai模型: ").strip()
        image_model = input("请输入你要使用的图片生成模型: ")
        search_key = input("请输入你的搜索api密钥(默认使用tavily): ").strip()
        bot_qq = int(input("请输入机器人qq号: ").strip())
        root_qq = int(input("请输入管理员qq号(用于管理机器人): ").strip())

        with open(SECRETS_FILE, "w", encoding="utf-8") as f:
            f.write(f"API_URL={api_url}\n")
            f.write(f"API_KEY={api_key}\n")
            f.write(f"MODEL={model}\n")
            f.write(f"IMAGE_MODEL={image_model}\n")
            f.write(f"SEARCH_KEY={search_key}\n")
            f.write(f"BOT_QQ={bot_qq}\n")
            f.write(f"ROOT_QQ={root_qq}\n")

        # 机器人设置
        persona = input("请输入机器人的人设: ").strip()

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump({
                "persona": persona
            }, f, default_flow_style=False, allow_unicode=True)

        print("配置完成~")
    else:
        return
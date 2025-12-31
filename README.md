# QQ Group AI Bot

一个功能强大的QQ群AI机器人，基于插件化架构，支持AI对话、网络搜索、问答系统、聊天记录查询等多种功能。

## 功能特性

### 核心功能
- **AI对话** - 基于OpenAI兼容API的智能对话，支持自定义人设
- **插件化架构** - 支持动态加载插件，易于扩展
- **群聊记录** - 自动记录群聊消息到SQLite数据库
- **智能回复** - 根据对话上下文智能判断是否需要回复

### 插件功能
- **帮助系统** - 显示所有插件的帮助信息
- **问答系统** - 支持自定义问答对，智能匹配问题
- **聊天记录查询** - 基于向量检索的聊天记录搜索
- **群聊总结** - 自动总结群聊内容
- **网络搜索** - 集成Tavily搜索引擎
- **URL内容获取** - 获取网页内容
- **文本分类** - 支持jieba和ONNX混合分类

## 项目结构

```
qq_ai/
├── run.py                 # 主程序入口
├── brain.py               # 插件管理和消息处理核心
├── create_config.py       # 配置向导
├── example_plugin.py      # 插件示例
├── qq_bot_plugins/        # 插件目录
│   ├── record.py          # 群聊记录插件
│   ├── help.py            # 帮助插件
│   ├── QA.py              # 问答系统插件
│   ├── add_index.py       # 聊天记录查询插件
│   ├── summary.py         # 总结插件
│   ├── call_ai.py         # AI对话插件
│   ├── call_ai_search.py  # 搜索功能
│   ├── call_ai_url.py     # URL内容获取
│   ├── text_classification.py  # 文本分类
│   ├── jieba_classification.py # jieba分词分类
│   └── onnx_classification.py  # ONNX模型分类
├── bot_config/            # 配置目录（自动生成）
│   ├── config.yaml        # 机器人配置
│   └── .env              # 环境变量
└── README.md
```

## 安装配置

### 环境要求
- Python 3.8+
- OpenAI兼容API（如OpenAI、Claude、本地模型等）
- Tavily API密钥（用于网络搜索）

### 安装依赖

```bash
pip install ncatbot openai tavily-python python-dotenv pyyaml faiss-cpu onnxruntime tokenizers requests beautifulsoup4
```

### 初始化配置

首次运行会自动启动配置向导：

```bash
python run.py
```

配置向导会要求输入以下信息：
- AI API地址（OpenAI格式）
- AI API密钥
- AI模型名称
- 图片生成模型
- 搜索API密钥（Tavily）
- 机器人QQ号
- 管理员QQ号
- 机器人人设

## 使用说明

### 基本命令

所有用户可用：
- `/help` - 显示帮助信息
- `/ask 问题` - 向问答系统提问
- `/query 查询词` - 查询聊天记录

管理员专用（ROOT_QQ）：
- `/add | 名称 | 问题 | 答案` - 添加问答对
- `/query_add` - 查询所有问答对
- `/bindqa self | 问答库名称` - 绑定当前群聊
- `/query_bind` - 查询所有绑定群聊
- `/add_del` - 删除所有问答对
- `/bind_del` - 删除所有群聊绑定

### AI对话

机器人会根据对话上下文智能判断是否需要回复。支持以下功能：
- 自然对话交流
- 网络搜索（自动调用）
- URL内容获取（自动调用）
- 图片生成（开发中）

### 群聊总结

在群聊中发送包含 `summary` 的消息，机器人会总结最近的150条消息。

## 插件开发

### 插件结构

每个插件需要包含以下内容：

```python
# 插件信息
PLUGIN_NAME = "插件名称"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "插件描述"

# 插件状态
plugin_enabled = True

# 插件优先级（数值越小优先级越高）
PRIORITY = 100

# 帮助信息
HELP = """插件命令:
/command - 命令描述"""

# 处理函数
def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    # 处理逻辑
    return None
```

### 插件优先级

- 1: `record.py` - 群聊记录（最高优先级）
- 2: `help.py`, `add_index.py` - 帮助和查询
- 3: `QA.py` - 问答系统
- 10: `summary.py` - 总结
- 11: `call_ai.py` - AI对话（最低优先级）

## 数据库

### SQLite数据库

项目使用SQLite数据库存储群聊记录，包含以下表：
- `groups` - 群聊信息
- `members` - 群成员信息
- `messages` - 群消息记录

数据库文件：`qq_chat.db`

### 向量数据库

聊天记录查询使用Faiss向量数据库：
- 索引文件：`qq_bot_vector_space.index`
- 数据库文件：`qq_bot_message_data.db`

## 配置文件

### config.yaml

```yaml
persona: "机器人人设描述"
```

### .env

```env
API_URL=你的API地址
API_KEY=你的API密钥
LOW_COST_API_URL=低成本API地址
LOW_COST_API_KEY=低成本API密钥
MODEL=AI模型名称
LOW_COST_MODEL=低成本模型名称
IMAGE_MODEL=图片生成模型
SEARCH_KEY=搜索API密钥
BOT_QQ=机器人QQ号
ROOT_QQ=管理员QQ号
SALT=随机盐值
```

## 注意事项

1. 首次运行需要完成配置向导
2. 确保API密钥正确且有足够的配额
3. 管理员QQ号用于管理问答系统和群聊绑定
4. 机器人会自动过滤群ID为1的消息
5. QQ号在数据库中使用哈希值存储，保护隐私

## 许可证

请查看 [LICENSE](LICENSE) 文件了解详细信息。

## 贡献

欢迎提交Issue和Pull Request！
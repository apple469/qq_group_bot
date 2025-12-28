import random
import faiss
import numpy as np
import os
import sqlite3
import onnxruntime
import time
from tokenizers import BertWordPieceTokenizer
from ncatbot.core import GroupMessage

# 插件信息
PLUGIN_NAME = "聊天记录查询插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "这是一个聊天记录查询插件"

# 插件状态
plugin_enabled = True

# 插件优先级 (数值越小优先级越高，默认100)
PRIORITY = 2

HELP = """聊天记录查询命令:
/query 查询词 - 查询聊天记录"""

# ================= ONNX 模型封装 (保留并微调) =================

class ONNXSentenceEncoder:
    def __init__(self, model_path, vocab_path, max_seq_len=128):
        # 强制使用 CPU 提高兼容性
        self.session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.tokenizer = BertWordPieceTokenizer(vocab=vocab_path, lowercase=True)
        self.max_seq_len = max_seq_len
        self.input_names = [inp.name for inp in self.session.get_inputs()]

    def _tokenize(self, text):
        encoded = self.tokenizer.encode(text)
        ids = encoded.ids[:self.max_seq_len]
        mask = encoded.attention_mask[:self.max_seq_len]
        p_len = self.max_seq_len - len(ids)
        return np.array([ids + [0]*p_len], dtype=np.int64), \
               np.array([mask + [0]*p_len], dtype=np.int64)

    def encode(self, texts):
        if isinstance(texts, str): texts = [texts]
        embeddings = []
        for text in texts:
            input_ids, attention_mask = self._tokenize(text)
            inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
            # 兼容你的模型输入名
            if "token_type_ids" in self.input_names:
                inputs["token_type_ids"] = np.zeros_like(input_ids)
            
            outputs = self.session.run(None, inputs)
            last_hidden_state = outputs[0]
            # 池化操作
            mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(float)
            sentence_embedding = np.sum(last_hidden_state * mask_expanded, axis=1) / np.clip(mask_expanded.sum(axis=1), 1e-9, None)
            # 归一化
            norm = np.linalg.norm(sentence_embedding, axis=1, keepdims=True)
            embeddings.append((sentence_embedding / norm)[0])
        return np.array(embeddings).astype('float32')

# ================= 2. 数据库逻辑 (路径优化版) =================

# --- 配置路径 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 定位到上一级目录
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
ONNX_DIR = os.path.join(SCRIPT_DIR, "onnx_models")

# 为文件增加标识性前缀，防止冲突，并存储在上一级目录
FAISS_INDEX_PATH = os.path.join(PARENT_DIR, "qq_bot_vector_space.index")
SQLITE_DB_PATH = os.path.join(PARENT_DIR, "qq_bot_message_data.db")

# 初始化模型
encoder = ONNXSentenceEncoder(
    os.path.join(ONNX_DIR, "model.onnx"), 
    os.path.join(ONNX_DIR, "vocab.txt")
)

# 自动获取模型维度
MODEL_DIM = encoder.encode("test").shape[1]

def add_message(group_id, text):
    """
    接收消息并存入数据库 (数据存储在上一级目录)
    """
    # 1. 向量化
    vector = encoder.encode(text)
    
    # 2. 存入 Faiss
    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)
    else:
        index = faiss.IndexFlatL2(MODEL_DIM)
    
    row_id = index.ntotal 
    index.add(vector)
    faiss.write_index(index, FAISS_INDEX_PATH)
    
    # 3. 存入 SQLite
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    # 增加表名标识度
    cursor.execute("CREATE TABLE IF NOT EXISTS group_msg_records (row_id INTEGER, group_id TEXT, content TEXT)")
    cursor.execute("INSERT INTO group_msg_records VALUES (?, ?, ?)", (row_id, str(group_id), text))
    conn.commit()
    conn.close()

def search_message(group_id, query_text, top_k=5):
    """
    在指定群聊内搜索最相似的消息
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        return []

    # 1. 查询向量化
    query_vector = encoder.encode(query_text)
    
    # 2. Faiss 检索
    index = faiss.read_index(FAISS_INDEX_PATH)
    distances, indices = index.search(query_vector, 100) 
    
    # 3. SQLite 过滤群号
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    final_results = []
    for idx in indices[0]:
        if idx == -1: continue
        # 使用更新后的表名查询
        cursor.execute("SELECT content FROM group_msg_records WHERE row_id = ? AND group_id = ?", (int(idx), str(group_id)))
        row = cursor.fetchone()
        if row:
            final_results.append(row[0])
            if len(final_results) >= top_k:
                break
                
    conn.close()
    return final_results

def handle_message(msg: GroupMessage):
    """
    处理群消息
    返回值格式: (回复内容, 是否@发送者, 图片路径)
    如果不需要回复，返回 None
    """
    if not plugin_enabled:
        return None
    
    raw_msg = msg.raw_message.strip()
    if "/query" in raw_msg:
        time.sleep(random.uniform(1, 3))
        query_text = raw_msg.replace("/query", "").strip()
        add_message(msg.group_id, raw_msg)
        if query_text:
            results = search_message(msg.group_id, query_text)
            if results:
                reply = "检索内容:\n" + "\n".join([f"{i+1}.{t}" for i, t in enumerate(results)])
                return reply, True, None
            else:
                return "没有找到相关消息", True, None
        else:
            return "请输入查询内容", True, None
    add_message(msg.group_id, raw_msg)
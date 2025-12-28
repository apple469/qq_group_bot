import onnxruntime
import numpy as np
from tokenizers import BertWordPieceTokenizer
import os


# --- Configuration ---
# Get the absolute path of the script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Directory for ONNX model and tokenizer files
ONNX_MODEL_DIR = os.path.join(SCRIPT_DIR, "onnx_models")
ONNX_MODEL_PATH = os.path.join(ONNX_MODEL_DIR, "model.onnx")
TOKENIZER_VOCAB_PATH = os.path.join(ONNX_MODEL_DIR, "vocab.txt")


class ONNXSentenceEncoder:
    """ONNX Model and Tokenizer Wrapper Class"""
    def __init__(self, model_path, vocab_path, max_seq_len=128):
        """
        Initializes ONNX model and tokenizer
        :param model_path: Path to the ONNX model file
        :param vocab_path: Path to the vocabulary file
        :param max_seq_len: Maximum sequence length
        """
        self.session = onnxruntime.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.tokenizer = BertWordPieceTokenizer(
            vocab=vocab_path,
            lowercase=True
        )
        self.max_seq_len = max_seq_len
        self.input_names = [inp.name for inp in self.session.get_inputs()]

    def _tokenize(self, text):
        """Tokenizes the input text"""
        encoded = self.tokenizer.encode(text)
        input_ids = encoded.ids
        attention_mask = encoded.attention_mask
        token_type_ids = encoded.type_ids

        # Truncate or pad to max_seq_len
        if len(input_ids) > self.max_seq_len:
            input_ids = input_ids[:self.max_seq_len]
            attention_mask = attention_mask[:self.max_seq_len]
            token_type_ids = token_type_ids[:self.max_seq_len]
        else:
            padding_len = self.max_seq_len - len(input_ids)
            input_ids = input_ids + [0] * padding_len
            attention_mask = attention_mask + [0] * padding_len
            token_type_ids = token_type_ids + [0] * padding_len

        return np.array([input_ids], dtype=np.int64), \
               np.array([attention_mask], dtype=np.int64), \
               np.array([token_type_ids], dtype=np.int64)

    def encode(self, texts):
        """Encodes a list of texts into embedding vectors"""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            input_ids, attention_mask, token_type_ids = self._tokenize(text)
            
            # Prepare input dictionary, ensuring it matches ONNX model input names
            inputs = {}
            if "input_ids" in self.input_names:
                inputs["input_ids"] = input_ids
            if "attention_mask" in self.input_names:
                inputs["attention_mask"] = attention_mask
            if "token_type_ids" in self.input_names:
                 inputs["token_type_ids"] = token_type_ids

            outputs = self.session.run(None, inputs)
            
            # Sentence-BERT typically outputs last_hidden_state, then pools
            last_hidden_state = outputs[0]
            
            # Average pooling, considering attention_mask
            input_mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(float)
            sum_embeddings = np.sum(last_hidden_state * input_mask_expanded, axis=1)
            sum_mask = np.clip(input_mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
            sentence_embedding = sum_embeddings / sum_mask
            
            # Normalize embedding vectors (L2 norm)
            sentence_embedding = sentence_embedding / np.linalg.norm(sentence_embedding, axis=1, keepdims=True)
            embeddings.append(sentence_embedding[0])
        
        return np.array(embeddings)


# --- Core Optimization: Global model initialization (loaded only once) ---
# Model and Tokenizer are loaded at program startup, subsequent classifications reuse them
try:
    global_encoder = ONNXSentenceEncoder(ONNX_MODEL_PATH, TOKENIZER_VOCAB_PATH)
    print("Classification model initialized successfully")
except Exception as e:
    print(f"Model initialization failed: {str(e)}")
    print("Please check if model.onnx and vocab.txt exist in the onnx_models directory")
    raise RuntimeError(f"ONNX model initialization failed: {str(e)}") from e


def cosine_similarity(vec1, vec2):
    """
    Calculates the cosine similarity between two vectors
    :param vec1: Vector 1
    :param vec2: Vector 2
    :return: Cosine similarity
    """
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# Add cache to store prototype sentence embeddings
from collections import OrderedDict
# Use OrderedDict to maintain cache order and limit max size to 100
prototype_embeddings_cache = OrderedDict()
MAX_CACHE_SIZE = 100

def classify_text(text, prototypes):
    """
    Classifies text based on prototype sentences (reusing global model instance)
    :param text: Text to be classified
    :param prototypes: List of prototype sentences, format: [{"text": "sample text", "label": "label"}, ...]
    :return: (best label, confidence)
    """
    # Check if model is initialized
    if 'global_encoder' not in globals():
        raise RuntimeError("ONNX model not initialized. Please check if model files exist in onnx_models directory")
    
    # Directly use the globally initialized encoder, no need to recreate
    encoder = global_encoder
    
    # Encode text to be classified
    text_embedding = encoder.encode(text)[0]
    
    # Group prototype sentences by label
    label_groups = {}
    for prototype in prototypes:
        label = prototype["label"]
        if label not in label_groups:
            label_groups[label] = []
        label_groups[label].append(prototype["text"])
    
    # Calculate average similarity for each label group
    label_similarities = {}
    for label, texts in label_groups.items():
        # Use cache to avoid recomputing prototype sentence embeddings
        cache_key = tuple(texts)  # Use text tuple as cache key
        if cache_key in prototype_embeddings_cache:
            # When accessing an existing cache item, move it to the end (most recently used)
            embeddings = prototype_embeddings_cache.pop(cache_key)
            prototype_embeddings_cache[cache_key] = embeddings
        else:
            embeddings = encoder.encode(texts)
            # Check cache size, remove oldest entry if limit exceeded
            if len(prototype_embeddings_cache) >= MAX_CACHE_SIZE:
                prototype_embeddings_cache.popitem(last=False)
            prototype_embeddings_cache[cache_key] = embeddings  # Cache result
            
        similarities = [cosine_similarity(text_embedding, emb) for emb in embeddings]
        label_similarities[label] = np.mean(similarities)
    
    # Return the label with the highest average similarity and confidence
    if not label_similarities:
        return None, 0.0
    
    best_label = max(label_similarities, key=label_similarities.get)
    confidence = label_similarities[best_label]
    
    return best_label, confidence
from jieba_classification import get_answer
import json

# 延迟导入ONNX分类模块，避免初始化失败
onnx_classification_available = False
try:
    from onnx_classification import classify_text
    onnx_classification_available = True
except Exception as e:
    print(f"ONNX classification module not available: {e}")
    onnx_classification_available = False

def classification(text: str, qa_dict: dict):
    """
    Hybrid classification system: first try ONNX classification, fallback to jieba classification
    :param text: Input text to classify
    :param qa_dict: Dictionary containing q-a pairs in format [{"q": "question", "a": "answer"}, ...]
    :return: best_match_q, best_match_a, score
    """
    # Try ONNX classification first
    try:
        # Extract only q parts from qa_dict and convert to prototype format
        prototypes = []
        for item in qa_dict:
            q_text = item["q"]
            prototypes.append({"text": q_text, "label": q_text})
        
        # Classify using ONNX model
        best_label, score = classify_text(text, prototypes)
        
        # Find corresponding answer in original qa_dict
        for item in qa_dict:
            if item["q"] == best_label:
                best_match_q = item["q"]
                best_match_a = item["a"]
                max_score = score
                return best_match_q, best_match_a, max_score
        
        # If no match found, fallback to jieba
        return get_answer(text, qa_dict)
    
    except Exception as e:
        # If ONNX classification fails, use jieba classification
        print(f"ONNX classification failed: {e}, falling back to jieba classification")
        return get_answer(text, qa_dict)
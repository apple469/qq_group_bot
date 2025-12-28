import jieba

def get_answer(question, qa_json):
    """
    智能问答核心函数
    :param question: 用户输入的问题字符串
    :param qa_json: 包含 {"q": "", "a": ""} 的列表
    :return: 最相似的问题, 对应的回答, 相似概率
    """
    # 1. 如果JSON是空的，返回空数据防止报错
    if not qa_json:
        return "无数据", "知识库为空", 0.0

    # 2. 定义停用词（过滤掉没意义的词，提高准确率）
    stopwords = {'的', '了', '是', '在', '我', '有', '和', '去', '吗', '怎么', '如何', '什么', '个', '啊', '呀', '呢', '吧', '就', '也', '都', '不', '没', '没有', '很', '非常', '特别', '太', '最', '更', '比较', '非常', '非常'}
    
    # 对用户输入进行分词，并转为集合
    user_words = set(jieba.lcut(question))
    # 过滤停用词和单字词
    user_words = {w for w in user_words if w not in stopwords and len(w) > 1 and w.strip()}

    # 3. 初始化最佳匹配
    # 默认选第1条作为保底，分数设为 -1 确保只要有计算就会更新
    best_match_q = qa_json[0]['q']
    best_match_a = qa_json[0]['a']
    max_score = -1.0 

    # 4. 遍历整个JSON列表
    for item in qa_json:
        db_q = item['q']
        db_a = item['a']
        
        # 对数据库里的问题分词
        db_words = set(jieba.lcut(db_q))
        db_words = {w for w in db_words if w not in stopwords and len(w) > 1 and w.strip()}

        # === 核心算法：改进的相似度计算 ===
        # 如果用户输入或数据库问题过滤后为空，使用原始文本进行简单匹配
        if not user_words or not db_words:
            # 使用简单的字符串包含匹配作为保底
            if question.strip() in db_q or db_q.strip() in question:
                score = 0.5
            else:
                score = 0.0
        else:
            # Jaccard 相似度
            intersection = user_words & db_words # 交集
            union = user_words | db_words        # 并集
            
            if not union:
                score = 0.0
            else:
                score = len(intersection) / len(union)
                
                # 增加权重：如果关键词完全匹配，提高分数
                if len(intersection) == len(user_words) and len(user_words) > 0:
                    score = min(score + 0.3, 1.0)

        # 5. 更新逻辑：只要当前分数比之前的最高分高，就替换
        # 注意：这里没有 if score > 0，所以即使是0分也会参与比较（或者保留默认值）
        if score > max_score:
            max_score = score
            best_match_q = db_q
            best_match_a = db_a

    # 6. 如果循环结束最高分还是-1或0（说明完全没匹配上），
    # 此时 best_match_q 依然是第1条数据，保证了"绝对输出"
    if max_score < 0: 
        max_score = 0.0
    
    # 7. 如果分数仍然为0，尝试使用更宽松的匹配策略
    if max_score == 0.0:
        # 使用字符级别的相似度作为最后的手段
        for item in qa_json:
            db_q = item['q']
            db_a = item['a']
            
            # 计算字符级别的相似度
            from difflib import SequenceMatcher
            score = SequenceMatcher(None, question.lower(), db_q.lower()).ratio()
            
            if score > max_score:
                max_score = score
                best_match_q = db_q
                best_match_a = db_a

    return best_match_q, best_match_a, max_score
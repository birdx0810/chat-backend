# Import Jieba TextRank
from jieba import analyse, posseg

with open('./QA/QA.txt' ,'r') as f:
    # TODO: 
    # Create Q dictionary
    # Tokenize Q (Sentences) using Jieba
    # Retrieve Top-K words from Question (K=3)
    # Create dictionary for mapping keywords to answer
    # {(kw_1, kw_2, kw_3): 'Answer'}
    lines = f.readlines()
    Q = {}
    count = 1 
    for idx in range(len(lines)):
        if idx % 2 is 0:
            Q[count] = lines[idx].strip("'").strip("\n")
            count += 1
    
    qa_list = []
    for idx in range(len(lines)):
        if idx % 2 is 0:
            qa_list.append(lines[idx])
        elif idx % 2 is not 0:
            qa_list[idx-1].append(lines[idx])

    print(qa_list)

    keywords = []
    for question in Q.values():
        # Get POS embeddings
        # word_POS = posseg.cut(question)
        # for word, flag in word_POS:
        #     print(f'| {word} | {flag} |')
        # print(f'*' * 10)
        
        # Get top-4 keywords
        words = analyse.extract_tags(question, topK=4, withWeight=True, allowPOS=())
        key = tuple([word[0] for word in words])
        keywords.append(key)
    
    print(keywords)
    # Output: [('手環', '出現', 'OFF', '畫面'), ('手環', '戴著', '碰水', '洗澡'), ('怎麼樣', '藍芽', '斷線', '怎麼'), ('偶爾', '拆掉', '把手', '可以'), ('怎麼', '手環', '還有', '沒有電'), ('溫度', '什麼', '手環', '顯示')]
    keywords = [
        ('畫面', 'ON', 'OFF'),
        ('碰水', '洗澡', '游泳'), 
        ('藍牙', '藍芽', '斷線', '連接'), 
        ('偶爾', '不穿', '拆掉'),
        ('沒有電', '電池'),
        ('溫度', '差')
    ]

    # QA Dictionary
    QA = {}
    for kw_tuple in keywords:
        for idx in range(len(lines)):
            # if idx % 2 is 
            if idx % 2 is not 0:
                QA[kw_tuple] = lines[idx].strip("'").strip("\n")

    # print(QA)
# -*- coding: UTF-8 -*-
'''
Some utilities for QA event
'''
# Import required modules
import pickle

# Initialize BERT-as-service encoder
from bert_serving.client import BertClient
bc = BertClient(ip='140.116.245.101')

# QA and keyword triplet
qa_dict = {
    ('畫面', 'ON', 'OFF'): [
        "手環如果出現ON/OFF的畫面怎麼辦？",
        "若手環畫面出現ON/OFF，請將選項選至ON並長按功能鍵直到恢復時間的畫面"
    ],
    ('碰水', '洗澡', '游泳'): [
        "手環是否可以戴著洗澡或碰水？",
        "若是一般洗手是可以戴著手環不用拔除，若是洗澡或是游泳等會長時間浸泡或碰觸水的情況，為了手環的穩定性，建議將手環拔除並與手機放置同一位置，避免藍芽斷線"
    ],
    ('藍牙', '藍芽', '斷線', '連接'): [
        "怎麼樣知道藍芽斷線了？怎麼處理？",
        "若手環時間畫面右上角沒有藍芽的圖示，則代表沒有與藍芽連線，請將手機收案app打開即可自動連線"
    ],
    ('偶爾', '不穿', '拆掉'): [
        "可以偶爾把手環拆掉嗎？",
        "原則上會希望除了洗澡之外的時間都將手環佩戴著，因為連續的體溫監測才能更及時的掌握您的體溫狀況及變化。若偶爾想要將手環拆下稍作休息，請將手環與手機放在同一位置以保持藍芽連線"
    ],
    ('沒有電', '電池'): [
        "怎麼知道手環還有沒有電？",
        "手機收案app的畫面有一個「電量」，此即是手環的電量。若手環沒電會自動關機，此時請將手環拔除充電"
    ],
    ('溫度', '差'): [
        "為什麼手環顯示的溫度跟平常量的溫度差這麼多？",
        "手環上所顯示的是體表溫度，與耳溫槍所量的核心溫度有差異是正常的"
    ]
}

# Encoded question embeddings
with open('QA/q_emb.pickle', 'rb') as f:
    q_embs = pickle.load(f)

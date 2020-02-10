# -*- coding: UTF-8 -*-
'''
The script for responding to user according to status
- Registration
- QA
- Event High Temperature
- TODO: Event Push News
'''
# Import required modules
from linebot import (
        LineBotApi, WebhookHandler

)
from linebot.exceptions import (
        InvalidSignatureError

)
from linebot.models import (
        MessageEvent, TextMessage, TextSendMessage, StickerMessage
)

from sklearn.metrics.pairwise import cosine_similarity

import pickle
import utilities
import templates as t

##############################
# Application & variable initialization
##############################
# Is development or production
is_development=False
if is_development:
    # Channel Access Token
    line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740')
else: # Is production
    # Channel Access Token
    line_bot_api = LineBotApi('8kCwJkbO0Ps6ftZfFSJmBjmc+VrpNB0x4lMn+pEUNV4t306quG5AQKUnPGHNqw8sYFIQL7086mkTQdQj4iC/zUgwKRZMPHCKaxc5N1buQSY+rzGohXfiwldZbkTQQj/sDK7tv8URS5C9sx7kwkfQRAdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('5e438935670953f040569105b3d527e1')


def registration_resp(event, status, session):
    '''
    Gets the status of user and replies according to user's registration status
    '''
    # Initialize variables
    userid = event.source.user_id

    err_msg = {
        'r0': "請輸入您的姓名（e.g. 大鳥陳）",
        'r1': "請輸入您的生日（年年年年月月日日）"
    }

    if status == 'r0':
        msg = "初次見面，請輸入您的姓名"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 'r1':
        msg = "請輸入您的生日（年年年年月月日日）"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 'r2':
        msg = "註冊成功啦"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.status[userid]['sess_status'] = session.init_state
    elif status == 'r_err':
        status = session.status[userid]['sess_status']
        msg = "不好意思，您的輸入有所異常。\n" + err_msg[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def qa_resp(event, session):
    '''
    Reply user according to status
    '''
    userid = event.source.user_id
    text = event.message.text
    status = session.status[userid]['sess_status']

    # Initialize BERT-as-service encoder
    from bert_serving.client import BertClient
    bc = BertClient(ip='140.116.245.101')

    if status == 'qa0':
        msg = "你好，請問我可以如何幫你？\n(小弟目前還在學習中，請多多指教～"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

    elif status == 'qa1':
        found = False
        # Keyword matching
        for keys, values in t.qa_dict.items():
            for keyword in keys:
                if keyword in text.lower():
                    found = True
                    msg = f"你想問的問題可能是:\n{repr(values[0])}\n\n我們的回答是:{repr(values[1])}"
        # Calculate cosine similarity if no keywords found in sentence
        if found == False:
            query = bc.encode([text])
            similarity = []
            for idx in range(len(t.question_embeddings)):
                query = query.transpose()
                sim = cosine_similarity(query, t.question_embeddings[idx].resize((768,1)))
                similarity.append(sim)
            max_idx, _ = max((i,v)for i,v in enumerate(similarity))
            msg = f"你想問的問題可能是:\n{repr(values[0])}\n\n我們的回答是:\n{repr(values[1])}"
        # Reply answer
        is_correct = t.yn_template('請問是否是你想要問的問題嗎？')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, is_correct)

    elif status == 'qa1_err':
        msg = '不好意思，我不明白你的意思…'
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        pass

    elif status == 'qa2_t':
        msg = "感謝你的回饋。很高興可以幫到你～"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.switch_status(userid, None)

    elif status == 'qa2_f':
        qa_labels = t.qa_labels()
        line_bot_api.reply_message(
            event.reply_token,
            qa_labels
        )

    elif status == 'qa3':
        for keys, values in t.qa_dict.items():
            if text == values[0]:
                msg = f"你想問的問題可能是:\n{repr(values[0])}\n\n我們的回答是:\n{repr(values[1])}\n\n感謝您的回饋。"
                break
            else:
                msg = f"不好意思，目前沒辦法回應你的需求。我們會再改進～"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.switch_status(userid, None)

def high_temp_resp(userid, session, event=None):
    '''
    High temperature event responder
    '''
    # Initialize variables
    if event is not None:
        text = event.message.text
    status = session.status[userid]['sess_status']

    # Scene 1:
    # Status 0 - API triggered
    if status == 's1s0':
        # Detected user high temperature, ask patient well being
        msg = "您好，手環資料顯示您的體溫似乎比較高，請問您有不舒服的情形嗎？"
        ask_status = t.tf_template(msg)
        line_bot_api.push_message(userid, ask_status)

    # Status 1 - Ask if feeling sick
    elif status == 's1s1':
        # If true (not feeling well), ask for symptoms
        symptom_template = t.symptoms_template()
        line_bot_api.reply_message(
            event.reply_token,
            symptom_template
        )
    elif status == 's1f1':
        # If false (feeling ok), reply msg
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.switch_status(userid, None)

    # Status 2 - Ask for symptoms
    elif status == 's1d0' or status == 's1d1':
        # If '皮膚出疹' & '眼窩痛' detected
        msg = t.symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(t.dengue_info()))
        ask_clinic = t.yn_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")
        line_bot_api.push_message(userid, ask_clinic)

    elif status == 's1d2' or status == 's1d3' or status == 's1d4':
        # If '喉嚨痛' & '咳嗽' & '咳血痰' detected
        msg = t.symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(t.flu_info()))
        ask_clinic = t.yn_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")
        line_bot_api.push_message(userid, ask_clinic)
    elif status == 's1d5':
        # If '肌肉酸痛' detected
        msg = t.symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(t.flu_info()+"\n"+t.dengue_info()))
        ask_clinic = t.yn_template("為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？")
        line_bot_api.push_message(userid, ask_clinic)
    elif status == 's1df':
        # If others
        msg = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.switch_status(userid, None)

    # Status 3: Ask for location
    elif status == 's1s2':
        # If replies to ask for nearby clinic
        msg = "請將您目前的位置傳送給我～"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 's1f2':
        # If doesn't need nearby clinic info
        msg = "請持續密切注意您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，若有任何身體不適仍建議您至醫療院所就醫！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        session.switch_status(userid, None)

    # Status 4: End scenario
    elif status == 's1s3':
        # Send clinic info and ask to go see doctor ASAP
        msg =  "請盡快至您熟悉方便的醫療院所就醫。"
        clinic = t.get_nearby_clinic(text)
        line_bot_api.reply_message(
            event.reply_token,
            clinic
        )
        line_bot_api.push_message(userid, TextSendMessage(text=msg))
        session.switch_status(userid, None)
        pass


def push_news_resp(event, session):
    # TODO: Push medical related news to all users
    # Initialize variables
    userid = event.source.user_id
    status = session.status[userid]['sess_status']

    if status == 's2s0':
        #TODO: push news and ask if not feeling well?
        # 1.1 Get news and template message
        news = get_news()
        ask_location = t.tf_template("請問您有在上述的區域內嗎？")
        # 1.2 Push news and ask if in location
        line_bot_api.push_message(userid, news)
        line_bot_api.push_message(userid, ask_location)
        pass
    elif status == 's2s1':
        # 2.1 If in location with case
        msg = "因為您所在的地區有確診案例，請問您有不舒服的狀況嗎？"
        line_bot_api.reply_message(
            event.reply_token,

        )
        pass
    elif status == 's2f1':
        # 2.2 If not in the location (end)
        msg = "您所在的位置非疫情區，因此不用太過緊張。若有最新消息將會立即更新讓您第一時間了解！"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 's2s2':
        # 2.3 Doctor function
        msg = "把我當成一個醫生，說說您現在哪邊不舒服？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    pass

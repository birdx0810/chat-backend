# -*- coding: UTF-8 -*-
'''
Templates for replying messages, reduce the dirtiness of the responder
'''
from linebot.models import *

import pickle
import google_map as gmaps

##############################
# Multi purpose templates
##############################

# True or false button template
def tf_template(msg):
    tf_template = TemplateSendMessage(
        alt_text=msg,
        template=ButtonsTemplate(
            title=msg,
            text=" ",
            actions=[
                MessageTemplateAction(
                    label='有',
                    text='有'
                ),
                MessageTemplateAction(
                    label='沒有',
                    text='沒有'
                )
            ]
        )
    )
    return tf_template

def yn_template(msg):
    tf_template = TemplateSendMessage(
        alt_text=msg,
        template=ButtonsTemplate(
            title=msg,
            text=" ",
            actions=[
                MessageTemplateAction(
                    label='是',
                    text='是'
                ),
                MessageTemplateAction(
                    label='不是',
                    text='不是'
                )
            ]
        )
    )
    return tf_template

##############################
# Task specific templates
##############################

# QA templates
qa_dict = {
    ('畫面', 'on', 'off', '螢幕'): [
        "手環如果出現ON/OFF的畫面怎麼辦？",
        "若手環畫面出現ON/OFF，請將選項選至ON並長按功能鍵直到恢復時間的畫面"
    ],
    ('碰水', '洗澡', '游泳'): [
        "手環是否可以戴著洗澡或碰水？",
        "若是一般洗手是可以戴著手環不用拔除，若是洗澡或是游泳等會長時間浸泡或碰觸水的情況，為了手環的穩定性，建議將手環拔除並與手機放置同一位置，避免藍芽斷線"
    ],
    ('藍牙', '藍芽', '斷線', '連接', '連線'): [
        "怎麼樣知道藍芽斷線了？怎麼處理？",
        "若手環時間畫面右上角沒有藍芽的圖示，則代表沒有與藍芽連線，請將手機收案app打開即可自動連線"
    ],
    ('偶爾', '不穿', '拆掉'): [
        "可以偶爾把手環拆掉嗎？",
        "原則上會希望除了洗澡之外的時間都將手環佩戴著，因為連續的體溫監測才能更及時的掌握您的體溫狀況及變化。若偶爾想要將手環拆下稍作休息，請將手環與手機放在同一位置以保持藍芽連線"
    ],
    ('沒有電', '電池', '沒電', '電'): [
        "怎麼知道手環還有沒有電？",
        "手機收案app的畫面有一個「電量」，此即是手環的電量。若手環沒電會自動關機，此時請將手環拔除充電"
    ],
    ('體溫', '溫度', '差'): [
        "為什麼手環顯示的溫度跟平常量的溫度差這麼多？",
        "手環上所顯示的是體表溫度，與耳溫槍所量的核心溫度有差異是正常的"
    ]
}

# Get question embeddings
with open('QA/q_emb.pickle', 'rb') as f:
    question_embeddings = pickle.load(f)

def qa_labels():
    qa_labels = TemplateSendMessage(
        alt_text="不好意思，請問以下有您想要問的問題嗎？\n若沒有，請輸入其他。",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title="不好意思，請問以下有您想要問的問題嗎？若沒有，請輸入其他。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label='手環 ON/OFF 畫面',
                            text=qa_dict[('畫面', 'on', 'off', '螢幕')][0]
                        ),
                        MessageAction(
                            label='手環是否防水',
                            text=qa_dict[('碰水', '洗澡', '游泳')][0],
                        ),
                        MessageAction(
                            label='藍牙斷線',
                            text=qa_dict[('藍牙', '藍芽', '斷線', '連接', '連線')][0]
                        )
                    ]
                ),
                CarouselColumn(
                    title="不好意思，請問以下有您想要問的問題嗎？若沒有，請輸入其他。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label='偶爾不穿手環',
                            text=qa_dict[('偶爾', '不穿', '拆掉')][0]
                        ),
                        MessageAction(
                            label='手環電池',
                            text=qa_dict[('沒有電', '電池', '沒電', '電')][0]
                        ),
                        MessageAction(
                            label='手環顯示有溫差',
                            text=qa_dict[('體溫', '溫度', '差')][0]
                        )
                    ]
                )
                
            ]
        )
    )
    return qa_labels

# Scenario 1
symptom_reply = {
    's1d0': "體溫異常升高，加上皮膚出疹為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
    's1d1': "體溫異常升高，加上眼窩痛為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
    's1d2': "體溫異常升高，加上喉嚨痛為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
    's1d3': "體溫異常升高，加上咳嗽為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
    's1d4': "體溫異常升高，加上咳血痰為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
    's1d5': "體溫異常升高，加上肌肉酸痛為疑登革熱/流感 情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
}

def flu_reply():
    reply = [
        "體溫異常升高加上咳血痰疑似為流感情形，但這只是初步懷疑請不用太過驚慌，以下為流感相關資訊提供給您",
        "https://www.cdc.gov.tw/Disease/SubIndex/x7jzGIMMuIeuLM5izvwg_g",
        "為了您的安全健康，建議儘速至醫療院所就醫",
        "請問是否需要提供您附近醫療院所的資訊"
    ]
    return "\n".join(reply)

def dengue_reply():
    reply = [
        "體溫異常升高加上肌肉/骨頭痠痛疑似為流感/登革熱情形，但這只是初步懷疑請不用太過驚慌，以下相關資訊提供給您",
        "https://www.cdc.gov.tw/Disease/SubIndex/x7jzGIMMuIeuLM5izvwg_g",
        "https://www.cdc.gov.tw/Disease/SubIndex/WYbKe3aE7LiY5gb-eA8PBw",
        "為了您的安全健康，建議儘速至醫療院所就醫",
        "請問是否需要提供您附近醫療院所的資訊"
    ]
    return "\n".join(reply)

def flu_info():
    info = ["流感併發重症", "https://www.cdc.gov.tw/Disease/SubIndex/x7jzGIMMuIeuLM5izvwg_g",
            "新型A型流感", "https://www.cdc.gov.tw/Disease/SubIndex/8Yt_gKjz-BEr3QJZGOa0fQ"]
    info = "\n".join(info)
    return info

def dengue_info():
    info = ["登革熱", "https://www.cdc.gov.tw/Disease/SubIndex/WYbKe3aE7LiY5gb-eA8PBw"]
    info = "\n".join(info)
    return info

def symptoms_template():
    symptom = ['皮膚出疹','眼窩痛','喉嚨痛','咳嗽','咳血痰','肌肉酸痛']
    symptoms = TemplateSendMessage(
        alt_text="請問您是否有以下的症狀？",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title="請問您是否有以下的症狀？若無，請輸入其它。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=symptom[0],
                            text=symptom[0]
                        ),
                        MessageAction(
                            label=symptom[1],
                            text=symptom[1],
                        ),
                        MessageAction(
                            label=symptom[2],
                            text=symptom[2]
                        )
                    ]
                ),
                CarouselColumn(
                    title="請問您是否有以下的症狀？若無，請輸入其它。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=symptom[3],
                            text=symptom[3]
                        ),
                        MessageAction(
                            label=symptom[4],
                            text=symptom[4],
                        ),
                        MessageAction(
                            label=symptom[5],
                            text=symptom[5]
                        )
                    ]
                )
            ]
        )
    )
    return symptoms

def get_nearby_clinic(address, keyword='內科 耳鼻喉科'):
    # try:
    nearby = gmaps.get_address(address, keyword)

    # send the nearby clinic to user
    if len(nearby) >= 1:
        for pos in nearby:
            # use url parser to extract latitude and longtitude
            lat, long = urllib.parse.parse_qs(pos[2])["query"][0].split(",")

            message = LocationSendMessage(
                title="離您最近的診所是：" + pos[0],
                address=pos[1],
                latitude=str(lat),
                longitude=str(long))
            break  # now only push the first result
        pass
    else:
        message = TextSendMessage("很抱歉，您附近並沒有相關的診所。")
    # except:
    #     message = TextSendMessage("很抱歉，您附近並沒有相關的診所。")
    return message
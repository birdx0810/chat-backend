# -*- coding: UTF-8 -*-
"""
Templates for replying messages, reduce the dirtiness of the responder
"""
import pickle
import traceback

from linebot.models import (
    LocationSendMessage, TemplateSendMessage, MessageAction,
    CarouselColumn, CarouselTemplate, ButtonsTemplate, MessageTemplateAction
)
import googlemaps

import environment

gmaps = googlemaps.Client(key=environment.get_maps_key())

##############################
# System templates
##############################

system_sticker_message = "[[使用者傳送了貼圖]]"

system_image_message = "[[使用者傳送了圖片]]"

system_video_message = "[[使用者傳送了影片]]"

system_audio_message = "[[使用者傳送了語音訊息]]"

system_wait_admin = "感謝您使用 HEARThermo 2.0。\n我們已收到您的訊息，客服會儘快與您聯繫。\n提醒您可以使用選單或輸入 /qa 進行簡單問答。"

##############################
# Multi purpose templates
##############################

# True or false button template

T = ["有", "要", "有喔", "有阿", "好", "好喔", "好阿", "可",
     "可以", "可以阿", "Yes", "有一點", "一點", "一點點", "是"]
F = ["沒有", "不要", "不", "沒", "No", "無", "否",
     "不用", "曾經有", "曾經", "以前有", "以前", "不是"]


def tf_template(msg):
    return TemplateSendMessage(
        alt_text=msg,
        template=ButtonsTemplate(
            title=msg,
            text=" ",
            actions=[
                MessageTemplateAction(
                    label="有",
                    text="有"
                ),
                MessageTemplateAction(
                    label="沒有",
                    text="沒有"
                )
            ]
        )
    )


def yn_template(msg):
    return TemplateSendMessage(
        alt_text=msg,
        template=ButtonsTemplate(
            title=msg,
            text=" ",
            actions=[
                MessageTemplateAction(
                    label="是",
                    text="是"
                ),
                MessageTemplateAction(
                    label="不是",
                    text="不是"
                )
            ]
        )
    )


def want_template(msg):
    return TemplateSendMessage(
        alt_text=msg,
        template=ButtonsTemplate(
            title=msg,
            text=" ",
            actions=[
                MessageTemplateAction(
                    label="要",
                    text="要"
                ),
                MessageTemplateAction(
                    label="不要",
                    text="不要"
                )
            ]
        )
    )

##############################
# Registration Template
##############################


registration_err_msg = {
    "r0": "請輸入您的中文姓名（e.g. 王小明）",
    "r1": "請輸入您的生日（年年年年月月日日）"
}

registration_greeting = "初次見面，請輸入您的中文姓名（e.g. 王小明）"

registration_birthday = "請輸入您的生日（年年年年月月日日）"

registration_successful = "註冊成功啦"


def registration_err(status="r0"):
    return "不好意思，您的輸入不符格式。\n" + registration_err_msg[status]


##############################
# QA Template
##############################

# QA templates
qa_list = [
    {
        "label": "手環 ON/OFF 畫面",
        "keywords": ["畫面", "on", "off", "螢幕"],
        "question": "手環如果出現 ON/OFF 的畫面怎麼辦？",
        "answer": "若手環畫面出現 ON/OFF，請將選項選至ON並長按功能鍵直到恢復時間的畫面",
    },
    {
        "label": "手環是否防水",
        "keywords": ["碰水", "洗澡", "游泳"],
        "question": "手環是否可以戴著洗澡或碰水？",
        "answer": "若是一般洗手是可以戴著手環不用拔除，若是洗澡或是游泳等會長時間浸泡或碰觸水的情況，為了手環的穩定性，建議將手環拔除並與手機放置同一位置，避免藍芽斷線",
    },
    {
        "label": "藍牙斷線",
        "keywords": ["藍牙", "藍芽", "斷線", "連接", "連線"],
        "question": "怎麼樣知道藍芽斷線了？怎麼處理？",
        "answer": "若手環時間畫面右上角沒有藍芽的圖示，則代表沒有與藍芽連線，請將手機收案app打開即可自動連線",
    },
    {
        "label": "偶爾不穿手環",
        "keywords": ["偶爾", "不穿", "拆掉"],
        "question": "可以偶爾把手環拆掉嗎？",
        "answer": "原則上會希望除了洗澡之外的時間都將手環佩戴著，因為連續的體溫監測才能更及時的掌握您的體溫狀況及變化。若偶爾想要將手環拆下稍作休息，請將手環與手機放在同一位置以保持藍芽連線",
    },
    {
        "label": "手環電池",
        "keywords": ["沒有電", "電池", "沒電", "電"],
        "question": "怎麼知道手環還有沒有電？",
        "answer": "手機收案app的畫面有一個「電量」，此即是手環的電量。若手環沒電會自動關機，此時請將手環拔除充電",
    },
    {
        "label": "手環顯示有溫差",
        "keywords": ["體溫", "溫度", "差"],
        "question": "為什麼手環顯示的溫度跟平常量的溫度差這麼多？",
        "answer": "手環上所顯示的是體表溫度，與耳溫槍所量的核心溫度有差異是正常的",
    }
]

qa_trigger = [
    "/qa",
]

# Get question embeddings
with open("embeddings/question.pickle", "rb") as f:
    question_embeddings = pickle.load(f)

qa_greeting = "您好，請問我可以如何幫您？\n（小弟目前還在學習中，請多多指教～）"

qa_check_is_helpful = "請問是否是您想要問的問題嗎？"

qa_unknown = "不好意思，我不明白您的意思…"

qa_thanks = "感謝您的回饋。"

qa_sorry = "不好意思，目前沒辦法回應您的需求。我們會再改進～"


def qa_response(idx):
    return (
        "您想問的問題可能是:\n「" +
        qa_list[idx]["question"] +
        "」\n\n我們的回答是:\n「" +
        qa_list[idx]["answer"] +
        "」"
    )


def qa_template():
    return TemplateSendMessage(
        alt_text="不好意思，請問以下有您想要問的問題嗎？\n若沒有，請輸入「無」。",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title="不好意思，請問以下有您想要問的問題嗎？若沒有，請輸入「無」。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=qa["label"],
                            text=qa["question"],
                        ) for qa in qa_list[:3]
                    ]
                ),
                CarouselColumn(
                    title="不好意思，請問以下有您想要問的問題嗎？若沒有，請輸入「無」。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=qa["label"],
                            text=qa["question"],
                        ) for qa in qa_list[3:]
                    ]
                )
            ]
        )
    )

##############################
# Scenario 1: High Temp Templates
##############################


symptoms_list = [
    {
        "status": "s1d0",
        "label": "皮膚出疹",
        "reply": "體溫異常升高，加上皮膚出疹為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    },
    {
        "status": "s1d1",
        "label": "眼窩痛",
        "reply": "體溫異常升高，加上眼窩痛為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    },
    {
        "status": "s1d2",
        "label": "喉嚨痛",
        "reply": "體溫異常升高，加上喉嚨痛為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    },
    {
        "status": "s1d3",
        "label": "咳嗽",
        "reply": "體溫異常升高，加上咳嗽為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    },
    {
        "status": "s1d4",
        "label": "咳血痰",
        "reply": "體溫異常升高，加上咳血痰為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    },
    {
        "status": "s1d5",
        "label": "肌肉酸痛",
        "reply": "體溫異常升高，加上肌肉酸痛為疑登革熱/流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
    }
]

high_temp_greeting = "您好，手環資料顯示您的體溫似乎比較高，請問您有不舒服的情形嗎？"

high_temp_ending = "請持續密切留意您的您的體溫變化，多休息多喝水，至公共場合時記得戴口罩，至公共場合時記得戴口罩,若有任何身體不適仍建議您至醫療院所就醫。"

high_temp_ask_clinic = "為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？"

high_temp_ask_location = "請將您目前的位置傳送給我～"

high_temp_asap = "請盡快至您熟悉方便的醫療院所就醫。"

high_temp_unknown = "不好意思，我不明白您的意思…"


def flu_info():
    return "\n".join([
        "流感併發重症",
        "https://www.cdc.gov.tw/Disease/SubIndex/x7jzGIMMuIeuLM5izvwg_g",
        "新型A型流感",
        "https://www.cdc.gov.tw/Disease/SubIndex/8Yt_gKjz-BEr3QJZGOa0fQ"
    ])


def dengue_info():
    return "\n".join([
        "登革熱",
        "https://www.cdc.gov.tw/Disease/SubIndex/WYbKe3aE7LiY5gb-eA8PBw"
    ])


def symptoms_template():
    return TemplateSendMessage(
        alt_text="請問您是否有以下的症狀？",
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    title="請問您是否有以下的症狀？若無，請輸入「無」。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=symptom["label"],
                            text=symptom["label"],
                        ) for symptom in symptoms_list[:3]
                    ]
                ),
                CarouselColumn(
                    title="請問您是否有以下的症狀？若無，請輸入「無」。",
                    text=" ",
                    actions=[
                        MessageAction(
                            label=symptom["label"],
                            text=symptom["label"],
                        ) for symptom in symptoms_list[3:]
                    ]
                )
            ]
        )
    )


def get_nearby_clinic(address):
    try:
        candidates = gmaps.places(
            query=f"{address} 內科 耳鼻喉", language="zh-TW")["results"]
        # send the nearby clinic to user
        if len(candidates) != 0:
            return LocationSendMessage(
                title="離您最近的診所是：" + candidates[0]["name"],
                address=candidates[0]["formatted_address"],
                latitude=candidates[0]["geometry"]["location"]["lat"],
                longitude=candidates[0]["geometry"]["location"]["lng"]
            )

        return "很抱歉，您附近並沒有相關的診所。"
    except Exception as err:
        print(err)
        print(traceback.format_exc())
        print("Failed to get nearby clinic")

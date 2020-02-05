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


import google_map as gmaps
import utilities

##############################
# Application & variable initialization
##############################
# Is development or production
is_development=True
if is_development:
    # Channel Access Token
    line_bot_api = LineBotApi('XEQclTuSIm6/pcNNB4W9a2DDX/KAbCBmZS4ltBl+g8q2IxwJyqdtgNNY9KtJJxfkuXbHmSdQPAqRWjAciP2IZgrvLoF3ZH2C2Hg+zZMgoy/xM/RbnoFa2eO9GV2F4E1qmjYxA0FbJm1uZkUms9o+4QdB04t89/1O/w1cDnyilFU=')
    # Channel Secret
    handler = WebhookHandler('fabfd7538c098fe222e8012e1df65740')
else:
    # Fill in when required
    pass


def registration_resp(event, status, session):
    '''
    Gets the status of user and replies according to user's registration status
    '''
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
        userid = event.source.user_id
        status = session.status[userid]['sess_status']
        msg = "不好意思，您的輸入有所異常。\n" + err_msg[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )

def qa_resp(event, status):
    '''
    Reply user according to status
    '''
    text = event.message.text

    if status == 'qa0':
        msg = "您好，請問我可以如何幫你？"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    elif status == 'qa1':
        found = False
        # Keyword matching
        for keys, values in qa_utils.qa_dict.items():
            for keyword in keys:
                if keyword in text:
                    found = True
                    msg = f"你想問的問題可能是:{repr(values[0])}\n我們的回答是:{repr(values[1])}\n請問是否是你想要問的問題嗎？"
                    sess.status[userid]['sess_status'] = "qa2"
                    return "qa2"
        # Calculate cosine similarity if no keywords found in sentence
        if found == False:
            query = qa_utils.bc.encode([text])
            similarity = []
            for idx in range(len(qa_utils.question_embeddings)):
                query = query.transpose()
                sim = cosine_similarity(query, qa_utils.question_embeddings[idx].resize((768,1)))
                similarity.append(sim)
            max_idx, _ = max((i,v)for i,v in enumerate(similarity))
            msg = f"你想問的問題可能是:{repr(values[0])}\n我們的回答是:{repr(values[1])}\n請問是否是你想要問的問題嗎？"
            sess.status[userid]['sess_status'] = "qa2"
            return "qa2"
    if status == 'qa2':
        # TODO: Label QA
        pass

def high_temp_resp(event, status):
    '''
    High temperature event responder
    '''
    # Initialize variables
    symptom = ['皮膚出疹','眼窩痛','喉嚨痛','咳嗽','咳血痰','肌肉酸痛','其他']

    symptom_msg = {
        's1d1': "體溫異常升高，加上皮膚出疹為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
        's1d2': "體溫異常升高，加上眼窩痛為疑似登革熱情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
        's1d3': "體溫異常升高，加上喉嚨痛為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
        's1d4': "體溫異常升高，加上咳嗽為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
        's1d5': "體溫異常升高，加上咳血痰為疑似流感情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！",
        's1d6': "體溫異常升高，加上肌肉酸痛為疑登革熱/流感 情形，但這只是初步懷疑請不用太過驚慌，以下為相關資訊提供給您！"
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

    def symptoms():
        symptoms = TemplateSendMessage(
            alt_text="請問您是否有以下的症狀？",
            template=ButtonsTemplate(
                title="請問您是否有以下的症狀？若無，請選擇其它。",
                text=" ",
                actions=[
                    MessageAction(
                        label=symptom[0]
                        text=symptom[0]
                    ),
                    MessageAction(
                        label=symptom[1]
                        text=symptom[1]
                    ),
                    MessageAction(
                        label=symptom[2]
                        text=symptom[2]
                    ),
                    MessageAction(
                        label=symptom[3]
                        text=symptom[3]
                    ),
                    MessageAction(
                        label=symptom[4]
                        text=symptom[4]
                    ),
                    MessageAction(
                        label=symptom[5]
                        text=symptom[5]
                    ),
                    MessageAction(
                        label=symptom[6]
                        text=symptom[6]
                    ),
                ]
            )
        )
        return symptoms

    def ask_nearby_clinic():
        question = "為了您的安全健康，建議盡快至醫療院所就醫。\n是否需要提供您附近醫療院所的資訊？"
        msg = TemplateSendMessage(
            alt_text=question,
            template=ButtonsTemplate(
                title=question,
                text=" ",
                actions=[
                    MessageTemplateAction(
                        label='是',
                        text='是'
                    ),
                    MessageTemplateAction(
                        label='否',
                        text='否'
                    )
                ]
            )
        )
        return msg

    def get_nearby_clinic(address, keyword):
        try:
            nearby = gmaps.get_address(address, keyword)

            # send the nearby clinic to user
            if len(nearby) >= 1:
                for pos in nearby:
                    # use url parser to extract latitude and longtitude
                    lat, long = urllib.parse.parse_qs(
                        pos[2])["query"][0].split(",")

                    message = LocationSendMessage(
                        title="離您最近的診所是：" + pos[0],
                        address=pos[1],
                        latitude=str(lat),
                        longitude=str(long))
                    break  # now only push the first result
                pass
            else:
                message = TextSendMessage("很抱歉，您附近並沒有 " + keyword + "。")
                pass
        except:
            message = TextSendMessage("很抱歉，您附近並沒有 " + keyword + "。")

        return message

    ##############################
    # Start of flow
    ##############################

    # Scene 1：Status 0 - API triggered
    if status == 's1s0':
        # Detected user high temperature, ask if they are not feeling well
        msg = "您好，手環資料顯示您的體溫似乎比較高，請問您有不舒服的情形嗎？"
        TF_template = TemplateSendMessage(
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
        line_bot_api.push_message(userid, TF_template)
    
    elif status == 's1s1':
        # If true (not feeling well), ask for symptoms
        symptom_template = symptoms()
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

    elif status == 's1d1' or status == 's1d2':
        # If '皮膚出疹' & '眼窩痛' detected
        msg = symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(dengue_info()))
        line_bot_api.push_message(userid, ask_nearby_clinic())
    elif status == 's1d3' or status == 's1d4' or status == 's1d5':
        # If '喉嚨痛' & '咳嗽' & '咳血痰' detected
        msg = symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(flu_info()))
        line_bot_api.push_message(userid, ask_nearby_clinic())
    elif status == 's1d6':
        # If '肌肉酸痛' detected
        msg = symptom_reply[status]
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
        line_bot_api.push_message(userid, TextSendMessage(flu_info()+"\n"+dengue_info()))
        line_bot_api.push_message(userid, ask_nearby_clinic())
    
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

    elif status == 's1s3':
        # Send clinic info and ask to go see doctor ASAP
        msg =  "請盡快至您熟悉方便的醫療院所就醫。"
        clinic = get_nearby_clinic()
        line_bot_api.reply_message(
            event.reply_token,
            clinic
        )
        line_bot_api.push_message(userid, TextSendMessage(text=msg))
        pass


def push_news_resp(event, status):
    # TODO

    def news_ask_location(self):
        location_question = "請問您有在上述的區域內嗎？"
        buttons_template = TemplateSendMessage(
            alt_text=location_question,
            template=ButtonsTemplate(
                title=location_question,
                text=" ",
                # thumbnail_image_url = "https://ibb.co/RvYKVyK",
                actions=[
                    MessageTemplateAction(
                        label=self.responder.Confirm[0],
                        text=self.responder.Confirm[0]
                    ),
                    MessageTemplateAction(
                        label=self.responder.Disable[0],
                        text=self.responder.Disable[0]
                    )
                ]
            )
        )
        return None, buttons_template
        pass

    if status == 's2s0':
        #TODO: push news and ask if not feeling well?
        # 1.1 Get news
        news = get_news()
        # 1.2 Push news and ask if in location
        line_bot_api.push_message(userid, news)
        line_bot_api.push_message(userid, ask_location())
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
    pass

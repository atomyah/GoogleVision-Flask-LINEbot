# ユーザの送った画像をGoogle Vison APIでOCR解析しリプライ

import io
import base64
import json
import requests
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
)
import os

# LINEアクセストークンとアプリケーションシークレット
ACCESS_TOKEN = ''
SECRET = ''
# Google Vision APIキー
API_KEY = ''

app = Flask(__name__)

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/callback',methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent,message=ImageMessage)
def handle_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    # event.message.idを指定することで画像本体データを読み出せる
    # message_content.content #取得した画像ファイル本体

    image_base64 = base64.b64encode(message_content.content) #画像ファイルをbase64に変換

    #リクエストボディを作成（json.dumps()でJSONに変換してる）
    req_body = json.dumps({
        'requests': [{
            'image': {
                'content': image_base64.decode('utf-8')
            },
            'features': [{
                'type': 'TEXT_DETECTION',
                'maxResults': 5,
            }]
        }]
    })
                        # Vison APIのエンドポイント↓
    res = requests.post("https://vision.googleapis.com/v1/images:annotate?key=" + API_KEY, data=req_body)

    result = res.json()

    txt = result["responses"][0]["fullTextAnnotation"]["text"]

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=txt)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

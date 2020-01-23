# ユーザの送った画像をstaticフォルダに保存してリプライ

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
def handle_Image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    # event.message.idを指定することで画像本体データを読み出せる
    # message_content.content #取得した画像ファイル本体

    with open("static/" + event.message.id + ".jpg","wb") as f:
        f.write(message_content.content)
        print("Saved Image: " + event.message.id)

        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url = "https://hidden-savannah-00000.herokuapp.com/static/" + event.message.id + ".jpg",
                preview_image_url = "https://hidden-savannah-0000.herokuapp.com/static/" + event.message.id + ".jpg"
            )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

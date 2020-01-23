# ユーザの送った画像をGoogle Vison APIで顔検出しcat.pngで隠した合成写真をリプライ

import io
import base64
import json
import requests
from flask import Flask, request, abort
from PIL import Image #Pillowをインストール pip3 install pillow

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
                'type': 'FACE_DETECTION',
                'maxResults': 1,
            }]
        }]
    })
                        # Vison APIのエンドポイント↓
    res = requests.post("https://vision.googleapis.com/v1/images:annotate?key=" + API_KEY, data=req_body)

    result = res.json()

    vertices = result["responses"][0]["faceAnnotations"][0]["boundingPoly"]['vertices']
    if vertices:
        print('取得できた')
    else:
        print('取得できてない')

    """
    resultはこんな感じになる。vertices（認識した顔の矩形の4頂点の座標
    {
    "responses": [
        {
        "faceAnnotations": [
        {
          "boundingPoly": {
            "vertices": [
              {
                "x": 932,
                "y": 313
              },
              {
                "x": 1028,
                "y": 313
              },
              {
                "x": 1028,
                "y": 425
              },
              {
                "x": 932,
                "y": 425
              }
            ]
          },
          "fdBoundingPoly": {
              ・・・
    """

    corner = vertices[0]

    width = vertices[1]['x'] - vertices[0]['x']
    height = vertices[2]['y'] - vertices[1]['y']

    image_base = Image.open(io.BytesIO(message_content.content))
    image_cover = Image.open('static/cat.png') # cat.pngはアルファチャンネル画像でないとダメ。ValueError: bad transparency maskとエラー
    image_cover = image_cover.resize((width,height))
    image_base.paste(image_cover, (corner['x'],corner['y']), image_cover)
    # Image.paste(im, box=None, mask=None)
    image_base.save('static/' + event.message.id + '.jpg')


    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
                original_content_url = "https://hidden-savannah-00000.herokuapp.com/static/" + event.message.id + ".jpg",
                preview_image_url = "https://hidden-savannah-00000.herokuapp.com/static/" + event.message.id + ".jpg"
        )
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

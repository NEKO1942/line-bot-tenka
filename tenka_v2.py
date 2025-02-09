#ライブラリのインポート
from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction,FlexSendMessage,BubbleContainer, TextComponent
)

import os
import re
import random
import requests
import json
from datetime import datetime
from math import ceil
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from city_ids import cityIDs
import response
from youtube_channel import channel_name,support_channel

wakaranai_words = response.wakaranai_words
place_recommend = response.place_recommend
music_recommend = response.music_recommend
restaurant_recommend = response.restaurant_recommend
jidori_img= response.jidori_img


# 軽量なウェブアプリケーションフレームワーク:Flask
app = Flask(__name__)

#LINE Acces Token
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

#LINE Channel Secret
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/", methods=['GET'])
def hello_world():
    return "koupen sample"

@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


# ここからが返信メッセージを作成しているブロック
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    sendmsg = ""
    sendimg = ""

    if event.message.text == "今期アニメ":
        year = datetime.now().year
        course = ceil(datetime.now().month / 3)
        anime_flex_list = generate_anime_flex(year, course)
                
        line_bot_api.reply_message(
            event.reply_token,
            [
            FlexSendMessage(alt_text="Anime Flex 1", contents=anime_flex_list[0]),
            FlexSendMessage(alt_text="Anime Flex 2", contents=anime_flex_list[1]),
            FlexSendMessage(alt_text="Anime Flex 3", contents=anime_flex_list[2]),
            FlexSendMessage(alt_text="Anime Flex 4", contents=anime_flex_list[3]),
            FlexSendMessage(alt_text="Anime Flex 5", contents=anime_flex_list[4]),
                    ]
                )
    elif event.message.text == "来期アニメ":
        year = datetime.now().year
        #四半期に変換
        year, course = checkcourse(datetime.now().year, ceil(datetime.now().month / 3)+1)
        anime_flex_list = generate_anime_flex(year, course)

        line_bot_api.reply_message(
            event.reply_token,
            [
            FlexSendMessage(alt_text="Anime Flex 1", contents=anime_flex_list[0]),
            FlexSendMessage(alt_text="Anime Flex 2", contents=anime_flex_list[1]),
            FlexSendMessage(alt_text="Anime Flex 3", contents=anime_flex_list[2]),
            FlexSendMessage(alt_text="Anime Flex 4", contents=anime_flex_list[3]),
            FlexSendMessage(alt_text="Anime Flex 5", contents=anime_flex_list[4]),
                    ]
                )
    elif event.message.text == "前期アニメ":
        year = datetime.now().year
        #四半期に変換
        year, course = checkcourse(datetime.now().year, ceil(datetime.now().month / 3)-1)
        anime_flex_list = generate_anime_flex(year, course)
        
        line_bot_api.reply_message(
            event.reply_token,
            [
            FlexSendMessage(alt_text="Anime Flex 1", contents=anime_flex_list[0]),
            FlexSendMessage(alt_text="Anime Flex 2", contents=anime_flex_list[1]),
            FlexSendMessage(alt_text="Anime Flex 3", contents=anime_flex_list[2]),
            FlexSendMessage(alt_text="Anime Flex 4", contents=anime_flex_list[3]),
            FlexSendMessage(alt_text="Anime Flex 5", contents=anime_flex_list[4]),
                    ]
                )
    
    elif re.search("自撮り", event.message.text):
        sendmsg = jidori_img[random.randrange(len(jidori_img))]

        line_bot_api.reply_message(
            event.reply_token,
            [ImageSendMessage(
            original_content_url = sendmsg,
            preview_image_url = sendmsg
            ),
            TextSendMessage(text = "こ、こんな感じ……かな……？")
            ]
        )
    elif re.search("何が出来る|何ができる|ヘルプ", event.message.text):
        sendmsg = "甜花……色々できるよ……" +"\n" + "「おはよう」「こんにちは」「こんばんは」に、反応して……あ、挨拶、できる……かも……" + "\n" + "「自己紹介して」って、聞いてくれたら……ちょっと、緊張しちゃうけど、自己紹介、する、かも……" +"\n"+"\n" + "おすすめの観光地とか、曲とか、飲食店……「おすすめの観光地」「おすすめの曲」「おすすめの飲食店」で、質問してみて……なんとか、答える、かも……"+"\n" +"\n"+"今日の天気とか、明日の天気も、47都道府県全部……「〇〇の天気」か「明日の〇〇の天気」で、聞かれたら、ちょっと、わかる、かも……"+"\n"+"\n"+"「自撮り送って」って、言われたら……ちょっと、恥ずかしい、けど、一生懸命、頑張って、送る、かも……"+"\n"+"プロデューサーさんのために、甜花、頑張る……! どうぞ、よろしく、お願いします…"
        sendimg = "https://imassc.gamedbs.jp/image/card/still/1611632395272_sqnvuf16.jpg"
        line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text = sendmsg),
                    ImageSendMessage(original_content_url = sendimg,preview_image_url = sendimg)
                    ]
            )
    elif "の天気" in event.message.text:
        place_name = event.message.text.replace("の天気", "")
        tomorrow_weather = False

        if "明日の" in place_name:
            place_name = place_name.replace("明日の", "")
            tomorrow_weather = True
        elif "今日の" in place_name:
            place_name = place_name.replace("今日の", "")
        
        elif place_name =="今日":
            place_name = "東京"
            tomorrow_weather = False
        elif place_name =="明日":
            place_name = "東京"
            tomorrow_weather = True

        if place_name is not None:

            try:
                city_data = cityIDs.get(place_name)
                city_id = city_data[0]
                latitude = city_data[1]
                longitude = city_data[2]
                (weather_detail,weather_detail_tomorrow,chancerain_morning,chancerain_daytime,chancerain_night,chancerain_morning_tomorrow,chancerain_daytime_tomorrow,chancerain_night_tomorrow) = weather_data(city_id)
                (maxtemp,mintemp,maxtemp_tomorrow,mintemp_tomorrow) = weather(latitude,longitude)

                if tomorrow_weather:
                    sendmsg = "明日の"+place_name+"の天気は" + "\n"+"■天気"+"\n" + str(weather_detail_tomorrow) + "\n" + "■気温"+"\n" + str(maxtemp_tomorrow) +"℃/"+ str(mintemp_tomorrow)+ "℃"  + "\n" + "■降水確率"+"\n" + "朝:" + str(chancerain_morning_tomorrow)+ " 昼:"+str(chancerain_daytime_tomorrow)+" 夜:"+str(chancerain_night_tomorrow) +  "\n" + "だよ……"
                else:
                     sendmsg = "今日の"+place_name+"の天気は" + "\n"+"■天気"+ "\n" + str(weather_detail) + "\n" + "■気温"+"\n" + str(maxtemp) +"℃/"+ str(mintemp)  + "℃"+"\n" + "■降水確率 " +"\n"+ "朝:" + str(chancerain_morning)+ " 昼:"+str(chancerain_daytime)+" 夜:"+str(chancerain_night)+ "\n" + "だよ……"
            except:
                 sendmsg="エラーだよ……" + "\n" + "えっと、プロデューサーさん、今日の天気とか知りたかったら、「〇〇の天気」か「天気」、「今日の天気」って、聞いてみてね。そしたら、ちょっと、お手伝い……する……かも……。" + "\n" + "それと、明日の天気が知りたかったら、「明日の〇〇の天気」か「明日の天気」って、聞いてみてね。" +"\n" +"でも、もし出なかったら、対応してない、地域なんだ… ごめんね……"


        line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text = sendmsg)
                    ]
            )
    elif event.message.text =="天気":
        
        try:
            city_data = cityIDs.get("東京")
            city_id=city_data[0]
            latitude=city_data[1]
            longitude=city_data[2]
            (weather_detail,weather_detail_tomorrow,chancerain_morning,chancerain_daytime,chancerain_night,chancerain_morning_tomorrow,chancerain_daytime_tomorrow,chancerain_night_tomorrow) = weather_data(city_id)
            (maxtemp,mintemp,maxtemp_tomorrow,mintemp_tomorrow) = weather(latitude,longitude)
            sendmsg = "今日の東京の天気は" + "\n"+"■天気"+ "\n" + str(weather_detail) + "\n" + "■気温"+"\n" + str(maxtemp) +"℃/"+ str(mintemp)  + "℃"+"\n" + "■降水確率 " +"\n"+ "朝:" + str(chancerain_morning)+ " 昼:"+str(chancerain_daytime)+" 夜:"+str(chancerain_night)+ "\n" + "だよ……"
        except:
             sendmsg="エラーだよ……" + "\n" + "えっと、プロデューサーさん、今日の天気とか知りたかったら、「〇〇の天気」か「天気」、「今日の天気」って、聞いてみてね。そしたら、ちょっと、お手伝い……する……かも……。" + "\n" + "それと、明日の天気が知りたかったら、「明日の〇〇の天気」か「明日の天気」って、聞いてみてね。" +"\n" +"でも、もし出なかったら、対応してない、地域なんだ… ごめんね……"
        
        line_bot_api.reply_message(
                    event.reply_token,
                    
                    TextSendMessage(text = sendmsg)
                    
            )
    elif re.search("おはよう",event.message.text):
        sendmsg = "あ、あっ… おはようございます… "

        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
        )
    elif re.search("こんにちは",event.message.text):
         sendmsg = "こ、こんにちは… "

         line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
         )
    elif re.search("こんばんは",event.message.text):
        sendmsg = "ぷ、プロデューサーさん……こんばんは……"

        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
        )
    elif re.search("自己紹介", event.message.text):
        sendmsg = "甜花は、アイドルグループ「アルストロメリア」のメンバーで、17歳。誕生日は12月25日で、血液型はA型だよ……。"+"\n"+"\n"+"趣味はお昼寝したり、ネットサーフィン、アニメとかゲームとかが好きかな……。"+"\n"+"\n"+"特技はあんまりないけど、ちょっとずつがんばってるよ。アイドル活動やレッスン、お仕事に励んで、プロデューサーさんに、少しでも、笑顔を届けられたらいいなって、思ってるんだ… 。"+"\n"+"あ、そうそう、なーちゃんもいるんだ。なーちゃんは、甜花の双子の妹で、いつも優しくて、元気な子。甜花のことも、なーちゃんが、いっぱい、支えてくれてるんだ… だから、これからも、プロデューサーさんと、なーちゃんと、一緒に、がんばりたいなって、思ってるんだ… "+"\n"+"プロデューサーさん、これからも、よろしくお願いします…"

        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
        )
    elif (event.message.type =="location"):
        sendmsg == "位置情報を取得しました"

        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
        )
    elif ("おすすめ" in event.message.text or "オススメ" in event.message.text) and "観光地" in event.message.text:
        sendmsg = "おすすめの観光地は"+"\n"+place_recommend[random.randrange(len(place_recommend))] +"だよ……"

        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
            )

    elif ("おすすめ" in event.message.text or "オススメ" in event.message.text) and any(keyword in event.message.text for keyword in ["曲", "音楽"]):
        random_song = music_recommend[random.randrange(len(music_recommend))]
        title = random_song["title"]
        url = random_song["url"]
        sendmsg = "おすすめの曲は"+"\n"+title +"だよ……"

        line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text = sendmsg),
                     TextSendMessage(text = url)
                    ]            
            )

    elif ("おすすめ" in event.message.text or "オススメ" in event.message.text) and any(keyword in event.message.text for keyword in ["飲食店", "レストラン"]):
        random_restaurant = restaurant_recommend[random.randrange(len(restaurant_recommend))]
        title = random_restaurant["title"]
        url = random_restaurant["url"]
        sendmsg = "おすすめの代々木上原周辺の飲食店は"+"\n"+title +"だよ〜"

        line_bot_api.reply_message(
                    event.reply_token,
                    [TextSendMessage(text = sendmsg),
                    TextSendMessage(text=url)
                    ]
            )
    
    elif re.search(r"^(おすすめの)?(.*?)の動画$", event.message.text):
        ytname = re.search(r"^(おすすめの)?(.*?)の動画$", event.message.text)
        if ytname:
            ytname = ytname.group(2)
            channel_data = channel_name.get(ytname)

            if channel_data:
                channel_id = channel_data
                video_flex = youtube_flex(channel_id)
                
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        FlexSendMessage(alt_text="YouTube Video", contents=video_flex),
                    ]
                )
            else:
                video_flex_error = video_error()
                error_msg = "あ、あの… ちょっと、チャンネル情報が、見つからなかったみたい… 別の名前で、試してみたら、…う、うまくいくかな…？"
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        FlexSendMessage(alt_text="error_video", contents=video_flex_error),
                        TextSendMessage(text=error_msg),
                    ]
                )
    
    
    
    elif event.message.text == "投稿者一覧":
        sendmsg = "\n".join(support_channel)
        
        line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text = sendmsg)
        )


# 条件分岐その３: それ以外
    else:
            sendmsg = random.choice(wakaranai_words)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text = sendmsg)
            )


CACHE_FILE = 'cache.json'

# キャッシュを読み込む関数
def load_cache():
    try:
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# キャッシュを保存する関数
def save_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file)

# キャッシュをクリアする関数
def clear_cache():
    now = datetime.now()
    if now.day == 1:
        cache.clear()
        save_cache(cache)

cache = load_cache()

def get_cached_thumbnail(official_url):
    if official_url in cache:
        return cache[official_url]
    else:
        response = requests.get(official_url)
        soup = BeautifulSoup(response.content, "lxml")
        meta_tags = soup.select('[property="og:image"]')

        if meta_tags:
            thumbnail_url = meta_tags[0]['content']
            if thumbnail_url.startswith("http:"):
                thumbnail_url = "https:" + thumbnail_url[5:]
            cache[official_url] = thumbnail_url
            save_cache(cache)
            return thumbnail_url

    return None

def get_anime_data(year, course):
    API_URL = f'https://anime-api.deno.dev/anime/v1/master/{year}/{course}'
    res = requests.get(API_URL)
    data = json.loads(res.text)
    anime_data = []

    for item in data:
        anime_title = item["title"]
        product_companies = item["product_companies"]
        #thumbnail_url = item["snippet"]["thumbnails"]["medium"]["url"]
        official_URL = item["public_url"]
        official_X = "https://twitter.com/" + item["twitter_account"]
        thumbnail_url = get_cached_thumbnail(official_URL)

        anime_info = {
            "title": anime_title,
            #"thumbnail": thumbnail_url,
            "official_URL": official_URL,
            "official_X": official_X,
            "product_companies":product_companies,
            "thumbnail_url": thumbnail_url

        }

        anime_data.append(anime_info)
        

    return anime_data

def create_anime_bubble(anime_title, official_URL, official_X,product_companies,thumbnail_url):
    if not product_companies:
        product_companies = "情報なし"  # デフォルトのテキストを設定
    if not thumbnail_url:
        thumbnail_url = "https://edogawa-fa.jp/junior/Photo/2008/Photo/NO_DATA.jpg"  # デフォルトのテキストを設定

    bubble =  {
      "type": "bubble",
      "hero": {
        "type": "image",
        "size": "full",
        "aspectRatio": "1200:630",
        "aspectMode": "cover",
        "url": thumbnail_url
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
          {
            "type": "text",
            "text": anime_title,
            "wrap": True,
            "weight": "bold",
            "size": "xl"
          },
          {
            "type": "box",
            "layout": "baseline",
            "contents": [
              {
                "type": "text",
                "text": product_companies,
                "wrap": True,
                "weight": "regular",
                "size": "xs",
                "flex": 0
              }
            ]
          }
        ]
      },
      "footer": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
          {
            "type": "button",
            "style": "primary",
            "action": {
              "type": "uri",
              "label": "公式サイト",
              "uri": official_URL
            }
          },
          {
            "type": "button",
            "action": {
              "type": "uri",
              "label": "公式X",
              "uri": official_X
            },
            "style": "secondary"
          }
        ]
      }
    }
    return bubble

def generate_anime_flex(year, course):
    anime_data = get_anime_data(year, course)
    anime_flex_contents_list = []
    
    chunk_size = 12
    for i in range(0, len(anime_data), chunk_size):
        chunk = anime_data[i:i + chunk_size]
        anime_bubbles = []

        for anime in chunk:
            bubble = create_anime_bubble(anime["title"], anime["official_URL"], anime["official_X"], anime["product_companies"],anime["thumbnail_url"])
            anime_bubbles.append(bubble)
        
        anime_flex_contents = {
            "type": "carousel",
            "contents": anime_bubbles
        }
        anime_flex_contents_list.append(anime_flex_contents)

    return anime_flex_contents_list


def checkcourse(year, course):
    # courseの値が5になったら、次の年の1期になるので、年を1増やす。一方で、courseの値が0になったら、前の年の4期になるので、年を1減らす。
    if (course == 5):
        year += 1
        course = 1
    elif (course == 0):
        year -= 1
        course = 4
    return year, course


def weather(latitude,longitude):
    API_URL = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=precipitation_probability&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=Asia%2FTokyo&forecast_days=3"
    res = requests.get(API_URL)
    data = json.loads(res.text)
    maxtemp = Decimal(str(data["daily"]["temperature_2m_max"][0])).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
    mintemp = Decimal(str(data["daily"]["temperature_2m_min"][0])).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
    maxtemp_tomorrow = Decimal(str(data["daily"]["temperature_2m_max"][1])).quantize(Decimal('0'), rounding=ROUND_HALF_UP)
    mintemp_tomorrow = Decimal(str(data["daily"]["temperature_2m_min"][1])).quantize(Decimal('0'), rounding=ROUND_HALF_UP)

    return maxtemp,mintemp,maxtemp_tomorrow,mintemp_tomorrow


def weather_data(city_id):
    API_URL = f"https://weather.tsukumijima.net/api/forecast/city/{city_id}"
    res = requests.get(API_URL)
    data = json.loads(res.text)
    weather_detail = data["forecasts"][0]["telop"]
    weather_detail_tomorrow = data["forecasts"][1]["telop"]
    chancerain_morning = data["forecasts"][0]["chanceOfRain"]["T06_12"]
    chancerain_daytime = data["forecasts"][0]["chanceOfRain"]["T12_18"]
    chancerain_night = data["forecasts"][0]["chanceOfRain"]["T18_24"]
    chancerain_morning_tomorrow = data["forecasts"][1]["chanceOfRain"]["T06_12"]
    chancerain_daytime_tomorrow = data["forecasts"][1]["chanceOfRain"]["T12_18"]
    chancerain_night_tomorrow = data["forecasts"][1]["chanceOfRain"]["T18_24"]
    return weather_detail,weather_detail_tomorrow,chancerain_morning,chancerain_daytime,chancerain_night,chancerain_morning_tomorrow,chancerain_daytime_tomorrow,chancerain_night_tomorrow




def get_youtube_video(channel_id):
    youtube_api = os.getenv("youtube_api")
    API_URL = f"https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={channel_id}&maxResults=10&order=date&type=video&key={youtube_api}"
    res = requests.get(API_URL)
    data = json.loads(res.text)
    video_data = []

    for item in data["items"]:
        video_title = item["snippet"]["title"]
        thumbnail_url = item["snippet"]["thumbnails"]["medium"]["url"]
        video_URL = "https://www.youtube.com/watch?v=" + item["id"]["videoId"]
        channel_title = item["snippet"]["channelTitle"]

        video_info = {
            "title": video_title,
            "thumbnail": thumbnail_url,
            "video_URL": video_URL,
            "channel_title": channel_title
        }

        video_data.append(video_info)
        

    return video_data


def create_video_bubble(video_title, thumbnail_url, video_URL, channel_title):
    bubble = {
        "type": "bubble",
        "hero": {
            "type": "image",
            "size": "full",
            "aspectRatio": "16:9",
            "aspectMode": "cover",
            "url": thumbnail_url
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": video_title,
                    "wrap": True,
                    "weight": "bold",
                    "size": "lg"
                },
                {
                    "type": "box",
                    "layout": "baseline",
                    "contents": [
                        {
                            "type": "text",
                            "text": channel_title,
                            "weight": "regular",
                            "size": "sm",
                            "flex": 0,
                            "wrap": True
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "action": {
                        "type": "uri",
                        "label": "動画を見る",
                        "uri": video_URL
                    }
                }
            ]
        }
    }
    return bubble


def youtube_flex(channel_id):
    video_data = get_youtube_video(channel_id)
    video_bubbles = []

    for video in video_data:
        bubble = create_video_bubble(video["title"], video["thumbnail"], video["video_URL"], video["channel_title"])
        video_bubbles.append(bubble)

    video_flex = {
        "type": "carousel",
        "contents": video_bubbles
    }
    return video_flex

def video_error():
    video_flex_error ={
  "type": "carousel",
  "contents": [
    {
      "type": "bubble",
      "hero": {
        "type": "image",
        "size": "full",
        "aspectRatio": "800:641",
        "aspectMode": "cover",
        "url": "https://1.bp.blogspot.com/-d3vDLBoPktU/WvQHWMBRhII/AAAAAAABL6E/Grg-XGzr9jEODAxkRcbqIXu-mFA9gTp3wCLcBGAs/s800/internet_404_page_not_found.png"
      },
      "body": {
        "type": "box",
        "layout": "vertical",
        "spacing": "md",
        "contents": [
          {
            "type": "text",
            "text": "エラーです！",
            "wrap": True,
            "weight": "bold",
            "size": "lg"
          }
        ]
      },
      "footer": {
        "type": "box",
        "layout": "horizontal",
        "spacing": "none",
        "contents": [
          {
            "type": "button",
            "action": {
              "type": "message",
              "label": "投稿者一覧を表示する",
              "text": "投稿者一覧"
            },
            "style": "primary"
          }
        ],
        "margin": "none"
      }
    }
  ]
}
    return video_flex_error



if __name__ == "__main__":
    port = os.getenv("PORT")
    app.run(host="0.0.0.0", port=port)

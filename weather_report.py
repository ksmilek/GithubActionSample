# 安装依赖 pip3 install requests html5lib bs4 schedule
import os
import requests
import json
from bs4 import BeautifulSoup

# 从环境变量获取微信公众号信息
appID = os.environ.get("APP_ID")
appSecret = os.environ.get("APP_SECRET")
# 收信人ID列表，用逗号分隔
openIds_str = os.environ.get("OPEN_IDS")
if openIds_str is None:
    print("Error: Environment variable 'OPEN_IDS' is not set.")
    exit(1)
openIds = openIds_str.split(',')
# 天气预报模板ID
weather_template_id = os.environ.get("TEMPLATE_ID")
if weather_template_id is None:
    print("Error: Environment variable 'TEMPLATE_ID' is not set.")
    exit(1)

def get_weather(my_city):
    urls = [
        "http://www.weather.com.cn/textFC/hb.shtml",  # 华北
        "http://www.weather.com.cn/textFC/db.shtml",  # 东北
        "http://www.weather.com.cn/textFC/hd.shtml",  # 华东
        "http://www.weather.com.cn/textFC/hz.shtml",  # 华中
        "http://www.weather.com.cn/textFC/hn.shtml",  # 华南
        "http://www.weather.com.cn/textFC/xb.shtml",  # 西北
        "http://www.weather.com.cn/textFC/xn.shtml"   # 西南
    ]
    for url in urls:
        resp = requests.get(url)
        text = resp.content.decode("utf-8")
        soup = BeautifulSoup(text, 'html5lib')
        div_conMidtab = soup.find("div", class_="conMidtab")
        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")[2:]
            for index, tr in enumerate(trs):
                tds = tr.find_all("td")
                # 这里倒着数，因为每个省会的td结构跟其他不一样
                city_td = tds[-8]
                this_city = list(city_td.stripped_strings)[0]
                if this_city == my_city:

                    high_temp_td = tds[-5]
                    low_temp_td = tds[-2]
                    weather_type_day_td = tds[-7]
                    weather_type_night_td = tds[-4]
                    wind_td_day = tds[-6]
                    wind_td_day_night = tds[-3]

                    high_temp = list(high_temp_td.stripped_strings)[0]
                    low_temp = list(low_temp_td.stripped_strings)[0]
                    weather_typ_day = list(weather_type_day_td.stripped_strings)[0]
                    weather_type_night = list(weather_type_night_td.stripped_strings)[0]

                    wind_day = list(wind_td_day.stripped_strings)[0] + list(wind_td_day.stripped_strings)[1]
                    wind_night = list(wind_td_day_night.stripped_strings)[0] + list(wind_td_day_night.stripped_strings)[1]

                    # 如果没有白天的数据就使用夜间的
                    temp = f"{low_temp}——{high_temp}摄氏度" if high_temp != "-" else f"{low_temp}摄氏度"
                    weather_typ = weather_typ_day if weather_typ_day != "-" else weather_type_night
                    wind = f"{wind_day}" if wind_day != "--" else f"{wind_night}"
                    return this_city, temp, weather_typ, wind


def get_access_token():
    # 获取access token的url
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appID.strip()}&secret={appSecret.strip()}'
    response = requests.get(url).json()
    print(response)
    access_token = response.get('access_token')
    return access_token


def get_daily_love():
    # 每日一句情话
    url = "https://api.lovelive.tools/api/SweetNothings/Serialization/Json"
    r = requests.get(url)
    all_dict = json.loads(r.text)
    sentence = all_dict['returnObj'][0]
    daily_love = sentence
    return daily_love


def send_weather(access_token, weather, openId):
    # touser 就是 openID
    # template_id 就是模板ID
    # url 就是点击模板跳转的url
    # data就按这种格式写，time和text就是之前{{time.DATA}}中的那个time，value就是你要替换DATA的值

    import datetime
    today = datetime.date.today()
    today_str = today.strftime("%Y年%m月%d日")

    body = {
        "touser": openId.strip(),
        "template_id": weather_template_id.strip(),
        "url": "https://weixin.qq.com",
        "data": {
            "date": {
                "value": today_str
            },
            "region": {
                "value": weather[0]
            },
            "weather": {
                "value": weather[2]
            },
            "temp": {
                "value": weather[1]
            },
            "wind_dir": {
                "value": weather[3]
            },
            "today_note": {
                "value": get_daily_love()
            }
        }
    }
    url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}'
    print(requests.post(url, json.dumps(body)).text)


def weather_report(this_city):
    # 1.获取access_token
    access_token = get_access_token()
    # 2. 获取天气
    weather = get_weather(this_city)
    print(f"天气信息： {weather}")
    # 3. 发送消息给所有 OpenID
    for openId in openIds:
        send_weather(access_token, weather, openId)


if __name__ == '__main__':
    weather_report("昭通")

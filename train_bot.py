import settings
import tweepy
import requests
from bs4 import BeautifulSoup

#------------------------------------------------------------------
# keyの指定(情報漏えいを防ぐため伏せています)
consumer_key = settings.CK
consumer_secret = settings.CS
access_token = settings.AT
access_token_secret = settings.ATC

# tweepyの設定(認証情報を設定)
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# tweepyの設定(APIインスタンスの作成)
api = tweepy.API(auth)

#LINEの設定
#line_access_token  = settings.LN
#line_url = 'https://notify-api.line.me/api/notify'
#headers = {'Authorization': 'Bearer ' + line_access_token}

#------------------------------------------------------------------
#辞書を作成
dict = {'59/60':'常磐線[水戸～いわき]', '166/0':'水郡線', '167/0':'水戸線', '76/0':'鹿島線', '181/0':'テスト線'}

#辞書の長さ分実行
for key in dict:
    url = 'https://transit.yahoo.co.jp/diainfo/' + key
    url_text = requests.get(url)
    soup = BeautifulSoup(url_text.text, 'html.parser')
    if soup.find('dd', class_='trouble'):
        message = '⚠' + str(dict[key]) + 'は現在正常に運行していません。\n詳細は下のURLからご確認下さい。(Yahoo路線情報)\n' + url
        payload = {'message': message}
        #r = requests.post(line_url, headers=headers, params=payload,)
        api.update_status_with_(status=message, filename='delay.png')

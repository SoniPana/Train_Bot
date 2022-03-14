import settings
import tweepy
import requests
import time
import shutil
import os
import cv2 
import numpy as np
from mega import Mega
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
line_access_token  = settings.LN
line_url = 'https://notify-api.line.me/api/notify'
headers = {'Authorization': 'Bearer ' + line_access_token}

#------------------------------------------------------------------
#辞書を作成
dict = {'59/60':'常磐線[水戸～いわき]', '166/0':'水郡線', '167/0':'水戸線', '76/0':'鹿島線'}
dict_name = {'常磐線[水戸～いわき]':'joban', '水郡線':'suigun', '水戸線':'mito', '鹿島線':'kasima'}

for key in dict:
  # Chromeヘッドレスモード起動
  options = webdriver.ChromeOptions()
  options.headless = True
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver',options=options)
  driver.implicitly_wait(10)

  # ファイル名接頭辞
  fileNamePrefix = 'image'

  # ウインドウ幅指定
  windowSizeWidth = 800

  # ウインドウ高さ指定
  windowSizeHeight = 600

  # パス指定
  folderPath = fileNamePrefix

  # サイトURL取得
  url = 'https://transit.yahoo.co.jp/diainfo/' + key
  driver.get(url)
  WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
  
  # ウインドウ幅・高さ指定
  windowWidth = windowSizeWidth if windowSizeWidth else driver.execute_script('return document.body.scrollWidth;')
  windowHeight = windowSizeHeight if windowSizeHeight else driver.execute_script('return document.body.scrollHeight;')
  driver.set_window_size(windowWidth, windowHeight)

  # 処理後一時待機
  time.sleep(2)

  # スクリーンショット格納
  driver.save_screenshot('image.png')

  # サーバー負荷軽減処理
  time.sleep(1)

  # ブラウザ稼働終了
  driver.quit()

  # 画像トリミング
  im = Image.open('image.png')
  im.crop((0, 270, 640, 350)).save('now.png', quality=95)
#-----------------------------------------------------------------------------
  #Megaにログイン(e-mailとパスワードは伏せています)
  mega = Mega()
  email = settings.EM
  password = settings.PW
  m = mega.login(email,password)
  
  ###ファイル取得(テスト用)
  ##linux = m.get_files()
  ##print(linux)

  #画像取得
  aaa = dict[key]
  image_pass = dict_name[aaa] + '.png'
  file = m.find(image_pass)
  m.download(file)
#-----------------------------------------------------------------------------
  #画像比較準備
  img_1 = cv2.imread('now.png')
  img_2 = cv2.imread(image_pass)
  
  #画像比較(もし違うなら実行)
  if np.array_equal(img_1, img_2) == False:
    #既にある画像を削除後、アップロード
    os.remove(image_pass)
    os.rename('now.png', image_pass)
    file = m.find(image_pass)
    m.delete(file[0])
    m.upload(image_pass)
    url_text = requests.get(url)
    soup = BeautifulSoup(url_text.text, 'html.parser')
    if soup.find('dd', class_='trouble'):
      message = '⚠「' + str(dict[key]) + '」は現在正常に運行していません。\n詳細は下のURLからご確認下さい。(Yahoo路線情報)\n\n' + url
      api.update_status_with_media(status=message, filename='delay.png')
      li = soup.find('dd', class_='trouble')
      li = [i.strip() for i in li.text.splitlines()]
      li = [i for i in li if i != ""]
      message = str(dict[key]) + 'は' + li[0]
      payload = {'message': message}
      r = requests.post(line_url, headers=headers, params=payload,)
    else:
      message = '✔「' + str(dict[key]) + '」の遅延・運休は解消され、現在は正常に運行しています。'
      payload = {'message': message}
      r = requests.post(line_url, headers=headers, params=payload,)
      api.update_status_with_media(status=message, filename='good.png')

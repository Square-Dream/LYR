import requests
from bs4 import BeautifulSoup
import os

# 크롤링할 웹툰 회차 URL
url = "https://comic.naver.com/webtoon/detail?titleId=777767&no=187&week=fri"

headers = {'User-Agent':'Mozilla/5.0'}  # 크롤링 차단 우회용 헤더

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# 웹툰 이미지가 들어있는 div(class=wt_viewer)에서 img 태그 추출
img_tags = soup.find("div", {"class": "wt_viewer"}).find_all("img")

# 이미지 저장 폴더 생성
os.makedirs("webtoon_images", exist_ok=True)

for idx, img in enumerate(img_tags, 1):
    img_url = img['src']
    img_data = requests.get(img_url, headers=headers).content
    with open(f"webtoon_images/{idx}.jpg", "wb") as f:
        f.write(img_data)

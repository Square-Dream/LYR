import requests
from bs4 import BeautifulSoup
import os
import time
import re

# 크롤링할 웹툰 회차 URL
url = "https://m.comic.naver.com/webtoon/detail?titleId=826381&no=48&week=mon&listSortOrder=DESC&listPage=1"

# 헤더 설정 (중요: Referer 설정이 필요함)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Referer': 'https://comic.naver.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

try:
    # 웹페이지 요청
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # 가능한 여러 클래스명 시도 (네이버 웹툰 구조가 변경될 수 있음)
    possible_classes = ["wt_viewer", "comic_viewer", "viewer_lst", "view_area", "comic_view", "viewer"]
    img_container = None
    
    for class_name in possible_classes:
        container = soup.find("div", class_=class_name)
        if container and container.find_all("img"):
            img_container = container
            print(f"이미지 컨테이너를 찾았습니다: {class_name}")
            break
    
    # 컨테이너를 찾지 못한 경우 다른 방법 시도
    if not img_container:
        # 모든 img 태그 찾기
        all_imgs = soup.find_all("img")
        # 웹툰 이미지로 보이는 것들만 필터링 (src에 "webtoon" 또는 "comic" 포함)
        img_tags = [img for img in all_imgs if img.get('src') and ('webtoon' in img['src'].lower() or 'comic' in img['src'].lower())]
    else:
        img_tags = img_container.find_all("img")
    
    # 이미지가 없으면 종료
    if not img_tags:
        print("이미지를 찾을 수 없습니다.")
        exit(1)
    
    # 이미지 저장 폴더 생성
    os.makedirs("webtoon_images", exist_ok=True)
    
    # 이미지 다운로드
    for idx, img in enumerate(img_tags, 1):
        if not img.get('src'):
            continue
            
        img_url = img['src']
        
        # 상대 URL인 경우 처리
        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        
        print(f"다운로드 중: {img_url}")
        img_response = requests.get(img_url, headers=headers)
        img_response.raise_for_status()
        
        # 이미지 확장자 추출 또는 기본값 사용
        extension = 'jpg'
        if '.' in img_url.split('/')[-1]:
            extension = img_url.split('/')[-1].split('.')[-1]
        
        with open(f"webtoon_images/{idx}.{extension}", "wb") as f:
            f.write(img_response.content)
        
        print(f"이미지 {idx} 저장 완료")
        # 요청 간 지연 추가 (서버 부하 방지)
        time.sleep(0.5)
    
    print(f"총 {len(img_tags)}개의 이미지를 다운로드했습니다.")

except Exception as e:
    print(f"오류 발생: {e}")

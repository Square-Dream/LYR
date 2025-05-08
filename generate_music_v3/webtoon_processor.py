import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
import pytesseract
import hashlib
import json
import time
import random
import traceback
import re

# Tesseract OCR 경로 설정 (Windows 기준)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# 공통 함수 정의
def convert_to_rgb(image):
    """RGBA 이미지를 RGB로 변환"""
    if image.mode == 'RGBA':
        rgb_image = Image.new('RGB', image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])
        return rgb_image
    return image

def save_image(image, path):
    """이미지를 지정된 경로에 저장"""
    image = convert_to_rgb(image)
    image.save(path, 'JPEG')

def preprocess_for_ocr(image):
    """OCR 전처리를 위해 이미지를 이진화"""
    gray_image = image.convert('L')
    threshold = 150
    return gray_image.point(lambda x: 0 if x < threshold else 255, '1')

def create_group_image(images):
    """이미지 그룹을 하나의 이미지로 합치기"""
    combined_height = sum(img.height for img in images)
    max_width = max(img.width for img in images)
    group_image = Image.new('RGB', (max_width, combined_height))
    y_offset = 0
    for img in images:
        img = convert_to_rgb(img)
        group_image.paste(img, ((max_width - img.width) // 2, y_offset))
        y_offset += img.height
    return group_image

def prepare_directories(cache_dir, output_dir, use_cache):
    """캐시 및 출력 디렉토리 준비"""
    if use_cache:
        os.makedirs(cache_dir, exist_ok=True)
        temp_dir = cache_dir  # 캐시 디렉토리만 사용
    else:
        temp_dir = None  # temp_webtoon_images 제거

    if output_dir is None:
        output_dir = "webtoon_images"
        os.makedirs(output_dir, exist_ok=True)

    return temp_dir, output_dir

def clean_ocr_text(text):
    """
    OCR 결과에서 의미 없는 단어와 영어 조각을 제거합니다.
    """
    cleaned_text = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', text)  # 특수문자 제거
    cleaned_text = re.sub(r'\b[a-zA-Z]\b', '', cleaned_text)  # 한 글자 영어 제거
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()  # 연속된 공백 제거
    return cleaned_text

def extract_webtoon_content(url, use_cache=True, output_dir=None, group_size=5):
    """
    웹툰 URL에서 이미지와 텍스트를 추출합니다.
    이미지를 group_size개씩 묶어서 처리합니다.
    """
    print(f"Extracting content from webtoon URL: {url}")
    cache_dir = os.path.join("cache", hashlib.md5(url.encode()).hexdigest())
    temp_dir, output_dir = prepare_directories(cache_dir, output_dir, use_cache)

    # 캐시 확인
    if use_cache and os.path.exists(os.path.join(cache_dir, "metadata.json")):
        try:
            with open(os.path.join(cache_dir, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
                print(f"Using cached content for: {url}")
                return metadata
        except Exception as e:
            print(f"Error loading cache: {e}. Proceeding with fresh extraction.")

    # 웹페이지 가져오기
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 제목 및 작가 정보 추출
        title_tag = soup.find('h2', class_='title') or soup.find('h3', class_='title')
        title = title_tag.text.strip() if title_tag else "Unknown Webtoon"
        author_tag = soup.find('span', class_='author')
        author = author_tag.text.strip() if author_tag else "Unknown Author"

        # 이미지 태그 추출
        image_container = soup.find('div', class_='wt_viewer') or soup.find('div', class_='viewer_lst') or soup.find('div', id='comic_view_area')
        img_tags = image_container.find_all('img') if image_container else soup.find_all('img')
        if not img_tags:
            raise ValueError("No images found in the webtoon page")
        print(f"Found {len(img_tags)} images in the webtoon")

        # 이미지 다운로드 및 처리
        valid_images = []
        for i, img in enumerate(img_tags):
            try:
                img_url = img.get('src')
                if not img_url or not img_url.endswith(('.jpg', '.png', '.jpeg', '.gif')):
                    continue
                if 'comic.pstatic.net' not in img_url and 'image-comic.pstatic.net' not in img_url:
                    continue
                time.sleep(random.uniform(0.5, 1.5))  # 서버 부하 방지
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()
                image = Image.open(BytesIO(img_response.content))
                if image.width < 300 or image.height < 300:
                    print(f"Skipping small image {i+1}: {image.width}x{image.height}")
                    continue
                valid_images.append(image)
                print(f"Processed image {i+1}/{len(img_tags)}")
            except Exception as e:
                print(f"Error processing image {i+1}: {e}")
                traceback.print_exc()

        # 그룹 이미지 생성 및 OCR
        texts = []
        group_image_paths = []
        for i in range(0, len(valid_images), group_size):
            group = valid_images[i:i+group_size]
            group_image = create_group_image(group)
            group_idx = i // group_size + 1
            group_path = os.path.join(output_dir, f"group_image_{group_idx}.jpg")
            save_image(group_image, group_path)  # 그룹 이미지만 저장
            group_image_paths.append(group_path)
            try:
                binary_group = preprocess_for_ocr(group_image)
                group_text = pytesseract.image_to_string(binary_group, lang='kor+eng')
                if group_text.strip():
                    texts.append(group_text)
                    print(f"Extracted text from group image {group_idx}: {group_text[:100]}...")
            except Exception as ocr_error:
                print(f"OCR error for group image {group_idx}: {ocr_error}")

        # 결과 저장
        result = {
            'title': title,
            'author': author,
            'group_image_paths': group_image_paths,
            'texts': texts
        }
        if use_cache:
            with open(os.path.join(cache_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        return result

    except Exception as e:
        print(f"Error extracting webtoon content: {e}")
        traceback.print_exc()
        return {
            'title': "Error",
            'author': "Unknown",
            'group_image_paths': [],
            'texts': []
        }
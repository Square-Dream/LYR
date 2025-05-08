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

def extract_webtoon_content(input_data, use_cache=True, output_dir=None, group_size=5):
    """
    웹툰 콘텐츠를 URL 또는 이미지 파일 리스트로부터 추출합니다.
    
    Args:
        input_data (str or list): URL 또는 이미지 파일 경로 리스트
        use_cache (bool): 캐시 사용 여부
        output_dir (str): 출력 디렉토리
        group_size (int): 그룹당 이미지 개수

    Returns:
        dict: 추출된 콘텐츠 (텍스트, 이미지 경로)
    """
    # URL인지 이미지 파일 리스트인지 확인
    if isinstance(input_data, list):
        print("Processing webtoon from image files...")
        return extract_from_images(input_data, output_dir, group_size)
    else:
        print(f"Processing webtoon from URL: {input_data}")
        return extract_from_url(input_data, use_cache, output_dir, group_size)

def extract_from_images(image_paths, output_dir, group_size):
    """
    이미지 파일 리스트에서 웹툰 콘텐츠를 추출합니다.
    """
    texts = []
    group_image_paths = []

    try:
        # 이미지 파일 로드
        images = []
        for image_path in image_paths:
            try:
                img = Image.open(image_path)
                images.append(img)
                print(f"Loaded image: {image_path}")
            except Exception as e:
                print(f"Error loading image {image_path}: {e}")

        # 이미지 그룹화 및 OCR 처리
        for i in range(0, len(images), group_size):
            group = images[i:i + group_size]
            group_image = create_group_image(group)
            group_idx = i // group_size + 1
            group_path = os.path.join(output_dir, f"group_image_{group_idx}.jpg")
            save_image(group_image, group_path)
            group_image_paths.append(group_path)

            try:
                binary_group = preprocess_for_ocr(group_image)
                group_text = pytesseract.image_to_string(binary_group, lang='kor+eng')
                if group_text.strip():
                    texts.append(group_text)
                    print(f"Extracted text from group {group_idx}: {group_text[:100]}...")
            except Exception as ocr_error:
                print(f"OCR error for group {group_idx}: {ocr_error}")

        return {
            'title': "Uploaded Images",
            'author': "Unknown",
            'group_image_paths': group_image_paths,
            'texts': texts
        }

    except Exception as e:
        print(f"Error processing images: {e}")
        traceback.print_exc()
        return {
            'title': "Error",
            'author': "Unknown",
            'group_image_paths': [],
            'texts': []
        }

def extract_from_url(url, use_cache=True, output_dir=None, group_size=5):
    """
    웹툰 URL에서 이미지와 텍스트를 추출합니다.
    """
    cache_dir = os.path.join("cache", hashlib.md5(url.encode()).hexdigest())

    # 캐시 사용 여부 확인
    if use_cache and os.path.exists(os.path.join(cache_dir, "metadata.json")):
        try:
            with open(os.path.join(cache_dir, "metadata.json"), "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                print(f"Using cached content for: {url}")
                return cached_data
        except Exception as e:
            print(f"Cache loading error: {e}")

    headers = {'User-Agent': 'Mozilla/5.0'}
    texts = []
    group_image_paths = []

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # 웹툰 이미지 추출
        img_tags = soup.find_all('img')
        valid_images = []

        for img_tag in img_tags:
            img_url = img_tag.get('src')
            if img_url and img_url.endswith(('jpg', 'jpeg', 'png')):
                try:
                    img_data = requests.get(img_url, headers=headers).content
                    image = Image.open(BytesIO(img_data))
                    valid_images.append(image)
                except Exception as e:
                    print(f"Error downloading image {img_url}: {e}")

        # 이미지 그룹화 및 OCR 처리
        for i in range(0, len(valid_images), group_size):
            group = valid_images[i:i + group_size]
            group_image = create_group_image(group)
            group_idx = i // group_size + 1
            group_path = os.path.join(output_dir, f"group_image_{group_idx}.jpg")
            save_image(group_image, group_path)
            group_image_paths.append(group_path)

            try:
                binary_group = preprocess_for_ocr(group_image)
                group_text = pytesseract.image_to_string(binary_group, lang='kor+eng')
                if group_text.strip():
                    texts.append(group_text)
                    print(f"Extracted text from group {group_idx}: {group_text[:100]}...")
            except Exception as ocr_error:
                print(f"OCR error for group {group_idx}: {ocr_error}")

        # 결과 저장
        result = {
            'title': "Webtoon from URL",
            'author': "Unknown",
            'group_image_paths': group_image_paths,
            'texts': texts
        }

        # 캐시 저장
        if use_cache:
            with open(os.path.join(cache_dir, "metadata.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    except Exception as e:
        print(f"Error extracting webtoon content from URL: {e}")
        traceback.print_exc()
        return {
            'title': "Error",
            'author': "Unknown",
            'group_image_paths': [],
            'texts': []
        }

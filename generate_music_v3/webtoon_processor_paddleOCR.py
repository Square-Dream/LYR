import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import os
from paddleocr import PaddleOCR
import hashlib
import json
import time
import random
import traceback
import numpy as np

# PaddleOCR 초기화
ocr = PaddleOCR(use_angle_cls=True, lang='korean')  # 한국어 지원

def extract_text_with_paddleocr(image):
    """
    PaddleOCR을 사용하여 이미지에서 텍스트를 추출합니다.
    
    Args:
        image (PIL.Image.Image): OCR을 수행할 이미지 객체
    
    Returns:
        str: 추출된 텍스트
    """
    # 이미지 데이터를 numpy 배열로 변환
    image_np = np.array(image)
    
    # OCR 실행
    result = ocr.ocr(image_np, cls=True)
    
    # 결과에서 텍스트 추출
    extracted_text = []
    for line in result[0]:
        extracted_text.append(line[1][0])  # line[1][0]은 텍스트 내용
    
    return "\n".join(extracted_text)

def extract_webtoon_content(url, use_cache=True, output_dir=None):
    """
    웹툰 URL에서 이미지와 텍스트를 추출합니다.
    
    Args:
        url (str): 웹툰 URL
        use_cache (bool): 캐시 사용 여부
        output_dir (str): 출력 디렉토리 (None인 경우 기본값 사용)
        
    Returns:
        dict: 추출된 이미지와 텍스트 정보
    """
    print(f"Extracting content from webtoon URL: {url}")
    
    # 캐시 디렉토리 확인
    cache_dir = os.path.join("cache", hashlib.md5(url.encode()).hexdigest())
    
    # 캐시 사용 시 이미 처리된 결과가 있는지 확인
    if use_cache and os.path.exists(os.path.join(cache_dir, "metadata.json")):
        try:
            with open(os.path.join(cache_dir, "metadata.json"), "r", encoding="utf-8") as f:
                metadata = json.load(f)
                
                # 이미지 객체 복원
                images = []
                for img_path in metadata['image_paths']:
                    if os.path.exists(img_path):
                        images.append(Image.open(img_path))
                
                metadata['images'] = images
                
                # 출력 디렉토리가 지정된 경우, 이미지를 해당 디렉토리로 복사
                if output_dir:
                    new_image_paths = []
                    for i, img_path in enumerate(metadata['image_paths']):
                        if os.path.exists(img_path):
                            new_path = os.path.join(output_dir, f"webtoon_image_{i+1}.jpg")
                            img = Image.open(img_path)
                            # RGBA 모드 처리
                            if img.mode == 'RGBA':
                                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                                rgb_img.paste(img, mask=img.split()[3])
                                rgb_img.save(new_path, 'JPEG')
                            else:
                                img.save(new_path, 'JPEG')
                            new_image_paths.append(new_path)
                    
                    # 합쳐진 이미지도 복사
                    if metadata['combined_image_path'] and os.path.exists(metadata['combined_image_path']):
                        new_combined_path = os.path.join(output_dir, "combined_webtoon.jpg")
                        img = Image.open(metadata['combined_image_path'])
                        # RGBA 모드 처리
                        if img.mode == 'RGBA':
                            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                            rgb_img.paste(img, mask=img.split()[3])
                            rgb_img.save(new_combined_path, 'JPEG')
                        else:
                            img.save(new_combined_path, 'JPEG')
                        metadata['combined_image_path'] = new_combined_path
                    
                    metadata['image_paths'] = new_image_paths
                
                print(f"Using cached content for: {url}")
                return metadata
        except Exception as e:
            print(f"Error loading cache: {e}. Proceeding with fresh extraction.")
    
    # User-Agent 설정으로 크롤링 방지 우회
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 웹페이지 가져오기
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 오류 발생 시 예외 발생
        
        # BeautifulSoup으로 HTML 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 웹툰 제목 추출
        title_tag = soup.find('h2', class_='title')
        if not title_tag:
            title_tag = soup.find('h3', class_='title')
        title = title_tag.text.strip() if title_tag else "Unknown Webtoon"
        
        # 작가 정보 추출
        author_tag = soup.find('span', class_='author')
        author = author_tag.text.strip() if author_tag else "Unknown Author"
        
        # 이미지 컨테이너 찾기 (다양한 클래스명 시도)
        image_container = soup.find('div', class_='wt_viewer')
        
        if not image_container:
            image_container = soup.find('div', class_='viewer_lst')
        
        if not image_container:
            image_container = soup.find('div', id='comic_view_area')
        
        if not image_container:
            # 컨테이너를 찾지 못한 경우 전체 페이지에서 이미지 검색
            img_tags = soup.find_all('img')
            print("Using alternative method: searching all images in page")
        else:
            # 이미지 태그 찾기
            img_tags = image_container.find_all('img')
        
        if not img_tags:
            raise ValueError("No images found in the webtoon page")
        
        # 캐시 및 이미지 저장 폴더 생성
        if use_cache:
            os.makedirs(cache_dir, exist_ok=True)
            temp_dir = cache_dir
        else:
            temp_dir = "temp_webtoon_images"
            os.makedirs(temp_dir, exist_ok=True)
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_dir = "webtoon_images"
            os.makedirs(output_dir, exist_ok=True)
        
        images = []
        texts = []
        image_paths = []
        
        print(f"Found {len(img_tags)} images in the webtoon")
        
        # 각 이미지 처리
        for i, img in enumerate(img_tags):
            try:
                img_url = img.get('src')
                
                # 웹툰 이미지 필터링 조건 강화
                if not img_url or not (img_url.endswith('.jpg') or img_url.endswith('.png') or 
                                      img_url.endswith('.jpeg') or img_url.endswith('.gif')):
                    continue
                    
                # 이미지 URL이 실제 웹툰 이미지인지 확인 (네이버 웹툰 특성)
                if 'comic.pstatic.net' not in img_url and 'image-comic.pstatic.net' not in img_url:
                    continue
                
                # 크롤링 간격 추가 (서버 부하 방지)
                time.sleep(random.uniform(0.5, 1.5))
                
                # 이미지 다운로드
                img_response = requests.get(img_url, headers=headers)
                img_response.raise_for_status()
                
                # 이미지 객체로 변환
                image = Image.open(BytesIO(img_response.content))
                
                # 작은 이미지 필터링 (아이콘, 버튼 등)
                if image.width < 300 or image.height < 300:
                    print(f"Skipping small image {i+1}: {image.width}x{image.height}")
                    continue
                    
                images.append(image)
                
                # 캐시용 이미지 저장
                temp_path = os.path.join(temp_dir, f"image_{i+1}.jpg")
                # RGBA 모드 처리
                if image.mode == 'RGBA':
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    rgb_image.save(temp_path, 'JPEG')
                else:
                    image.save(temp_path, 'JPEG')
                
                # 출력용 이미지 저장
                output_path = os.path.join(output_dir, f"webtoon_image_{i+1}.jpg")
                if image.mode == 'RGBA':
                    rgb_image.save(output_path, 'JPEG')
                else:
                    image.save(output_path, 'JPEG')
                image_paths.append(output_path)
                
                # OCR로 이미지에서 텍스트 추출
                try:
                    text = extract_text_with_paddleocr(image)
                    if text.strip():
                        texts.append(text)
                        print(f"Extracted text from image {i+1}: {text[:50]}...")
                except Exception as ocr_error:
                    print(f"OCR error for image {i+1}: {ocr_error}")
                
                print(f"Processed image {i+1}/{len(img_tags)}")
                
            except Exception as e:
                print(f"Error processing image {i+1}: {e}")
                traceback.print_exc()
        
        # 결과 저장
        result = {
            'title': title,
            'author': author,
            'images': images,
            'image_paths': image_paths,
            'texts': texts
        }
        
        return result
        
    except Exception as e:
        print(f"Error extracting webtoon content: {e}")
        traceback.print_exc()
        return {
            'title': "Error",
            'author': "Unknown",
            'images': [],
            'texts': [],
            'image_paths': []
        }
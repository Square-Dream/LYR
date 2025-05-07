import os
import re
import json
import hashlib

def process_novel_file(file_path, use_cache=True):
    """
    웹소설 텍스트 파일을 처리합니다.
    
    Args:
        file_path (str): 텍스트 파일 경로
        use_cache (bool): 캐시 사용 여부
        
    Returns:
        dict: 추출된 텍스트 정보
    """
    print(f"Processing novel file: {file_path}")
    
    # 캐시 디렉토리 확인
    cache_dir = os.path.join("cache", "novels")
    os.makedirs(cache_dir, exist_ok=True)
    
    # 파일 해시 계산
    file_hash = ""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Error calculating file hash: {e}")
    
    cache_path = os.path.join(cache_dir, f"{file_hash}.json")
    
    # 캐시 사용 시 이미 처리된 결과가 있는지 확인
    if use_cache and file_hash and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                print(f"Using cached content for: {file_path}")
                return cached_data
        except Exception as e:
            print(f"Error loading cache: {e}. Proceeding with fresh processing.")
    
    try:
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path)
        
        if ext.lower() != '.txt':
            raise ValueError(f"Unsupported file format: {ext}. Only .txt files are supported.")
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # 파일명에서 제목 추출
        title = os.path.basename(file_path).replace('.txt', '')
        
        # 텍스트 전처리
        # 불필요한 공백 제거
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 챕터 구분 (예: "제 1 장", "Chapter 1" 등의 패턴 찾기)
        chapter_pattern = r'(?:제\s*\d+\s*장|Chapter\s*\d+|CHAPTER\s*\d+|\d+\s*장|\d+\.\s)'
        chapters = re.split(chapter_pattern, content)
        if len(chapters) <= 1:
            # 챕터 구분이 없으면 단락으로 구분
            chapters = [p for p in content.split('\n\n') if p.strip()]
        
        # 챕터 제목 추출
        chapter_titles = re.findall(chapter_pattern, content)
        
        # 챕터 제목과 내용 매핑
        chapter_data = []
        for i in range(min(len(chapters), len(chapter_titles) + 1)):
            if i == 0 and not chapter_titles:
                chapter_data.append({
                    'title': '서문',
                    'content': chapters[i].strip()
                })
            elif i > 0 or chapter_titles:
                title_idx = i - 1 if i > 0 else 0
                chapter_title = chapter_titles[title_idx] if title_idx < len(chapter_titles) else f"Chapter {i+1}"
                chapter_data.append({
                    'title': chapter_title.strip(),
                    'content': chapters[i].strip()
                })
        
        # 결과 저장
        result = {
            'title': title,
            'full_text': content,
            'chapters': [ch['content'] for ch in chapter_data],
            'chapter_data': chapter_data,
            'word_count': len(content.split())
        }
        
        # 캐시에 결과 저장
        if use_cache and file_hash:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
        
    except Exception as e:
        print(f"Error processing novel file: {e}")
        return {
            'title': "Error",
            'full_text': f"Error processing file: {str(e)}",
            'chapters': [],
            'chapter_data': [],
            'word_count': 0
        }

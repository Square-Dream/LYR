# Java 메모리 설정
import os
os.environ['JAVA_OPTS'] = '-Xmx4g'  # Java 최대 힙 메모리를 4GB로 설정

from keybert import KeyBERT
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
from konlpy.tag import Okt
import os
from PIL import Image
import hashlib
import json
import base64
import traceback

# NLTK 데이터 다운로드
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# KoNLPy 초기화 - 오류 방지를 위해 try-except로 감싸기
try:
    # JVM 설정
    import jpype
    if not jpype.isJVMStarted():
        jvm_path = jpype.getDefaultJVMPath()
        jpype.startJVM(jvm_path, '-Xms1g', '-Xmx4g', '-Dfile.encoding=UTF8', convertStrings=True)
    
    from konlpy.tag import Okt
    okt_initialized = Okt()
    KONLPY_AVAILABLE = True
except Exception as e:
    print(f"Warning: KoNLPy initialization failed: {e}")
    KONLPY_AVAILABLE = False

# def get_openai_client():
#     """OpenAI 클라이언트를 필요할 때만 초기화합니다."""
#     try:
#         from openai import OpenAI
#         # API 키 설정 방법 1: 환경 변수
#         # import os
#         # os.environ["OPENAI_API_KEY"] = "your-api-key-here"
        
#         # API 키 설정 방법 2: 직접 전달
#         return OpenAI(api_key="여러분의키를넣어주세요")  # 실제 API 키로 교체
#     except Exception as e:
#         print(f"Error initializing OpenAI client: {e}")
#         return None

def get_openai_client(api_key):
    """
    OpenAI 클라이언트를 초기화합니다.

    Args:
        api_key (str): OpenAI API 키

    Returns:
        openai.Client: OpenAI 클라이언트 인스턴스
    """
    try:
        import openai
        openai.api_key = api_key
        return openai
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        return None
    
def analyze_image_content(image_path, api_key):
    """
    이미지 내용을 분석하여 캐릭터의 표정, 행동, 감정 등을 추출합니다.
    OpenAI의 Vision API를 사용합니다.
    
    Args:
        image_path (str): 이미지 파일 경로
        
    Returns:
        list: 추출된 키워드 리스트
    """
    # 이미지 분석 캐시 확인
    cache_dir = os.path.join("cache", "image_analysis")
    os.makedirs(cache_dir, exist_ok=True)
    
    # 이미지 해시 계산
    img_hash = ""
    try:
        with open(image_path, 'rb') as f:
            img_hash = hashlib.md5(f.read()).hexdigest()
    except Exception as e:
        print(f"Error calculating image hash: {e}")
    
    cache_path = os.path.join(cache_dir, f"{img_hash}.json")
    
    # 캐시 확인
    if img_hash and os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                print(f"Using cached image analysis for: {image_path}")
                return cached_data.get("keywords", [])
        except Exception as e:
            print(f"Error loading image analysis cache: {e}")
    
    print(f"Analyzing image content and emotions: {image_path}")
    
    try:
        # 이미지 유효성 검사
        img = Image.open(image_path)
        if img.width < 100 or img.height < 100:
            print(f"Image too small for analysis: {img.width}x{img.height}")
            return ["image", "visual", "graphic"]
        
        # OpenAI 클라이언트 초기화 (필요할 때만)
        client = get_openai_client(api_key)
        if not client:
            print("OpenAI client initialization failed, using basic keywords")
            return ["image", "visual", "graphic", "scene", "character"]
        
        # 이미지를 base64로 인코딩
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # OpenAI API 호출
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "이 웹툰 이미지를 분석해서 감정과 분위기를 나타내는 키워드를 5-10개 추출해주세요."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=200
            )
            
            # 응답 텍스트 가져오기
            analysis_text = response.choices[0].message.content
            print(f"Image analysis result: {analysis_text[:100]}...")
            
        except Exception as api_error:
            print(f"OpenAI API error: {api_error}")
            # API 호출 실패 시 기본 키워드 반환
            return ["image", "visual", "scene", "character", "emotion"]
        
        # 감정 키워드 추출
        emotion_keywords = []
        
        # 한국어/영어 감정 키워드 목록
        emotion_terms = [
            'happy', 'sad', 'angry', 'surprised', 'scared', 'disgusted', 'confused', 
            'excited', 'worried', 'nervous', 'calm', 'relaxed', 'tense', 'frustrated',
            'joyful', 'depressed', 'anxious', 'content', 'disappointed', 'embarrassed',
            '행복', '슬픔', '분노', '놀람', '공포', '혐오', '혼란', '흥분', '걱정', '긴장',
            '평온', '편안', '불안', '좌절', '기쁨', '우울', '불안', '만족', '실망', '당황'
        ]
        
        # 행동 키워드 목록
        action_terms = [
            'smiling', 'crying', 'laughing', 'shouting', 'running', 'walking', 'fighting',
            'hugging', 'kissing', 'talking', 'whispering', 'sleeping', 'eating', 'drinking',
            '웃음', '울음', '달리기', '걷기', '싸움', '포옹', '키스', '대화', '속삭임', '잠', '식사'
        ]
        
        # 분위기 키워드 목록
        mood_terms = [
            'romantic', 'dramatic', 'mysterious', 'thrilling', 'peaceful', 'chaotic',
            'tense', 'comical', 'nostalgic', 'dreamy', 'nightmarish', 'magical',
            '로맨틱', '드라마틱', '미스터리', '스릴', '평화로운', '혼란스러운',
            '긴장된', '코믹', '향수', '꿈같은', '악몽', '마법'
        ]
        
        # 분석 텍스트에서 키워드 추출
        if analysis_text:
            for term in emotion_terms + action_terms + mood_terms:
                if term.lower() in analysis_text.lower():
                    emotion_keywords.append(term.lower())
            
            # 분석 텍스트에서 직접 키워드 추출 (콜론 뒤에 오는 단어들)
            if "keywords:" in analysis_text.lower() or "키워드:" in analysis_text.lower():
                keyword_section = analysis_text.lower().split("keywords:")[1] if "keywords:" in analysis_text.lower() else analysis_text.lower().split("키워드:")[1]
                extracted_keywords = [k.strip() for k in keyword_section.split(",")]
                emotion_keywords.extend([k for k in extracted_keywords if k and len(k) > 1])
        
        # 기본 이미지 특성 추출
        try:
            width, height = img.size
            aspect_ratio = width / height
            
            # 이미지 크기에 따른 키워드
            size_keywords = []
            if width > 1000:
                size_keywords.append("high_resolution")
            if aspect_ratio > 1.5:
                size_keywords.append("wide_format")
            elif aspect_ratio < 0.7:
                size_keywords.append("vertical_format")
            
            # 이미지 모드에 따른 키워드
            mode_keywords = []
            if img.mode == "L":
                mode_keywords.append("black_and_white")
            elif img.mode == "RGB":
                mode_keywords.append("color")
        except Exception as img_error:
            print(f"Error analyzing image properties: {img_error}")
            size_keywords = []
            mode_keywords = []
        
        # 모든 키워드 결합
        all_keywords = emotion_keywords + size_keywords + mode_keywords + ["visual", "graphic"]
        
        # 중복 제거
        all_keywords = list(set(all_keywords))
        
        # 키워드가 너무 적으면 기본 키워드 추가
        if len(all_keywords) < 5:
            all_keywords.extend(["scene", "character", "emotion", "story", "webtoon"])
            all_keywords = list(set(all_keywords))
        
        # 캐시에 결과 저장
        if img_hash:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump({"keywords": all_keywords, "analysis": analysis_text}, f, ensure_ascii=False, indent=2)
            except Exception as cache_error:
                print(f"Error saving to cache: {cache_error}")
        
        return all_keywords
    except Exception as e:
        print(f"Error analyzing image: {e}")
        traceback.print_exc()
        return ["image", "visual", "scene", "character", "emotion"]

def extract_keywords(content, content_type='webtoon', api_key=None, num_keywords=15):
    """
    콘텐츠에서 키워드와 분위기를 추출합니다.
    
    Args:
        content (dict): 콘텐츠 정보
        content_type (str): 콘텐츠 타입 ('webtoon' 또는 'novel')
        api_key (str): OpenAI API 키 (선택 사항)
        num_keywords (int): 추출할 키워드 수
        
    Returns:
        tuple: (키워드 리스트, 장르, 분위기, 시대 배경, 음악 스타일)
    """
    print(f"Extracting detailed keywords and mood from {content_type} content...")
    
    try:
        # KeyBERT 모델 초기화
        kw_model = KeyBERT()
        client = get_openai_client(api_key) if api_key else None
        
        # 텍스트 추출
        if content_type == 'webtoon':
            text = ' '.join(content['texts'])
            
            # 오류 메시지 포함 여부 확인
            if 'error' in text.lower() or 'exception' in text.lower():
                print("Error messages detected in text, using title and author only")
                text = f"{content['title']} {content['author']}"
                
            if not text.strip():
                # 텍스트가 없으면 제목과 작가 정보 사용
                text = f"{content['title']} {content['author']}"
            
            # 이미지 분석을 통한 추가 키워드 추출
            image_keywords = []
            
            # 그룹 이미지 분석 (5개씩 묶은 이미지)
            if 'group_image_paths' in content and content['group_image_paths']:
                group_keywords = []
                for group_path in content['group_image_paths']:
                    if os.path.exists(group_path):
                        try:
                            # 그룹 이미지 분석
                            group_img_keywords = analyze_image_content(group_path, api_key)
                            group_keywords.extend(group_img_keywords)
                            print(f"Keywords from group image analysis: {group_img_keywords}")
                        except Exception as group_error:
                            print(f"Error in group image analysis: {group_error}")
                
                # 중복 제거
                image_keywords = list(set(group_keywords))
            
            # 그룹 이미지가 없거나 분석 실패한 경우 전체 이미지 분석
            if not image_keywords and 'combined_image_path' in content and content['combined_image_path'] and os.path.exists(content['combined_image_path']):
                try:
                    image_keywords = analyze_image_content(content['combined_image_path'], api_key)
                    print(f"Keywords from combined image analysis: {image_keywords}")
                except Exception as img_error:
                    print(f"Error in combined image analysis: {img_error}")
        else:  # novel
            text = content['full_text']
            image_keywords = []  # 웹소설은 이미지가 없으므로 빈 리스트
        
        # 텍스트 전처리
        text = text.lower()
        
        # 한국어 텍스트 처리
        is_korean_dominant = sum(1 for char in text if ord('가') <= ord(char) <= ord('힣')) > len(text) / 3
        
        # KoNLPy 사용 여부 결정 (오류 방지)
        use_konlpy = KONLPY_AVAILABLE and is_korean_dominant
        
        if use_konlpy:
            # 한국어 형태소 분석
            try:
                # 전역 변수로 초기화된 Okt 인스턴스 사용
                tokens = okt_initialized.morphs(text)
                processed_text = ' '.join(tokens)
                
                # 한국어 불용어 설정 (확장)
                korean_stop_words = {
                    '이', '그', '저', '것', '이것', '저것', '그것', '및', '등', '등등',
                    '나', '너', '우리', '저희', '당신', '그들', '그녀', '이런', '저런', '그런',
                    '하다', '되다', '있다', '없다', '같다', '보다', '이다', '아니다',
                    '그리고', '또는', '그러나', '하지만', '또한', '그래서', '왜냐하면',
                    '에러', '오류', '에러가', '오류가', 'error', 'exception'  # 오류 관련 단어 추가
                }
                
                # 키워드 추출
                keywords = kw_model.extract_keywords(
                    processed_text,
                    keyphrase_ngram_range=(1, 2),
                    stop_words=list(korean_stop_words),
                    use_mmr=True,
                    diversity=0.7,
                    top_n=num_keywords
                )
            except Exception as e:
                print(f"Error in Korean text processing: {e}")
                # 오류 발생 시 영어 처리 방식으로 대체
                use_konlpy = False
        
        if not use_konlpy:
            # 영어 및 기타 언어 처리
            # 특수 문자 제거
            text = re.sub(r'[^\w\s]', '', text)
            
            # 영어 불용어 설정
            stop_words = set(stopwords.words('english'))
            # 오류 관련 단어 추가
            error_words = {'error', 'exception', 'traceback', 'failed', 'failure', 'broken'}
            stop_words.update(error_words)
            
            # 키워드 추출
            keywords = kw_model.extract_keywords(
                text, 
                keyphrase_ngram_range=(1, 2), 
                stop_words=list(stop_words),
                use_mmr=True,
                diversity=0.7,
                top_n=num_keywords
            )
        
        # 키워드와 점수 분리
        keyword_list = [keyword for keyword, _ in keywords]
        
        # 오류 관련 키워드 필터링
        error_related = ['error', 'exception', 'traceback', 'failed', 'failure', 'broken', 'cannot', 'could not', 'not found', 'missing']
        keyword_list = [k for k in keyword_list if not any(err in k.lower() for err in error_related)]
        
        # 이미지 키워드 추가
        keyword_list.extend(image_keywords)
        
        # 웹툰/웹소설 장르 분류 (확장된 장르 목록)
        genre_keywords = {
            'romance': ['love', 'romance', 'relationship', 'couple', 'dating', '사랑', '연애', '로맨스', '커플', '연인'],
            'action': ['fight', 'battle', 'action', 'war', 'combat', '전투', '액션', '싸움', '전쟁', '격투'],
            'fantasy': ['magic', 'dragon', 'wizard', 'elf', 'fantasy', '마법', '판타지', '용', '마법사', '요정'],
            'horror': ['ghost', 'zombie', 'horror', 'scary', 'fear', '귀신', '공포', '좀비', '무서움', '두려움'],
            'comedy': ['funny', 'comedy', 'laugh', 'humor', 'joke', '코미디', '웃음', '유머', '재미', '농담'],
            'thriller': ['suspense', 'mystery', 'crime', 'detective', '스릴러', '서스펜스', '미스터리', '범죄', '탐정'],
            'sci-fi': ['future', 'space', 'alien', 'robot', 'technology', '미래', '우주', '외계인', '로봇', '기술'],
            'slice_of_life': ['daily', 'life', 'school', 'ordinary', '일상', '학교', '생활', '평범한', '일상생활'],
            'historical': ['history', 'dynasty', 'kingdom', 'ancient', 'period', '역사', '왕조', '왕국', '고대', '시대극'],
            'sports': ['sports', 'game', 'competition', 'athlete', 'team', '스포츠', '경기', '선수', '팀', '대회'],
            'drama': ['drama', 'emotional', 'family', 'conflict', 'tragedy', '드라마', '감정', '가족', '갈등', '비극'],
            'supernatural': ['ghost', 'spirit', 'psychic', 'paranormal', '초자연', '영혼', '귀신', '초능력', '신비']
        }
        
        # 분위기 분류 (더 세분화된 분위기 목록)
        mood_keywords = {
            'happy': ['happy', 'joy', 'laugh', 'cheerful', 'bright', '행복', '기쁨', '웃음', '명랑', '밝음'],
            'sad': ['sad', 'cry', 'tear', 'sorrow', 'melancholy', '슬픔', '눈물', '아픔', '우울', '비통'],
            'exciting': ['exciting', 'thrill', 'adventure', 'dynamic', 'intense', '흥미', '모험', '스릴', '역동적', '강렬'],
            'scary': ['scary', 'horror', 'fear', 'terror', 'dread', '공포', '두려움', '무서움', '공포감', '전율'],
            'romantic': ['love', 'romance', 'kiss', 'heart', 'affection', '사랑', '로맨스', '키스', '애정', '설렘'],
            'mysterious': ['mystery', 'secret', 'puzzle', 'enigma', 'curious', '미스터리', '비밀', '수수께끼', '의문', '호기심'],
            'peaceful': ['peace', 'calm', 'quiet', 'relax', 'serene', '평화', '고요', '휴식', '평온', '차분'],
            'tense': ['tension', 'anxiety', 'nervous', 'suspense', 'stress', '긴장', '불안', '초조', '서스펜스', '스트레스'],
            'nostalgic': ['nostalgia', 'memory', 'reminisce', 'past', 'childhood', '향수', '추억', '회상', '과거', '어린 시절'],
            'epic': ['epic', 'grand', 'majestic', 'magnificent', 'heroic', '서사시', '웅장', '장엄', '영웅적', '대서사'],
            'comical': ['funny', 'comedy', 'humorous', 'witty', 'silly', '코믹', '유머', '재미있는', '익살', '우스운'],
            'dreamy': ['dream', 'fantasy', 'surreal', 'ethereal', 'magical', '꿈같은', '환상적', '초현실적', '신비로운', '마법같은']
        }
        
        # 시대 배경 분류
        era_keywords = {
            'modern': ['modern', 'contemporary', 'today', 'present', 'current', '현대', '현재', '요즘', '지금', '현시대'],
            'future': ['future', 'futuristic', 'sci-fi', 'advanced', 'dystopian', '미래', '미래적', 'SF', '첨단', '디스토피아'],
            'medieval': ['medieval', 'castle', 'knight', 'kingdom', 'sword', '중세', '성', '기사', '왕국', '검'],
            'ancient': ['ancient', 'historical', 'old', 'traditional', 'classic', '고대', '역사적', '옛날', '전통적', '고전'],
            'prehistoric': ['prehistoric', 'dinosaur', 'primitive', 'caveman', '선사시대', '공룡', '원시', '동굴인'],
            'victorian': ['victorian', '19th century', 'industrial', '빅토리아', '19세기', '산업혁명'],
            'renaissance': ['renaissance', 'baroque', 'artistic', '르네상스', '바로크', '예술적'],
            'post_apocalyptic': ['apocalypse', 'post-apocalyptic', 'ruins', 'wasteland', '종말', '포스트 아포칼립스', '폐허', '황무지']
        }
        
        # 음악 스타일 분류
        music_style_keywords = {
            'orchestral': ['orchestra', 'symphony', 'classical', 'epic', 'grand', '오케스트라', '교향곡', '클래식', '웅장한'],
            'electronic': ['electronic', 'synth', 'techno', 'digital', 'edm', '일렉트로닉', '신스', '테크노', '디지털', 'EDM'],
            'acoustic': ['acoustic', 'guitar', 'piano', 'soft', 'unplugged', '어쿠스틱', '기타', '피아노', '부드러운'],
            'rock': ['rock', 'guitar', 'band', 'electric', 'heavy', '록', '기타', '밴드', '일렉트릭', '헤비'],
            'jazz': ['jazz', 'saxophone', 'trumpet', 'swing', 'blues', '재즈', '색소폰', '트럼펫', '스윙', '블루스'],
            'pop': ['pop', 'catchy', 'upbeat', 'mainstream', 'melody', '팝', '캐치한', '경쾌한', '대중적인', '멜로디'],
            'ambient': ['ambient', 'atmospheric', 'background', 'calm', 'space', '앰비언트', '대기적', '배경', '고요한', '공간감'],
            'folk': ['folk', 'traditional', 'acoustic', 'country', 'ballad', '포크', '전통적', '어쿠스틱', '컨트리', '발라드'],
            'cinematic': ['cinematic', 'soundtrack', 'film', 'score', 'theme', '영화음악', '사운드트랙', '영화', '스코어', '테마'],
            'hip_hop': ['hip hop', 'rap', 'beat', 'urban', 'rhythm', '힙합', '랩', '비트', '어반', '리듬'],
            'lo_fi': ['lo-fi', 'chill', 'relaxed', 'mellow', 'calm', '로파이', '칠', '편안한', '차분한']
        }
        
        # 텍스트에서 각 카테고리별 키워드 빈도 계산
        genre_scores = {genre: 0 for genre in genre_keywords}
        mood_scores = {mood: 0 for mood in mood_keywords}
        era_scores = {era: 0 for era in era_keywords}
        music_style_scores = {style: 0 for style in music_style_keywords}
        
        # 장르 점수 계산
        for genre, words in genre_keywords.items():
            for word in words:
                if word in text.lower():
                    genre_scores[genre] += text.lower().count(word)
        
        # 분위기 점수 계산
        for mood, words in mood_keywords.items():
            for word in words:
                if word in text.lower():
                    mood_scores[mood] += text.lower().count(word)
        
        # 시대 배경 점수 계산
        for era, words in era_keywords.items():
            for word in words:
                if word in text.lower():
                    era_scores[era] += text.lower().count(word)
        
        # 음악 스타일 점수 계산
        for style, words in music_style_keywords.items():
            for word in words:
                if word in text.lower():
                    music_style_scores[style] += text.lower().count(word)
        
        # 가장 높은 점수의 카테고리 선택
        dominant_genre = max(genre_scores, key=genre_scores.get) if any(genre_scores.values()) else 'slice_of_life'
        dominant_mood = max(mood_scores, key=mood_scores.get) if any(mood_scores.values()) else 'peaceful'
        dominant_era = max(era_scores, key=era_scores.get) if any(era_scores.values()) else 'modern'
        dominant_music_style = max(music_style_scores, key=music_style_scores.get) if any(music_style_scores.values()) else 'cinematic'
        
        # 결과 출력
        print(f"Extracted {len(keyword_list)} keywords")
        print(f"Detected genre: {dominant_genre}")
        print(f"Detected mood: {dominant_mood}")
        print(f"Detected era: {dominant_era}")
        print(f"Suggested music style: {dominant_music_style}")
        
        # 장르와 분위기에 따른 추가 키워드 생성
        additional_keywords = []
        
        # 장르별 특성 키워드 추가
        genre_specific_keywords = {
            'romance': ['emotional', 'sweet', 'tender', 'intimate'],
            'action': ['powerful', 'dynamic', 'energetic', 'strong'],
            'fantasy': ['magical', 'mystical', 'enchanting', 'wondrous'],
            'horror': ['eerie', 'dark', 'haunting', 'sinister'],
            'comedy': ['light', 'playful', 'whimsical', 'cheerful'],
            'thriller': ['tense', 'suspenseful', 'gripping', 'mysterious'],
            'sci-fi': ['futuristic', 'technological', 'innovative', 'otherworldly'],
            'slice_of_life': ['gentle', 'everyday', 'simple', 'natural'],
            'historical': ['traditional', 'noble', 'ancient', 'cultural'],
            'sports': ['energetic', 'competitive', 'triumphant', 'spirited'],
            'drama': ['emotional', 'moving', 'poignant', 'heartfelt'],
            'supernatural': ['mysterious', 'otherworldly', 'magical', 'ethereal']
        }
        
        # 분위기별 특성 키워드 추가
        mood_specific_keywords = {
            'happy': ['bright', 'uplifting', 'joyful', 'cheerful'],
            'sad': ['melancholic', 'somber', 'emotional', 'touching'],
            'exciting': ['thrilling', 'energetic', 'dynamic', 'powerful'],
            'scary': ['dark', 'ominous', 'tense', 'eerie'],
            'romantic': ['tender', 'emotional', 'intimate', 'warm'],
            'mysterious': ['intriguing', 'enigmatic', 'puzzling', 'curious'],
            'peaceful': ['serene', 'calm', 'gentle', 'soothing'],
            'tense': ['suspenseful', 'anxious', 'uneasy', 'dramatic'],
            'nostalgic': ['reminiscent', 'wistful', 'reflective', 'sentimental'],
            'epic': ['grand', 'majestic', 'powerful', 'heroic'],
            'comical': ['playful', 'light', 'quirky', 'amusing'],
            'dreamy': ['ethereal', 'floating', 'surreal', 'magical']
        }
        
        # 시대별 특성 키워드 추가
        era_specific_keywords = {
            'modern': ['contemporary', 'urban', 'current', 'today'],
            'future': ['futuristic', 'advanced', 'technological', 'innovative'],
            'medieval': ['ancient', 'traditional', 'historical', 'old-world'],
            'ancient': ['classical', 'timeless', 'historical', 'traditional'],
            'prehistoric': ['primitive', 'primal', 'ancient', 'raw'],
            'victorian': ['elegant', 'refined', 'classical', 'traditional'],
            'renaissance': ['artistic', 'cultural', 'classical', 'refined'],
            'post_apocalyptic': ['desolate', 'barren', 'ruined', 'abandoned']
        }
        
        # 음악 스타일별 특성 키워드 추가
        music_style_specific_keywords = {
            'orchestral': ['grand', 'majestic', 'powerful', 'rich'],
            'electronic': ['modern', 'digital', 'synthetic', 'pulsating'],
            'acoustic': ['natural', 'organic', 'warm', 'intimate'],
            'rock': ['energetic', 'powerful', 'driving', 'strong'],
            'jazz': ['smooth', 'sophisticated', 'complex', 'improvisational'],
            'pop': ['catchy', 'upbeat', 'melodic', 'contemporary'],
            'ambient': ['atmospheric', 'spacious', 'ethereal', 'subtle'],
            'folk': ['traditional', 'authentic', 'rustic', 'simple'],
            'cinematic': ['dramatic', 'emotional', 'powerful', 'thematic'],
            'hip_hop': ['rhythmic', 'urban', 'cool', 'contemporary'],
            'lo_fi': ['relaxed', 'mellow', 'nostalgic', 'warm']
        }
        
        # 주요 카테고리에서 추가 키워드 선택
        if dominant_genre in genre_specific_keywords:
            additional_keywords.extend(genre_specific_keywords[dominant_genre])
        
        if dominant_mood in mood_specific_keywords:
            additional_keywords.extend(mood_specific_keywords[dominant_mood])
        
        if dominant_era in era_specific_keywords:
            additional_keywords.extend(era_specific_keywords[dominant_era])
        
        if dominant_music_style in music_style_specific_keywords:
            additional_keywords.extend(music_style_specific_keywords[dominant_music_style])
        
        # 중복 제거
        additional_keywords = list(set(additional_keywords))
        
        # 키워드 리스트에 추가
        keyword_list.extend(additional_keywords)
        
        # 키워드가 너무 적으면 기본 키워드 추가
        if len(keyword_list) < 5:
            keyword_list.extend(["story", "character", "scene", "emotion", "narrative"])
        
        # 중복 제거 및 상위 키워드 선택
        final_keywords = list(dict.fromkeys(keyword_list))[:num_keywords]
        
        return final_keywords, dominant_genre, dominant_mood, dominant_era, dominant_music_style
    
    except Exception as e:
        print(f"Error in keyword extraction: {e}")
        traceback.print_exc()
        # 오류 발생 시 기본값 반환 (웹툰/웹소설 관련 키워드)
        return ["story", "character", "narrative", "scene", "emotion", "drama", "adventure", "fantasy", "mystery", "journey"], "slice_of_life", "peaceful", "modern", "cinematic"

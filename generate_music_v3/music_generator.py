from transformers import AutoProcessor, MusicgenForConditionalGeneration
import torch
import scipy.io.wavfile
import numpy as np
import os
import random
from pydub import AudioSegment
import hashlib
import json

def generate_music(keywords, genre, mood, era, music_style, output_path, use_cache=True):
    """
    키워드와 분위기를 기반으로 3분 길이의 음악을 생성합니다.
    
    Args:
        keywords (list): 키워드 리스트
        genre (str): 장르
        mood (str): 분위기
        era (str): 시대 배경
        music_style (str): 음악 스타일
        output_path (str): 출력 파일 경로
        use_cache (bool): 캐시 사용 여부
        
    Returns:
        str: 생성된 음악 파일 경로
    """
    print("Generating 3-minute music based on content analysis...")
    
    # 출력 디렉토리 확인 및 생성
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 캐시 디렉토리 확인
    cache_dir = os.path.join("cache", "music")
    os.makedirs(cache_dir, exist_ok=True)
    
    # 입력 파라미터를 기반으로 캐시 키 생성
    cache_key = f"{'-'.join(keywords[:5])}-{genre}-{mood}-{era}-{music_style}"
    cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()
    cache_path = os.path.join(cache_dir, f"{cache_key_hash}.wav")
    metadata_path = os.path.join(cache_dir, f"{cache_key_hash}_metadata.json")
    
    # 캐시 확인
    if use_cache and os.path.exists(cache_path) and os.path.exists(metadata_path):
        try:
            # 메타데이터 확인
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                print(f"Using cached music for: {metadata.get('prompt', 'Unknown prompt')}")
            
            # 캐시된 음악 파일 복사
            audio = AudioSegment.from_wav(cache_path)
            audio.export(output_path, format="wav")
            
            # 메타데이터 파일 생성 (출력 디렉토리에)
            output_metadata_path = output_path.replace('.wav', '_metadata.txt')
            with open(output_metadata_path, 'w', encoding='utf-8') as f:
                f.write(f"Generated Music Metadata (from cache)\n")
                f.write(f"----------------------\n")
                f.write(f"Keywords: {', '.join(keywords)}\n")
                f.write(f"Genre: {genre}\n")
                f.write(f"Mood: {mood}\n")
                f.write(f"Era: {era}\n")
                f.write(f"Music Style: {music_style}\n")
                f.write(f"Base Prompt: {metadata.get('prompt', 'Unknown')}\n")
            
            print(f"Music loaded from cache and saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error loading music cache: {e}")
    
    # 키워드를 문자열로 변환 (상위 5개만)
    keywords_str = ', '.join(keywords[:5])
    
    # 장르별 음악 스타일 매핑
    genre_style_map = {
        'romance': 'emotional and tender melody with soft instrumentation',
        'action': 'energetic and powerful music with strong percussion and dynamic rhythm',
        'fantasy': 'magical and enchanting composition with mystical elements',
        'horror': 'eerie and tense atmospheric music with dissonant tones',
        'comedy': 'light and playful melody with quirky elements',
        'thriller': 'suspenseful music with building tension and dramatic moments',
        'sci-fi': 'futuristic electronic sounds with innovative textures',
        'slice_of_life': 'gentle and simple melody reflecting everyday moments',
        'historical': 'traditional instrumentation with cultural elements',
        'sports': 'energetic and triumphant music with motivational elements',
        'drama': 'emotional and moving composition with heartfelt melody',
        'supernatural': 'mysterious and otherworldly sounds with ethereal elements'
    }
    
    # 분위기별 음악 특성 매핑
    mood_style_map = {
        'happy': 'upbeat and cheerful with bright tones',
        'sad': 'melancholic and emotional with minor key progression',
        'exciting': 'thrilling and dynamic with energetic rhythm',
        'scary': 'dark and ominous with unsettling elements',
        'romantic': 'tender and intimate with warm harmonies',
        'mysterious': 'intriguing and enigmatic with curious progression',
        'peaceful': 'calm and serene with gentle flow',
        'tense': 'suspenseful and anxious with building intensity',
        'nostalgic': 'wistful and sentimental with reflective quality',
        'epic': 'grand and majestic with powerful dynamics',
        'comical': 'playful and light with quirky elements',
        'dreamy': 'ethereal and floating with surreal quality'
    }
    
    # 시대별 음악 특성 매핑
    era_style_map = {
        'modern': 'contemporary sound with current production techniques',
        'future': 'futuristic electronic elements with advanced sound design',
        'medieval': 'ancient instruments and traditional melodies',
        'ancient': 'classical elements with timeless quality',
        'prehistoric': 'primitive percussion and primal sounds',
        'victorian': 'elegant classical instrumentation with refined quality',
        'renaissance': 'artistic classical arrangements with cultural elements',
        'post_apocalyptic': 'desolate atmosphere with sparse instrumentation'
    }
    
    # 음악 스타일별 특성 매핑
    music_style_map = {
        'orchestral': 'grand orchestral arrangement with rich instrumentation',
        'electronic': 'modern electronic production with digital elements',
        'acoustic': 'natural acoustic instruments with organic quality',
        'rock': 'electric guitars and drums with strong energy',
        'jazz': 'smooth jazz elements with sophisticated harmonies',
        'pop': 'catchy pop melody with contemporary production',
        'ambient': 'atmospheric textures with spacious sound design',
        'folk': 'traditional folk instruments with authentic feel',
        'cinematic': 'dramatic film score style with emotional impact',
        'hip_hop': 'rhythmic beats with urban feel',
        'lo_fi': 'relaxed lo-fi beats with warm nostalgic quality'
    }
    
    # 장르와 분위기에 맞는 스타일 선택
    genre_style = genre_style_map.get(genre, 'melodic instrumental music')
    mood_style = mood_style_map.get(mood, 'emotional and expressive')
    era_style = era_style_map.get(era, 'contemporary sound')
    music_style_desc = music_style_map.get(music_style, 'cinematic instrumental music')
    
    # 고정된 세그먼트 수 (3분 = 6개 세그먼트)
    num_segments = 6
    
    # 각 세그먼트에 대한 최대 토큰 수 (약 30초)
    max_tokens = 1000
    
    try:
        # MusicGen 모델 로드
        processor = AutoProcessor.from_pretrained("facebook/musicgen-small")
        model = MusicgenForConditionalGeneration.from_pretrained("facebook/musicgen-small")
        
        # 메모리 사용량 최적화를 위한 설정
        if torch.cuda.is_available():
            model = model.to("cuda")
        
        # 출력 디렉토리 확인 및 생성
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 여러 세그먼트 생성 및 연결
        combined_audio = None
        sampling_rate = 16000  # MusicGen의 샘플링 레이트
        
        print(f"Generating 6 segments for a 3-minute music piece...")
        
        # 프롬프트 템플릿 (기본 템플릿)
        base_prompt_templates = [
            f"{genre_style} with {mood_style}, {music_style_desc}, inspired by themes of {keywords_str}, no vocals",
            f"{music_style_desc} that feels {mood_style}, with elements of {genre_style}, inspired by {keywords_str}, instrumental",
            f"{era_style} {music_style_desc} with {mood_style} atmosphere, related to {keywords_str}, no lyrics",
            f"An instrumental {music_style_desc} piece that captures {mood_style} and {genre_style}, inspired by {keywords_str}"
        ]
        
        # 기본 프롬프트 선택
        base_prompt = random.choice(base_prompt_templates)
        print(f"Base prompt: {base_prompt}")
        
        for i in range(num_segments):
            # 각 세그먼트에 약간의 변형 추가
            segment_descriptors = [
                "intro", "building", "main theme", "variation", "bridge", "outro"
            ]
            
            # 현재 세그먼트에 맞는 프롬프트 생성
            prompt = f"{base_prompt}, {segment_descriptors[i]} section"
            print(f"Generating segment {i+1}/6: {segment_descriptors[i]}")
            
            # 텍스트 프롬프트 처리
            inputs = processor(
                text=[prompt],
                padding=True,
                return_tensors="pt",
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # 음악 세그먼트 생성
            audio_values = model.generate(**inputs, do_sample=True, guidance_scale=3, max_new_tokens=max_tokens)
            
            # 모델이 GPU에 있다면 CPU로 이동
            if torch.cuda.is_available():
                audio_values = audio_values.cpu()
            
            # 현재 세그먼트를 임시 파일로 저장
            temp_segment_path = f"{output_path}_segment_{i+1}.wav"
            scipy.io.wavfile.write(temp_segment_path, rate=sampling_rate, data=audio_values[0, 0].numpy())
            
            # 세그먼트를 AudioSegment로 로드
            segment = AudioSegment.from_wav(temp_segment_path)
            
            # 첫 번째 세그먼트이거나 이전 세그먼트와 연결
            if combined_audio is None:
                combined_audio = segment
            else:
                # 크로스페이드로 자연스럽게 연결 (1초 = 1000ms)
                crossfade_duration = 1000  # 1초 크로스페이드
                combined_audio = combined_audio.append(segment, crossfade=crossfade_duration)
            
            # 임시 파일 삭제
            os.remove(temp_segment_path)
        
        # 최종 오디오 저장
        combined_audio.export(output_path, format="wav")
        
        # 캐시에 오디오 저장
        if use_cache:
            combined_audio.export(cache_path, format="wav")
            
            # 메타데이터 저장
            cache_metadata = {
                "keywords": keywords,
                "genre": genre,
                "mood": mood,
                "era": era,
                "music_style": music_style,
                "prompt": base_prompt,
                "duration": "3 minutes (6 segments)"
            }
            
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(cache_metadata, f, ensure_ascii=False, indent=2)
        
        # 메타데이터 저장 (출력 파일용)
        output_metadata_path = output_path.replace('.wav', '_metadata.txt')
        with open(output_metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"Generated Music Metadata\n")
            f.write(f"----------------------\n")
            f.write(f"Keywords: {', '.join(keywords)}\n")
            f.write(f"Genre: {genre}\n")
            f.write(f"Mood: {mood}\n")
            f.write(f"Era: {era}\n")
            f.write(f"Music Style: {music_style}\n")
            f.write(f"Duration: 3 minutes (6 segments)\n")
            f.write(f"Base Prompt: {base_prompt}\n")
        
        print(f"3-minute music successfully generated and saved to {output_path}")
        print(f"Metadata saved to {output_metadata_path}")
        
        return output_path
        
    except Exception as e:
        print(f"Error generating music: {e}")
        return None

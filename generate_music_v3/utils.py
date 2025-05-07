# Matplotlib 백엔드를 'Agg'로 설정 (GUI 없는 백엔드)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import numpy as np
from PIL import Image
import os
import hashlib
import json
import traceback

def visualize_keywords(keywords, output_path='keywords_visualization.png', use_cache=True):
    """
    추출된 키워드를 시각화합니다.
    
    Args:
        keywords (list): 키워드 리스트
        output_path (str): 출력 이미지 경로
        use_cache (bool): 캐시 사용 여부
    """
    try:
        # 캐시 디렉토리 확인
        cache_dir = os.path.join("cache", "visualizations")
        os.makedirs(cache_dir, exist_ok=True)
        
        # 키워드 리스트를 기반으로 캐시 키 생성
        keywords_str = '-'.join(sorted(keywords))
        cache_key = hashlib.md5(keywords_str.encode()).hexdigest()
        cache_path = os.path.join(cache_dir, f"{cache_key}.png")
        
        # 캐시 확인
        if use_cache and os.path.exists(cache_path):
            try:
                # 캐시된 이미지 파일 복사
                img = Image.open(cache_path)
                img.save(output_path)
                print(f"Keyword visualization loaded from cache and saved to {output_path}")
                return output_path
            except Exception as e:
                print(f"Error loading visualization cache: {e}")
        
        # 키워드 빈도 계산
        keyword_counts = {}
        for keyword in keywords:
            if keyword in keyword_counts:
                keyword_counts[keyword] += 1
            else:
                keyword_counts[keyword] = 1
        
        # 상위 10개 키워드 선택
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        if not top_keywords:
            print("No keywords to visualize")
            # 빈 이미지 생성
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, "No keywords available", ha='center', va='center', fontsize=14)
            plt.axis('off')
            plt.savefig(output_path)
            plt.close()
            return output_path
        
        # 시각화
        plt.figure(figsize=(10, 6))
        plt.bar([kw for kw, _ in top_keywords], [count for _, count in top_keywords])
        plt.xlabel('Keywords')
        plt.ylabel('Frequency')
        plt.title('Top Keywords')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 이미지 저장
        plt.savefig(output_path)
        
        # 캐시에 저장
        if use_cache:
            plt.savefig(cache_path)
        
        plt.close()
        
        print(f"Keyword visualization saved to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error in keyword visualization: {e}")
        traceback.print_exc()
        
        # 오류 발생 시 빈 이미지 생성
        try:
            plt.figure(figsize=(10, 6))
            plt.text(0.5, 0.5, f"Visualization error: {str(e)}", ha='center', va='center', fontsize=14)
            plt.axis('off')
            plt.savefig(output_path)
            plt.close()
        except:
            pass
        
        return output_path

def save_webtoon_images(images, output_dir='webtoon_images'):
    """
    웹툰 이미지를 저장합니다.
    
    Args:
        images (list): 이미지 객체 리스트
        output_dir (str): 출력 디렉토리
    """
    try:
        # 디렉토리 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 이미지 저장
        saved_paths = []
        for i, img in enumerate(images):
            output_path = os.path.join(output_dir, f'image_{i+1}.jpg')
            img.save(output_path)
            saved_paths.append(output_path)
        
        return saved_paths
    except Exception as e:
        print(f"Error saving webtoon images: {e}")
        traceback.print_exc()
        return []

def combine_audio_files(audio_files, output_path, crossfade_duration=1000):
    """
    여러 오디오 파일을 하나로 합칩니다.
    
    Args:
        audio_files (list): 오디오 파일 경로 리스트
        output_path (str): 출력 파일 경로
        crossfade_duration (int): 크로스페이드 시간(ms)
    
    Returns:
        str: 합쳐진 오디오 파일 경로
    """
    try:
        if not audio_files:
            return None
        
        from pydub import AudioSegment
        
        # 첫 번째 오디오 파일 로드
        combined = AudioSegment.from_file(audio_files[0])
        
        # 나머지 오디오 파일 추가
        for audio_file in audio_files[1:]:
            next_segment = AudioSegment.from_file(audio_file)
            combined = combined.append(next_segment, crossfade=crossfade_duration)
        
        # 결과 저장
        combined.export(output_path, format="wav")
        
        return output_path
    except Exception as e:
        print(f"Error combining audio files: {e}")
        traceback.print_exc()
        return None

def normalize_audio(input_path, output_path=None, target_dBFS=-20.0):
    """
    오디오 파일의 볼륨을 정규화합니다.
    
    Args:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로 (None이면 입력 파일 덮어쓰기)
        target_dBFS (float): 목표 dBFS 값
    
    Returns:
        str: 정규화된 오디오 파일 경로
    """
    try:
        from pydub import AudioSegment
        
        if output_path is None:
            output_path = input_path
        
        # 오디오 로드
        sound = AudioSegment.from_file(input_path)
        
        # 현재 dBFS 계산
        change_in_dBFS = target_dBFS - sound.dBFS
        
        # 볼륨 조정
        normalized_sound = sound.apply_gain(change_in_dBFS)
        
        # 결과 저장
        normalized_sound.export(output_path, format="wav")
        
        return output_path
    except Exception as e:
        print(f"Error normalizing audio: {e}")
        traceback.print_exc()
        return input_path

def create_audio_preview(input_path, output_path=None, duration=30000):
    """
    오디오 파일의 미리듣기 버전을 생성합니다.
    
    Args:
        input_path (str): 입력 오디오 파일 경로
        output_path (str): 출력 오디오 파일 경로 (None이면 자동 생성)
        duration (int): 미리듣기 길이(ms)
    
    Returns:
        str: 미리듣기 오디오 파일 경로
    """
    try:
        from pydub import AudioSegment
        
        if output_path is None:
            output_path = input_path.replace('.wav', '_preview.wav')
        
        # 오디오 로드
        sound = AudioSegment.from_file(input_path)
        
        # 미리듣기 길이가 원본보다 길면 원본 길이로 조정
        if len(sound) < duration:
            duration = len(sound)
        
        # 미리듣기 생성 (시작 부분부터)
        preview = sound[:duration]
        
        # 페이드 아웃 효과 추가
        preview = preview.fade_out(2000)
        
        # 결과 저장
        preview.export(output_path, format="wav")
        
        return output_path
    except Exception as e:
        print(f"Error creating audio preview: {e}")
        traceback.print_exc()
        return None

def clean_temp_files(directory=None, pattern="*_segment_*.wav"):
    """
    임시 파일을 정리합니다.
    
    Args:
        directory (str): 정리할 디렉토리 (None이면 현재 디렉토리)
        pattern (str): 파일 패턴
    """
    try:
        import glob
        
        if directory is None:
            directory = "."
        
        # 패턴에 맞는 파일 찾기
        files = glob.glob(os.path.join(directory, pattern))
        
        # 파일 삭제
        for file in files:
            try:
                os.remove(file)
                print(f"Removed temporary file: {file}")
            except Exception as e:
                print(f"Error removing file {file}: {e}")
    except Exception as e:
        print(f"Error cleaning temporary files: {e}")
        traceback.print_exc()

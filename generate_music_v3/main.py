import argparse
import os
import datetime
import uuid
import traceback
from webtoon_processor import extract_webtoon_content
from novel_processor import process_novel_file
from keyword_extractor import extract_keywords
from music_generator import generate_music
from utils import visualize_keywords

def create_output_directory(content_type, input_source):
    """
    테스트마다 고유한 출력 디렉토리를 생성합니다.
    
    Args:
        content_type (str): 콘텐츠 타입 ('webtoon' 또는 'novel')
        input_source (str): 입력 소스 (URL 또는 파일 경로)
        
    Returns:
        str: 생성된 출력 디렉토리 경로
    """
    # 현재 날짜와 시간을 포함한 디렉토리 이름 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 입력 소스에서 간단한 식별자 추출
    if content_type == 'webtoon':
        # URL에서 마지막 부분만 추출
        identifier = input_source.split('/')[-1].split('?')[0]
        if len(identifier) > 20:  # 너무 길면 잘라내기
            identifier = identifier[:20]
    else:  # novel
        # 파일 이름에서 확장자 제거
        identifier = os.path.basename(input_source).split('.')[0]
        if len(identifier) > 20:
            identifier = identifier[:20]
    
    # 고유 ID 추가 (충돌 방지)
    unique_id = str(uuid.uuid4())[:8]
    
    # 디렉토리 이름 생성 및 생성
    output_dir = f"output_{content_type}_{identifier}_{timestamp}_{unique_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Created output directory: {output_dir}")
    return output_dir

def main():
    try:
        parser = argparse.ArgumentParser(description='Generate music based on webtoon or web novel content')
        parser.add_argument('--type', choices=['webtoon', 'novel'], required=True, help='Content type: webtoon or novel')
        parser.add_argument('--input', required=True, help='URL for webtoon or file path for novel')
        parser.add_argument('--output', default=None, help='Output music file path (optional)')
        parser.add_argument('--use_cache', action='store_true', help='Use cached content if available')
        
        args = parser.parse_args()
        
        # 출력 디렉토리 생성
        output_dir = create_output_directory(args.type, args.input)
        
        # 출력 파일 경로 설정 (지정되지 않은 경우 자동 생성)
        if args.output is None:
            output_filename = f"generated_music.wav"
        else:
            output_filename = os.path.basename(args.output)
        
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Processing {args.type} content from {args.input}...")
        print(f"Output will be saved to: {output_path}")
        
        # 콘텐츠 처리
        if args.type == 'webtoon':
            # 웹툰 처리 시 이미지 저장 경로를 출력 디렉토리로 지정
            content = extract_webtoon_content(args.input, use_cache=args.use_cache, output_dir=output_dir)
            
            # 이미지 추출 성공 여부 확인
            if content['images']:
                print(f"Successfully extracted {len(content['images'])} images from webtoon")
            else:
                print("Failed to extract images from webtoon")
        else:  # novel
            content = process_novel_file(args.input)
            
            # 웹소설 텍스트 미리보기 저장
            preview_path = os.path.join(output_dir, "novel_preview.txt")
            with open(preview_path, "w", encoding="utf-8") as f:
                preview_text = content['full_text'][:1000] + "..." if len(content['full_text']) > 1000 else content['full_text']
                f.write(preview_text)
        
        # 키워드 및 분위기 추출
        keywords, genre, mood, era, music_style = extract_keywords(content, content_type=args.type)
        
        # 키워드 정보 저장
        keywords_info_path = os.path.join(output_dir, "keywords_info.txt")
        with open(keywords_info_path, "w", encoding="utf-8") as f:
            f.write(f"Extracted keywords: {', '.join(keywords)}\n")
            f.write(f"Detected genre: {genre}\n")
            f.write(f"Detected mood: {mood}\n")
            f.write(f"Detected era: {era}\n")
            f.write(f"Suggested music style: {music_style}\n")
        
        print(f"Extracted keywords: {keywords}")
        print(f"Detected genre: {genre}")
        print(f"Detected mood: {mood}")
        print(f"Detected era: {era}")
        print(f"Suggested music style: {music_style}")
        
        # 키워드 시각화 (출력 디렉토리에 저장)
        visualization_path = os.path.join(output_dir, "keywords_visualization.png")
        visualize_keywords(keywords, output_path=visualization_path)
        
        # 음악 생성
        music_path = generate_music(keywords, genre, mood, era, music_style, output_path)
        
        if music_path:
            print(f"Music generated successfully at {music_path}")
            
            # 결과 요약 파일 생성
            summary_path = os.path.join(output_dir, "summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"Content Type: {args.type}\n")
                f.write(f"Input Source: {args.input}\n")
                f.write(f"Generated Music: {output_filename}\n")
                f.write(f"Genre: {genre}\n")
                f.write(f"Mood: {mood}\n")
                f.write(f"Era: {era}\n")
                f.write(f"Music Style: {music_style}\n")
                f.write(f"Keywords: {', '.join(keywords)}\n")
                f.write(f"\nProcessed on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print(f"All output files saved to directory: {output_dir}")
        else:
            print("Failed to generate music")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

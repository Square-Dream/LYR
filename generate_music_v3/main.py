import argparse
import os
import datetime
import uuid
import traceback
from webtoon_processor import extract_webtoon_from_files, extract_webtoon_content
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
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 파일명 또는 URL에서 간단한 식별자 추출
    if content_type == 'webtoon':
        identifier = os.path.basename(input_source[0]).split('.')[0] if os.path.exists(input_source[0]) else input_source[0].split('/')[-1]
    else:
        identifier = os.path.basename(input_source[0]).split('.')[0]

    # 고유 ID 생성
    unique_id = str(uuid.uuid4())[:8]
    output_dir = f"output_{content_type}_{identifier}_{timestamp}_{unique_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Created output directory: {output_dir}")
    return output_dir

def main():
    try:
        parser = argparse.ArgumentParser(description='Generate music based on webtoon or novel content.')
        parser.add_argument('--type', choices=['webtoon', 'novel'], required=True, help='Content type: webtoon or novel')
        parser.add_argument('--input', nargs='+', required=True, help='One or more file paths or a single URL')
        parser.add_argument('--output', default=None, help='Output music file path (optional)')
        parser.add_argument('--use_cache', action='store_true', help='Use cached content if available')
        args = parser.parse_args()

        # 출력 디렉터리 생성
        output_dir = create_output_directory(args.type, args.input)

        # 출력 파일 경로
        if args.output:
            output_path = os.path.join(output_dir, os.path.basename(args.output))
        else:
            output_path = os.path.join(output_dir, "generated_music.wav")

        print(f"Processing {args.type} content from {args.input}...")
        print(f"Output will be saved to: {output_path}")

        content = None

        # 콘텐츠 처리
        if args.type == 'webtoon':
            # 여러 파일 경로를 입력받은 경우
            if os.path.exists(args.input[0]):
                files = [open(file_path, 'rb') for file_path in args.input]
                content = extract_webtoon_from_files(files, use_cache=args.use_cache, output_dir=output_dir)
            # URL로 전달된 경우
            else:
                content = extract_webtoon_content(args.input[0], use_cache=args.use_cache, output_dir=output_dir)

            # 이미지 추출 성공 여부 확인
            if content and content.get('images'):
                print(f"Successfully extracted {len(content['images'])} images.")
            else:
                print("No images extracted.")

        elif args.type == 'novel':
            # 소설 파일은 하나만 받아야 함
            if len(args.input) != 1:
                print("Error: Only one file should be provided for novel processing.")
                return
            
            content = process_novel_file(args.input[0])

            # 소설 텍스트 미리보기 저장
            preview_path = os.path.join(output_dir, "novel_preview.txt")
            with open(preview_path, "w", encoding="utf-8") as f:
                preview_text = content['full_text'][:1000] + "..." if len(content['full_text']) > 1000 else content['full_text']
                f.write(preview_text)
        
        if not content:
            print("Content processing failed.")
            return

        # 키워드 추출
        keywords, genre, mood, era, music_style = extract_keywords(content, content_type=args.type)

        # 키워드 시각화
        visualization_path = os.path.join(output_dir, "keywords_visualization.png")
        visualize_keywords(keywords, output_path=visualization_path)

        # 음악 생성
        music_path = generate_music(keywords, genre, mood, era, music_style, output_path)

        if music_path:
            print(f"Music generated successfully at {music_path}")

            # 결과 요약 저장
            summary_path = os.path.join(output_dir, "summary.txt")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(f"Content Type: {args.type}\n")
                f.write(f"Input Source: {args.input}\n")
                f.write(f"Generated Music: {output_path}\n")
                f.write(f"Genre: {genre}\n")
                f.write(f"Mood: {mood}\n")
                f.write(f"Era: {era}\n")
                f.write(f"Music Style: {music_style}\n")
                f.write(f"Keywords: {', '.join(keywords)}\n")
                f.write(f"Processed on: {datetime.datetime.now()}\n")

            print(f"All output files saved to {output_dir}")
        else:
            print("Music generation failed.")

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

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
        api: 수동
    Returns:
        str: 생성된 출력 디렉토리 경로
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    if content_type == 'webtoon':
        identifier = input_source.split('/')[-1].split('?')[0]
        if len(identifier) > 20:
            identifier = identifier[:20]
    else:
        identifier = os.path.basename(input_source).split('.')[0]
        if len(identifier) > 20:
            identifier = identifier[:20]

    unique_id = str(uuid.uuid4())[:8]
    output_dir = f"output_{content_type}_{identifier}_{timestamp}_{unique_id}"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Created output directory: {output_dir}")
    return output_dir

def main():
    """
    프로그램의 메인 엔트리 포인트. 웹툰 또는 소설을 입력으로 받아 음악을 생성합니다.
    """
    try:
        parser = argparse.ArgumentParser(description='Generate music based on webtoon or web novel content')
        parser.add_argument('--type', choices=['webtoon', 'novel'], required=True, help='Content type: webtoon or novel')
        parser.add_argument('--input', required=True, help='URL for webtoon or file path for novel')
        parser.add_argument('--output', default=None, help='Output music file path (optional)')
        parser.add_argument('--api_key', required=True, help='OpenAI API key')
        parser.add_argument('--use_cache', action='store_true', help='Use cached content if available')

        args = parser.parse_args()

        output_dir = create_output_directory(args.type, args.input)

        if args.output:
            output_filename = os.path.basename(args.output)
        else:
            output_filename = "generated_music.wav"

        output_path = os.path.join(output_dir, output_filename)

        print(f"Processing {args.type} content from {args.input}...")
        print(f"Output will be saved to: {output_path}")

        content = {}
        if args.type == 'webtoon':
            if args.input.startswith('http'):
                content = extract_webtoon_content(args.input, use_cache=args.use_cache, output_dir=output_dir)
            else:
                image_files = args.input.split(',')
                content = extract_webtoon_content(image_files, use_cache=args.use_cache, output_dir=output_dir)

        elif args.type == 'novel':
            content = process_novel_file(args.input)
            preview_path = os.path.join(output_dir, "novel_preview.txt")
            with open(preview_path, "w", encoding="utf-8") as f:
                preview_text = content['full_text'][:1000] + "..." if len(content['full_text']) > 1000 else content['full_text']
                f.write(preview_text)

        # 키워드 추출
        keywords, genre, mood, era, music_style = extract_keywords(content, content_type=args.type, api_key=args.api_key)

        # 키워드 정보 저장
        keywords_info_path = os.path.join(output_dir, "keywords_info.txt")
        with open(keywords_info_path, "w", encoding="utf-8") as f:
            f.write(f"Detected genre: {genre}\n")
            f.write(f"Detected mood: {mood}\n")
            f.write(f"Detected era: {era}\n")
            f.write(f"Suggested music style: {music_style}\n")

        print(f"Extracted keywords: {keywords}")
        print(f"Detected genre: {genre}")
        print(f"Detected mood: {mood}")
        print(f"Detected era: {era}")
        print(f"Suggested music style: {music_style}")

        # 키워드 시각화 저장
        visualization_path = os.path.join(output_dir, "keywords_visualization.png")
        visualize_keywords(keywords, output_path=visualization_path)

        # 음악 생성
        music_path = generate_music(keywords, genre, mood, era, music_style, output_path)

        if music_path:
            print(f"Music generated successfully at {music_path}")
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
                f.write(f"Processed on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            print(f"All output files saved to directory: {output_dir}")
        else:
            print("Failed to generate music")

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()

# app.py

import gradio as gr
from keyword_extractor import analyze_image_content, extract_keywords
from music_generator import generate_music
import tempfile
import os

def process_content(api_key, content_type, files):
    """
    콘텐츠를 처리하고 음악을 생성합니다.

    Args:
        api_key (str): OpenAI API 키
        content_type (str): 콘텐츠 타입 ('webtoon' 또는 'novel')
        files (list): 업로드된 파일 리스트

    Returns:
        tuple: 상태 메시지, 생성된 오디오 파일 경로
    """
    temp_dir = tempfile.mkdtemp()
    keywords = []

    try:
        if content_type == "webtoon":
            for file in files:
                file_path = file.name

                # 이미지 분석 (API Key 전달)
                image_keywords = analyze_image_content(file_path, api_key)
                keywords.extend(image_keywords)

        elif content_type == "novel":
            file_path = files[0].name

            # 텍스트 분석 (API Key 전달)
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            keywords = extract_keywords({"full_text": text_content}, "novel", api_key)

        keywords = list(set(keywords))
        output_path = os.path.join(temp_dir, "output.wav")

        # 음악 생성
        generate_music(keywords, "romance", "peaceful", "modern", "acoustic", output_path)

        return f"Generated Music with Keywords: {', '.join(keywords)}", output_path

    except Exception as e:
        print(f"Error: {str(e)}")
        return f"Error: {str(e)}", None

def gradio_interface():
    with gr.Blocks() as demo:
        gr.Markdown("# Webtoon & Novel to Music Generator")
        gr.Markdown("Upload images or a text file and enter your OpenAI API key to generate music.")

        api_key_input = gr.Textbox(label="OpenAI API Key", type="password", placeholder="Enter your OpenAI API Key")
        content_type_input = gr.Dropdown(choices=["webtoon", "novel"], label="Content Type")
        file_input = gr.Files(label="Upload Files", file_types=["image", "text"])

        submit_button = gr.Button("Generate Music")
        output_text = gr.Textbox(label="Status")
        output_audio = gr.Audio(label="Generated Music", type="filepath")

        submit_button.click(
            fn=process_content,
            inputs=[api_key_input, content_type_input, file_input],
            outputs=[output_text, output_audio]
        )

    return demo

if __name__ == "__main__":
    demo = gradio_interface()
    demo.launch()

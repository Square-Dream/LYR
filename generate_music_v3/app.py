import os
import gradio as gr
from webtoon_processor import extract_webtoon_from_files
from novel_processor import process_novel_file
from music_generator import generate_music
from utils import visualize_keywords

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def analyze_content(content_type, files, prompt):
    content = None
    extracted_text = ""

    if content_type == "webtoon":
        content = extract_webtoon_from_files(files, use_cache=True)
        extracted_texts = content.get('texts', [])
        extracted_text = " ".join(extracted_texts)

    elif content_type == "novel":
        if len(files) != 1:
            return None, None, "Please upload a single text file for novel analysis."
        file_path = files[0].name
        content = process_novel_file(file_path)
        extracted_text = content.get('full_text', "")

    if prompt:
        extracted_text += f" {prompt}"

    keywords = extracted_text.split()[:5]
    genre = "ambient" if content_type == "webtoon" else "cinematic"
    mood = "calm" if content_type == "webtoon" else "dramatic"
    era = "modern"
    music_style = "lo_fi" if content_type == "webtoon" else "epic"

    visualization_path = "keywords_visualization.png"
    visualize_keywords(keywords, output_path=visualization_path)

    music_path = "generated_music.wav"
    generate_music(keywords, genre, mood, era, music_style, output_path=music_path)

    result_text = f"Keywords: {', '.join(keywords)}\nGenre: {genre}\nMood: {mood}\nEra: {era}\nMusic Style: {music_style}"

    return visualization_path, music_path, result_text

# Gradio 인터페이스 설정
with gr.Blocks() as demo:
    gr.Markdown("# 🎵 Content to Music Generator")
    gr.Markdown("Upload images for webtoon analysis or a text file for novel analysis to generate mood-based music.")

    with gr.Row():
        with gr.Column():
            content_type = gr.Radio(["webtoon", "novel"], label="Content Type", value="webtoon")
            file_input = gr.Files(label="Upload Files (Images or Text)", file_count="multiple")
            prompt_input = gr.Textbox(label="Optional Prompt", placeholder="Add any descriptive prompt...")

        with gr.Column():
            analysis_output = gr.Textbox(label="Analysis Result", interactive=False)
            music_output = gr.Audio(label="Generated Music", interactive=False)

    generate_button = gr.Button("Generate Music")

    # Example Files
    example_files = [
        ["webtoon", [os.path.join(ASSETS_DIR, "example1.JPG"), os.path.join(ASSETS_DIR, "example2.JPG")], "A calm scene"],
        ["novel", [os.path.join(ASSETS_DIR, "example_novel.txt")], "A dramatic narrative"]
    ]

    with gr.Row():
        gr.Examples(
            examples=example_files,
            inputs=[content_type, file_input, prompt_input],
            outputs=[analysis_output, music_output],
            fn=analyze_content,
            cache_examples=True
        )

    generate_button.click(
        analyze_content,
        inputs=[content_type, file_input, prompt_input],
        outputs=[analysis_output, music_output]
    )

demo.launch()

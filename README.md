
# Webtoon & Novel Emotion-Based Music Generator 

This project extracts emotions from webtoon images and novel text, then generates emotionally aligned music using AI models. It integrates OCR, keyword extraction, emotion classification, and music generation through MusicGen.

---

## Project Structure

```
/project-root/
│── main.py               # CLI entry point
│── app.py                # Web UI server
│── utils.py              # Visualization, audio tools
│── keyword_extractor.py  # Keyword & emotion extractor (KoNLPy + KeyBERT + GPT-4o Vision)
│── music_generator.py    # MusicGen-based music generator
│── novel_processor.py    # .txt novel content processor
│── webtoon_processor.py  # Image crawler + OCR (pytesseract)
│── prompt_gen.py         # Prompt builder for music generation
│── requirements.txt      # Python dependencies
│── input_images/         # Folder for webtoon images
│── output_music/         # Generated music output
│── cache/                # Cached results (keywords, music, vision)
│── test_texts/           # Sample novel text files
```

---

##  Prerequisites

- Python 3.8+
- Tesseract OCR (required for image-to-text)
- PyTorch
- EasyOCR
- Audiocraft (for MusicGen)
- KoNLPy, NLTK, KeyBERT

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## How to Use

### CLI Mode – Emotion to Music

```bash
python main.py --input input_images/test_image_romance_webtoon \
               --output output_music/test_music.wav \
               --api_key YOUR_OPENAI_API_KEY
```

Arguments:
- `--input`: Path to image folder or `.txt` file
- `--output`: Output path for `.wav` file
- `--api_key`: OpenAI API key (for GPT-4o Vision emotion analysis)

---

### Web Application Mode

```bash
python app.py --port 8080 --api_key YOUR_OPENAI_API_KEY
```

Then open: `http://localhost:8080`

---

### Input Examples

**Image Folder**
```
/input_images/test_image_romance_webtoon/
├── image1.jpg
├── image2.jpg
```

**Text File**
```
/test_texts/
├── romance_novel.txt
```

---

## Music Generation Flow

The `music_generator.py` module uses Audiocraft's `musicgen-small`. It synthesizes music prompts from text & image emotions and creates six-segment compositions (intro to outro) with crossfade.

```python
from music_generator import generate_music_from_prompt

prompt = "A calm, nostalgic melody with emotional undertones."
output_path = "output_music/generated_music.wav"
generate_music_from_prompt(prompt, output_path)
```

---

## Utilities

**Keyword Wordcloud**
```python
from utils import visualize_keywords

keywords = ["love", "loss", "memory", "sunset", "hope"]
visualize_keywords(keywords, "output/keywords_visualization.png")
```

**Audio Normalization**
```python
from utils import normalize_audio
normalize_audio("output_music/generated.wav")
```

---

## Caching

To accelerate repeated runs, image/text/music outputs are cached in `/cache`. Avoids redundant re-analysis.

---

## License

Licensed under the MIT License.

---

## Contributing

1. Fork this repo
2. Create a new branch: `feature/my-feature`
3. Commit & push changes
4. Open a Pull Request

---

## Notes

- Make sure Tesseract is installed and path is properly set in `webtoon_processor.py`
- Keep your OpenAI API key secure (e.g., via `.env` or CLI args)


from audio_processor import AudioProcessor
from dotenv import load_dotenv
from pathlib import Path
import os
import requests

load_dotenv()

def clean_story_with_gemini(story_text):
    """
    Use Gemini API to clean and validate the story text for TTS (remove unsupported characters, ensure proper punctuation, and keep it API-friendly).
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("Gemini API key not set. Set GEMINI_API_KEY in your .env file.")
        return story_text
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro-latest:generateContent?key=" + gemini_api_key
    prompt = (
        "Clean up the following story for use with a TTS API. "
        "Ensure it is plain, well-punctuated, free of unsupported symbols, and not excessively long. "
        "Return only the cleaned story.\n\n" + story_text
    )
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, json=data, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        cleaned = result["candidates"][0]["content"]["parts"][0]["text"]
        return cleaned.strip()
    except Exception as e:
        print(f"Gemini API error: {e}")
        return story_text

def local_clean_story(story_text, max_length=4000):
    """
    Clean the story text using a local fallback method (remove non-ASCII characters, ensure proper punctuation, and truncate if too long).
    """
    # Remove non-ASCII characters
    cleaned = ''.join(c if 32 <= ord(c) <= 126 or c in '\n\r' else ' ' for c in story_text)
    # Replace multiple spaces/newlines with single
    import re
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Truncate to max_length
    cleaned = cleaned[:max_length]
    # Ensure it ends with a period
    if not cleaned.strip().endswith(('.', '!', '?')):
        cleaned = cleaned.strip() + '.'
    return cleaned

def split_story_into_chunks(story_text, max_chunk_length=1000):
    """
    Split the story into chunks (by sentence or paragraph) that are each <= max_chunk_length characters.
    """
    import re
    # Split by paragraph or sentence
    sentences = re.split(r'(?<=[.!?]) +', story_text)
    chunks = []
    current = ''
    for s in sentences:
        if len(current) + len(s) + 1 > max_chunk_length:
            if current:
                chunks.append(current.strip())
                current = ''
        current += (' ' if current else '') + s
    if current:
        chunks.append(current.strip())
    return chunks

if __name__=="__main__":
    ffmpeg = r"E:\Projects\Audio 5D\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
    proc = AudioProcessor(ffmpeg_bin=ffmpeg)
    
    story_file = Path("story.txt")
    if not story_file.exists():
        print(f"Error: Input file not found at '{story_file}'")
    else:
        with open(story_file, "r", encoding="utf-8") as f:
            story_text = f.read()
        # Clean and validate story text using Gemini before processing
        cleaned = clean_story_with_gemini(story_text)
        if cleaned == story_text or cleaned.strip() == '':
            print("Using local fallback cleaning for story text.")
            cleaned = local_clean_story(story_text)
        # Split into TTS-safe chunks
        chunks = split_story_into_chunks(cleaned, max_chunk_length=950)
        print(f"Processing story in {len(chunks)} chunks...")
        temp_files = []
        for i, chunk in enumerate(chunks):
            temp_out = f"temp_audio_chunk_{i}.mp3"
            proc.process_story(chunk, "temp_audio", temp_out)
            temp_files.append(temp_out)
        # Concatenate all chunk outputs into the final file
        if temp_files:
            concat_file = "concat_list.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                for tf in temp_files:
                    f.write(f"file '{tf}'\n")
            ffmpeg_bin = ffmpeg
            final_out = "aetherfall_immersive.mp3"
            os.system(f'"{ffmpeg_bin}" -y -f concat -safe 0 -i {concat_file} -c copy {final_out}')
            print(f"Final audio created: {final_out}")
            # Clean up temp files
            for tf in temp_files:
                try:
                    os.remove(tf)
                except Exception:
                    pass
            try:
                os.remove(concat_file)
            except Exception:
                pass
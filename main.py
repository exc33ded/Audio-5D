from audio_processor import AudioProcessor
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

if __name__=="__main__":
    ffmpeg = r"E:\Projects\Audio 5D\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
    proc = AudioProcessor(ffmpeg_bin=ffmpeg)
    
    story_file = Path("story2.txt")
    if not story_file.exists():
        print(f"Error: Input file not found at '{story_file}'")
    else:
        with open(story_file, "r", encoding="utf-8") as f:
            story_text = f.read()
        proc.process_story(story_text, "temp_audio", "aetherfall_immersive2.mp3")
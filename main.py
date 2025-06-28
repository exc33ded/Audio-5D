from audio_processor import AudioProcessor

def demo_story():
    return """
    Narrator: In a world of endless possibilities...
    Male Character: I've discovered something extraordinary!
    Female Character: What could it be?
    Narrator: The air crackled with excitement as they gathered around.
    """

if __name__ == "__main__":
    # point to your ffmpeg.exe if it's not in PATH:
    ffmpeg_path = r"E:\Projects\Audio 5D\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"

    ap = AudioProcessor(ffmpeg_bin=ffmpeg_path)
    story = demo_story().strip()
    ap.process_story(story, work_dir="temp_audio", final_out="immersive_story.mp3")

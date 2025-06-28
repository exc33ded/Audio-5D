import os
import subprocess
import requests
from dotenv import load_dotenv

class AudioProcessor:
    def __init__(self, api_key=None, ffmpeg_bin=None):
        load_dotenv()
        self.api_key = api_key or os.getenv("UNREAL_SPEECH_API_KEY")
        # path to ffmpeg.exe
        self.ffmpeg = ffmpeg_bin or r"ffmpeg"  
        # voices mapping
        self.voices = {
            'narrator': 'af_nicole',
            'male_character': 'am_michael',
            'female_character': 'af_bella'
        }

    def text_to_mp3(self, text, voice_id, out_path):
        """Call Unreal Speech and write raw MP3 to out_path."""
        resp = requests.post(
            "https://api.v8.unrealspeech.com/stream",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"Text": text, "VoiceId": voice_id, "Bitrate":"256k",
                  "Speed":"0","Pitch":"1","Codec":"libmp3lame"}
        )
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)

    def apply_effects(self, in_path, out_path,
                      pan_rate=0.2,    # oscillations per second
                      reverb_in_gain=0.8, reverb_out_gain=0.9,
                      reverb_delays="60|60", reverb_decays="0.4|0.3"):
        """
        Uses FFmpeg:
          - apulsator=hz=<pan_rate>      → oscillating stereo pan
          - aecho=<in_gain>:<out_gain>:<delays>:<decays>  → reverb
        """
        pan_filter    = f"apulsator=hz={pan_rate}"
        reverb_filter = f"aecho={reverb_in_gain}:{reverb_out_gain}:{reverb_delays}:{reverb_decays}"
        filter_chain  = f"{pan_filter},{reverb_filter},loudnorm"  # add loudnorm for consistent volume

        cmd = [
            self.ffmpeg, "-y", "-i", in_path,
            "-af", filter_chain,
            "-codec:a", "libmp3lame", "-b:a", "256k",
            out_path
        ]
        subprocess.run(cmd, check=True)

    def concat(self, segment_paths, final_out):
        """Concatenate via ffmpeg concat demuxer."""
        # Create a temporary list file
        list_txt = "segments.txt"
        with open(list_txt, "w") as f:
            for p in segment_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            self.ffmpeg, "-y", "-f", "concat", "-safe", "0",
            "-i", list_txt,
            "-c", "copy",
            final_out
        ]
        subprocess.run(cmd, check=True)
        os.remove(list_txt)

    def process_story(self, story_text, work_dir="temp", final_out="output.mp3"):
        os.makedirs(work_dir, exist_ok=True)
        segment_files = []

        # 1) split lines and TTS each
        for idx, line in enumerate([l.strip() for l in story_text.splitlines() if l.strip()]):
            # pick voice
            role = 'narrator'
            lower = line.lower()
            for key in self.voices:
                if key in lower:
                    role = key
                    break

            raw_mp3 = os.path.join(work_dir, f"raw_{idx}.mp3")
            proc_mp3 = os.path.join(work_dir, f"fx_{idx}.mp3")

            self.text_to_mp3(line, self.voices[role], raw_mp3)

            # 2) apply spatial + reverb + loudness normalization
            self.apply_effects(raw_mp3, proc_mp3)

            segment_files.append(proc_mp3)

        # 3) concat into one
        self.concat(segment_files, final_out)

        print(f"✨ Done! Final audio → {final_out}")
        return final_out

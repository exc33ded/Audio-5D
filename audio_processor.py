import os
import subprocess
import requests
from dotenv import load_dotenv
import shutil

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

    def extract_emotion_params(self, text):
        """Detect emotion cues, punctuation, and return TTS params: speed, pitch, volume."""
        cues = [
            (['shout', 'shouted', 'yelled', 'exclaimed', 'loudly', '!'], '0.25', '1.25', '1.3'),
            (['whisper', 'whispered', 'softly', 'murmur', 'quietly'], '-0.25', '0.9', '0.7'),
            (['sad', 'sadly', 'sorrow', 'cry', 'cried'], '-0.15', '0.8', '0.9'),
            (['happy', 'happily', 'joy', 'excited', 'excitedly'], '0.12', '1.12', '1.1'),
            (['angry', 'angrily', 'furious', 'rage'], '0.18', '1.18', '1.2'),
            (['calm', 'calmly', 'serene', 'peaceful'], '-0.12', '1.0', '0.9'),
        ]
        lower = text.lower()
        # Punctuation-based cues
        if text.strip().endswith('!'):
            return '0.25', '1.25', '1.3'
        if text.strip().endswith('...'):
            return '-0.15', '0.9', '0.8'
        for keywords, speed, pitch, volume in cues:
            if any(k in lower for k in keywords):
                return speed, pitch, volume
        # Question: slightly higher pitch
        if text.strip().endswith('?'):
            return '0.05', '1.15', '1.0'
        return '0', '1', '1'  # default: neutral

    def text_to_mp3(self, text, voice_id, out_path, speed='0', pitch='1', volume='1'):
        """Call Unreal Speech and write raw MP3 to out_path, with emotion params and optional pause."""
        # Add a short pause after each line for pacing
        if text and not text.strip().endswith(('.', '!', '?', '...')):
            text = text.strip() + '.'
        resp = requests.post(
            "https://api.v8.unrealspeech.com/stream",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "Text": text,
                "VoiceId": voice_id,
                "Bitrate": "256k",
                "Speed": speed,
                "Pitch": pitch,
                "Volume": volume,
                "Codec": "libmp3lame"
            }
        )
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(resp.content)
        # Add a 0.3s silence after each segment for pacing
        silence_path = out_path.replace('.mp3', '_silence.mp3')
        cmd = [self.ffmpeg, '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-t', '0.3', '-q:a', '9', '-acodec', 'libmp3lame', silence_path]
        subprocess.run(cmd, check=True)
        # Concatenate voice and silence
        concat_path = out_path.replace('.mp3', '_withsilence.mp3')
        cmd = [self.ffmpeg, '-y', '-i', f"concat:{out_path}|{silence_path}", '-acodec', 'libmp3lame', '-b:a', '256k', concat_path]
        subprocess.run(cmd, check=True)
        os.replace(concat_path, out_path)
        os.remove(silence_path)

    def detect_sfx_and_pan(self, text, role):
        """Detect multiple SFX and pan direction from text and role. More robust cue matching and debug output."""
        sfx_map = {
            'rain': ['rain', 'raining', 'poured', 'pouring', 'downpour'],
            'forest': ['forest', 'woods', 'trees'],
            'gate': ['gate', 'door', 'creaked', 'opened'],
            'battle': ['battle', 'fight', 'sword', 'combat'],
            'storm': ['storm', 'thunder', 'lightning', 'tempest', 'rumbled'],
            'fire': ['fire', 'flame', 'burn', 'crackled'],
            'crowd': ['crowd', 'chanting', 'people', 'voices'],
            'wind': ['wind', 'howled', 'gust'],
            'river': ['river', 'stream', 'water', 'rushing'],
            'beast': ['beast', 'roared', 'monster', 'growl'],
        }
        pan_map = {
            'narrator': 0.0,
            'male_character': -0.5,  # left
            'female_character': 0.5, # right
        }
        sfx_list = []
        pan = pan_map.get(role, 0.0)
        lower = text.lower()
        for cue, keywords in sfx_map.items():
            if any(word in lower for word in keywords):
                sfx_path = f'sfx/{cue}.mp3'
                sfx_list.append(sfx_path)
                print(f"[SFX DETECTED] '{cue}' in line: {text.strip()}")
        # Pan cues
        if 'left' in lower:
            pan = -1.0
        elif 'right' in lower:
            pan = 1.0
        elif 'behind' in lower:
            pan = 0.0  # center, but could add reverb
        return sfx_list, pan

    def apply_effects(self, in_path, out_path,
                      pan_rate=0.2,
                      reverb_in_gain=0.8, reverb_out_gain=0.9,
                      reverb_delays="60|60", reverb_decays="0.4|0.3",
                      pan_pos=0.0, sfx_path=None):
        """
        Uses FFmpeg:
          - apulsator=hz=<pan_rate>      → oscillating stereo pan
          - pan=stereo|c0=<L>|c1=<R>     → static pan
          - aecho=<in_gain>:<out_gain>:<delays>:<decays>  → reverb
          - mixes in SFX if provided (now supports multiple SFX)
        """
        # If SFX is requested but missing, try to fetch it from Freesound
        sfx_paths = sfx_path if isinstance(sfx_path, list) else ([sfx_path] if sfx_path else [])
        for sfx in sfx_paths:
            if sfx and not os.path.exists(sfx):
                cue = os.path.splitext(os.path.basename(sfx))[0]
                print(f"SFX '{sfx}' not found. Attempting to fetch from Freesound...")
                self.fetch_sfx_from_freesound(cue, sfx)
        # Pan filter: static if pan_pos set, else oscillating
        if pan_pos != 0.0:
            l = max(0.0, 1.0 - pan_pos)
            r = max(0.0, 1.0 + pan_pos)
            pan_filter = f"pan=stereo|c0={l}*c0|c1={r}*c1"
        else:
            pan_filter = f"apulsator=hz={pan_rate}"
        reverb_filter = f"aecho={reverb_in_gain}:{reverb_out_gain}:{reverb_delays}:{reverb_decays}"
        filter_chain = f"{pan_filter},{reverb_filter},loudnorm"
        # If SFX, mix them in
        if sfx_paths:
            # Build filter_complex for multiple SFX
            inputs = [f'-i', in_path] + sum([[f'-i', s] for s in sfx_paths if os.path.exists(s)], [])
            amix_inputs = 1 + len([s for s in sfx_paths if os.path.exists(s)])
            # Make narration louder and SFX a bit softer
            narration_boost = '[0:a]volume=1.2[voice]'  # boost narration
            sfx_volumes = [f'[{i+1}:a]volume=0.18[sfx{i}]' for i in range(amix_inputs-1)]
            sfx_labels = ''.join([f'[sfx{i}]' for i in range(amix_inputs-1)])
            filter_complex = (
                narration_boost + ';' +
                ('' if not sfx_volumes else ';'.join(sfx_volumes) + ';') +
                f'[voice]{sfx_labels}amix=inputs={amix_inputs}:duration=first:dropout_transition=2[out]'
            )
            cmd = [self.ffmpeg, '-y'] + inputs + [
                '-filter_complex', filter_complex,
                '-map', '[out]',
                '-codec:a', 'libmp3lame', '-b:a', '256k',
                out_path
            ]
        else:
            cmd = [
                self.ffmpeg, '-y', '-i', in_path,
                '-af', filter_chain,
                '-codec:a', 'libmp3lame', '-b:a', '256k',
                out_path
            ]
        print(f"[FFMPEG CMD] {' '.join(str(c) for c in cmd)}")
        subprocess.run(cmd, check=True)

    def concat(self, segment_paths, final_out):
        """Concatenate via ffmpeg concat demuxer."""
        # Build input arguments
        input_args = []
        filter_inputs = []
        for i, p in enumerate(segment_paths):
            input_args += ['-i', os.path.abspath(p)]
            filter_inputs.append(f'[{i}:a]')
        filter_complex = f'{"".join(filter_inputs)}concat=n={len(segment_paths)}:v=0:a=1[out]'
        cmd = [
            self.ffmpeg, '-y', *input_args,
            '-filter_complex', filter_complex,
            '-map', '[out]',
            '-acodec', 'libmp3lame', '-b:a', '256k',
            final_out
]
        subprocess.run(cmd, check=True)

    def get_ambient_sfx(self, story_text):
        """Detect ambient SFX (rain, forest, wind, etc.) that should persist for the whole story or scene."""
        ambient_cues = ['rain', 'forest', 'wind', 'river', 'storm', 'crowd', 'fire']
        lower = story_text.lower()
        ambient_sfx = []
        for cue in ambient_cues:
            if cue in lower:
                sfx_path = f'sfx/{cue}.mp3'
                if sfx_path not in ambient_sfx:
                    ambient_sfx.append(sfx_path)
        return ambient_sfx

    def process_story(self, story_text, work_dir="temp", final_out="output.mp3"):
        os.makedirs(work_dir, exist_ok=True)
        segment_files = []
        import random
        narrator_lines = []
        narrator_indices = []
        char_segments = {}
        # 1) split lines and collect narrator/character lines
        for idx, line in enumerate([l.strip() for l in story_text.splitlines() if l.strip()]):
            role = 'narrator'
            lower = line.lower()
            for key in self.voices:
                if key in lower:
                    role = key
                    break
            if role == 'narrator':
                narrator_lines.append(line)
                narrator_indices.append(idx)
            else:
                char_segments[idx] = (line, role)
        # 2) Process narrator lines as one segment for smooth 8D pan
        if narrator_lines:
            narrator_text = ' '.join(narrator_lines)
            speed, pitch, volume = self.extract_emotion_params(narrator_text)
            # Add slight random pitch/volume for realism
            pitch = str(float(pitch) + random.uniform(-0.04, 0.04))
            volume = str(float(volume) + random.uniform(-0.05, 0.05))
            raw_mp3 = os.path.join(work_dir, f"raw_narrator.mp3")
            proc_mp3 = os.path.join(work_dir, f"fx_narrator.mp3")
            self.text_to_mp3(narrator_text, self.voices['narrator'], raw_mp3, speed, pitch, volume)
            pan_rate = random.uniform(0.13, 0.22)
            # Check for any special cues in narrator text
            lower = narrator_text.lower()
            if any(cue in lower for cue in ['behind', 'echo', 'distant', 'far away']):
                reverb = True
                extra_reverb = True
                volume = str(float(volume) * 0.7)
            else:
                reverb = False
                extra_reverb = False
            if reverb or extra_reverb:
                self.apply_effects(
                    raw_mp3, proc_mp3,
                    pan_pos=0.0, pan_rate=pan_rate, sfx_path=None,
                    reverb_in_gain=0.9 if extra_reverb else 0.8,
                    reverb_out_gain=1.0 if extra_reverb else 0.9,
                    reverb_delays="120|90" if extra_reverb else "60|60",
                    reverb_decays="0.7|0.5" if extra_reverb else "0.4|0.3"
                )
            else:
                self.apply_effects(raw_mp3, proc_mp3, pan_pos=0.0, pan_rate=pan_rate, sfx_path=None)
            # Split processed narrator audio into segments matching original narrator lines
            # (Optional: advanced - for now, treat as one segment)
            segment_files.append((min(narrator_indices), proc_mp3))
        # 3) Process character lines as before
        for idx in sorted(char_segments.keys()):
            line, role = char_segments[idx]
            speed, pitch, volume = self.extract_emotion_params(line)
            sfx_list, pan = self.detect_sfx_and_pan(line, role)
            pan_pos = pan
            pan_rate = 0.2
            raw_mp3 = os.path.join(work_dir, f"raw_{idx}.mp3")
            proc_mp3 = os.path.join(work_dir, f"fx_{idx}.mp3")
            self.text_to_mp3(line, self.voices[role], raw_mp3, speed, pitch, volume)
            self.apply_effects(raw_mp3, proc_mp3, pan_pos=pan_pos, pan_rate=pan_rate, sfx_path=sfx_list)
            segment_files.append((idx, proc_mp3))
        # 4) Sort and concat all segments in original order
        segment_files = [f for _, f in sorted(segment_files)]
        self.concat(segment_files, final_out)
        print(f"✨ Done! Final audio → {final_out}")
        # Clean up temp_audio and sfx content
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        if os.path.exists('sfx'):
            for f in os.listdir('sfx'):
                try:
                    os.remove(os.path.join('sfx', f))
                except Exception as e:
                    print(f"Could not delete SFX file {f}: {e}")
        return final_out

    def fetch_sfx_from_freesound(self, query, out_path, api_key=None):
        """Fetch a free SFX from Freesound.org API and save to out_path. Returns True if successful."""
        api_key = api_key or os.getenv("FREESOUND_API_KEY")
        if not api_key:
            print("Freesound API key not set. Set FREESOUND_API_KEY in your .env file.")
            return False
        # Map cue to better search terms
        cue_map = {
            'rain': 'rain heavy rainstorm',
            'forest': 'forest ambience birds',
            'gate': 'gate creak open metal',
            'battle': 'battle swords fight',
            'storm': 'storm thunder',
            'fire': 'fire crackling',
            'crowd': 'crowd talking',
            'wind': 'wind blowing',
            'river': 'river stream water',
            'beast': 'beast roar monster',
        }
        search_term = cue_map.get(query, query)
        base_url = "https://freesound.org/apiv2"
        headers = {"Authorization": f"Token {api_key}"}
        params = {"query": search_term, "fields": "id,previews,license", "page_size": 1}
        try:
            resp = requests.get(f"{base_url}/search/text/", headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                print(f"No SFX found for '{search_term}' on Freesound.")
                return False
            preview_url = results[0]["previews"]["preview-hq-mp3"]
            sfx_data = requests.get(preview_url, timeout=10)
            sfx_data.raise_for_status()
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(sfx_data.content)
            print(f"Downloaded SFX for '{search_term}' to {out_path}")
            return True
        except Exception as e:
            print(f"Error fetching SFX from Freesound: {e}")
            return False
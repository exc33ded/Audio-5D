from flask import Flask, render_template, request, send_file, redirect, url_for, flash, make_response
from audio_processor import AudioProcessor
from dotenv import load_dotenv
import os
from pathlib import Path
import tempfile
import re

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(32))

def split_story_into_chunks(story_text, max_chunk_length=950):
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        story_text = request.form.get('story_text')
        if not story_text or len(story_text.strip()) < 10:
            flash('Please enter a valid story.', 'danger')
            return redirect(url_for('index'))
        # Split into TTS-safe chunks
        chunks = split_story_into_chunks(story_text, max_chunk_length=950)
        ffmpeg = r"ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
        proc = AudioProcessor(ffmpeg_bin=ffmpeg)
        temp_files = []
        for i, chunk in enumerate(chunks):
            with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.txt') as tf:
                tf.write(chunk)
                tf_path = tf.name
            output_path = tf_path.replace('.txt', f'_chunk_{i}.mp3')
            proc.process_story(chunk, "temp_audio", output_path)
            temp_files.append(output_path)
        # Concatenate all chunk outputs into the final file
        if temp_files:
            concat_file = "concat_list.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                for tf in temp_files:
                    f.write(f"file '{tf}'\n")
            final_out = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            os.system(f'"{ffmpeg}" -y -f concat -safe 0 -i {concat_file} -c copy {final_out}')
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
            with open(final_out, 'rb') as f:
                audio_data = f.read()
            response = make_response(audio_data)
            response.headers.set('Content-Type', 'audio/mpeg')
            response.headers.set('Content-Disposition', 'inline; filename=immersive_story.mp3')
            try:
                os.remove(final_out)
            except Exception:
                pass
            return response
        else:
            flash('Audio generation failed.', 'danger')
            return redirect(url_for('index'))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

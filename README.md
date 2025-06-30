# 5D Audio Story Processor

This project transforms text stories into an immersive audio experience with spatial audio effects, often marketed as "5D" or "8D" audio. It leverages AI-powered text-to-speech (TTS) via the [Unreal Speech API](https://unrealspeech.com), combined with advanced audio processing techniques like dynamic panning, reverb, and sound effects (SFX) mixing, to create a captivating listening experience.

> **🎧 For the best experience, use headphones!**  
> Enjoy true left/right separation, swirling effects, and a sense of space that standard speakers can't replicate.

---

## What is "5D/8D" Audio?

"5D" and "8D" are informal terms describing stereo audio that simulates a three-dimensional soundscape through headphones. This project achieves this effect using:

- **Dynamic Panning**: Audio oscillates between left and right channels to mimic movement around the listener.
- **Static Panning**: Positions characters or sounds at specific points (e.g., left for male characters, right for female characters).
- **Reverb and Echo**: Adds depth and a sense of environment (e.g., a distant storm or echoing cave).
- **Stereo Enhancement**: Amplifies separation between channels for a wider soundstage.

**Note**: This is not true 3D audio (which requires formats like ambisonics or specialized hardware) but offers an engaging, immersive experience with standard stereo headphones.

---

## Features

- Text-to-speech conversion using Unreal Speech API
- Support for multiple character voices (narrator, male, female)
- Spatial audio effects with dynamic and static panning
- Reverb, normalization, and cross-fading for polish
- Automatic SFX detection and mixing (e.g., rain, fire, beast)
- Modern web UI with Flask, Bootstrap, glassmorphism, and animated backgrounds
- Progress indicators and in-browser audio playback/download

---

## 🎵 Sample Audio

Listen to a sample immersive audio story:  
[▶️ Sample.mp3](Sample.mp3)

---

## Prerequisites

- **Python 3.10 or higher**
- **Unreal Speech API key** (required for TTS)
- **(Optional) Gemini API key** for advanced story cleaning
- **(Optional) Freesound API key** for SFX fetching
- **FFmpeg** installed and accessible (for audio processing)

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Audio-5D
   ```

2. **Install dependencies** (use [uv](https://github.com/astral-sh/uv) for faster installs):
   ```bash
   uv pip install -r requirements.txt
   ```
   Or with pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your `.env` file**:
   Copy `.env.example` to `.env` and add your API keys:
   ```
   UNREAL_SPEECH_API_KEY=your_unreal_key
   GEMINI_API_KEY=your_gemini_key
   FREESOUND_API_KEY=your_freesound_key
   ```

4. **Install FFmpeg**: Ensure FFmpeg is installed and its path is provided (e.g., in `main.py` or `app.py`).

---

## Usage (Python)

Run the script directly with `main.py` if you don’t need the web interface.

1. **Import the AudioProcessor**:
   ```python
   from audio_processor import AudioProcessor
   ```

2. **Initialize with FFmpeg path**:
   ```python
   processor = AudioProcessor(ffmpeg_bin="path/to/ffmpeg.exe")
   ```

3. **Process a story**:
   ```python
   story = """
   Narrator: In a world of endless possibilities...
   Male Character: I've discovered something extraordinary!
   Female Character: What could it be?
   Narrator: The air crackled with excitement as they gathered around.
   """
   processed_audio = processor.process_story(story)
   ```

4. **Output**: The audio is saved as `output.mp3` (default) in the working directory.

Run `main.py` to process a story from `story.txt`:
```bash
python main.py
```

---

## Web App (Recommended)

Use `app.py` for a user-friendly Flask-based interface.

1. **Run the web app**:
   ```bash
   uv run app.py
   ```
   Or with Flask’s built-in server:
   ```bash
   python app.py
   ```
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

2. **Paste your story** into the text area.
3. Click **"Generate Immersive Audio"**.
4. Wait for processing (a spinner indicates progress).
5. **Listen** in-browser or **download** the resulting `immersive_story.mp3`.

---

## Customization

Adjust audio processing in `audio_processor.py`:

- **Voices**: Modify `self.voices` (e.g., `'narrator': 'af_nicole'`) for different TTS voices.
- **Panning**: Change `pan_pos` or `pan_rate` in `apply_effects`.
- **Reverb**: Tweak `reverb_in_gain`, `reverb_delays`, etc., in `apply_effects`.
- **SFX**: Add cues to `detect_sfx_and_pan` or adjust volume in `apply_effects`.

---

## Technical Details

### Audio Processing Pipeline

1. **Text-to-Speech Conversion** (`audio_processor.py`):
   - Uses Unreal Speech API for high-quality TTS.
   - Adjusts speed, pitch, and volume based on emotion cues (e.g., "shouted" → louder, faster).
   - Adds pauses between segments for natural pacing.

2. **Spatial Audio Processing** (`audio_processor.py`):
   - **Dynamic Panning**: FFmpeg’s `apulsator` filter oscillates audio between channels.
   - **Static Panning**: `pan` filter positions audio (e.g., left for male characters).
   - **Reverb**: `aecho` filter adds depth, with customizable parameters.

3. **Sound Effects (SFX)** (`audio_processor.py`):
   - Detects cues (e.g., "rain", "beast") in text and mixes corresponding SFX.
   - Fetches SFX from Freesound.org (if API key provided) or uses local files.
   - Adjusts SFX volume to complement narration.

4. **Chunking and Concatenation** (`main.py`, `app.py`):
   - Splits stories into chunks (<950 characters) to manage API limits.
   - Concatenates processed chunks using FFmpeg’s `concat` demuxer.

### Key Files

- **`main.py`**:
  - Standalone script for processing stories from `story.txt`.
  - Cleans text with Gemini API (optional) or locally, splits into chunks, and generates audio.
  - Ideal for command-line use without Flask.

- **`app.py`**:
  - Flask web app for interactive story processing.
  - Handles story input via a web form, processes chunks, and streams audio to the browser.
  - Requires FFmpeg path configuration.

- **`audio_processor.py`**:
  - Core logic for TTS, spatial effects, SFX mixing, and audio enhancement.
  - Manages Unreal Speech API calls, FFmpeg filters, and file operations.

### Reducing API Dependency

To minimize costs and avoid API limits:

- **Unreal Speech API**:
  - Stories are split into chunks (<950 characters) to stay within free-tier limits (check [Unreal Speech’s pricing](https://unrealspeech.com/pricing)).
  - Required for TTS; no local fallback exists.

- **Gemini API** (Optional):
  - Used in `main.py` for advanced story cleaning (e.g., punctuation, length).
  - Falls back to `local_clean_story` if no API key is provided or if requests fail.
  - Chunks input to avoid word limit overload.

- **Freesound API** (Optional):
  - Fetches SFX dynamically if local files are missing.
  - Falls back to skipping SFX if no API key or files are available.

**Cost Management Tips**:
- Use local cleaning (`local_clean_story`) and pre-downloaded SFX to avoid optional APIs.
- Process large stories in chunks to leverage free tiers.

---

## Screenshots

![Web App Screenshot](SS.jpeg)

---

## API Keys

- **Unreal Speech**: Required for TTS generation.
- **Gemini**: Optional for advanced text cleaning (local fallback available).
- **Freesound**: Optional for SFX fetching (local files can substitute).

**Security Note**: Never commit your `.env` file! It’s included in `.gitignore` for safety.

---

## Credits

Made with ❤️ by [Mohammed Sarim](https://github.com/exc33ded).

---

## License

MIT License

---

## Contributing

Contributions are welcome! Submit a Pull Request with your improvements.

---

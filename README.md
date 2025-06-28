# 5D Audio Story Processor

This project creates an immersive audio experience by converting text stories into spatial audio with 5D/8D effects. It uses AI-powered text-to-speech conversion combined with advanced audio processing techniques to create a unique listening experience.

## Features

- Text-to-speech conversion using Unreal Speech API
- Multiple character voices support
- Spatial audio effects (5D/8D)
- Reverb and normalization
- Dynamic panning for immersive experience

## Prerequisites

- Python 3.8 or higher
- Unreal Speech API key

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd Audio-5D
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your Unreal Speech API key:
   - Sign up at [Unreal Speech](https://unrealspeech.com/)
   - Get your API key
   - Set it as an environment variable:
     ```bash
     # Windows
     set UNREAL_SPEECH_API_KEY=your_api_key_here
     
     # Linux/Mac
     export UNREAL_SPEECH_API_KEY=your_api_key_here
     ```

## Usage

1. Import the AudioProcessor class:
```python
from audio_processor import AudioProcessor
```

2. Create an instance with your API key:
```python
processor = AudioProcessor(api_key='your_api_key_here')  # Optional if set as env variable
```

3. Process a story:
```python
story = """
Narrator: In a world of endless possibilities...
Male Character: I've discovered something extraordinary!
Female Character: What could it be?
Narrator: The air crackled with excitement as they gathered around.
"""

processed_audio = processor.process_story(story)
processor.save_audio(processed_audio, 'output_story.mp3')
```

## Customization

You can customize various aspects of the audio processing:

- Voice selection for different characters
- Spatial effect parameters
- Reverb settings
- Audio quality settings

Check the `audio_processor.py` file for available options and parameters.

## Technical Details

The project uses several audio processing techniques:

1. **Text-to-Speech Conversion**
   - Utilizes Unreal Speech API for high-quality voice synthesis
   - Supports multiple voices for different characters

2. **Spatial Audio Processing**
   - Dynamic panning for 5D/8D effect
   - Customizable oscillation rate
   - Stereo enhancement

3. **Audio Effects**
   - Reverb for depth and atmosphere
   - Volume normalization
   - Cross-fading between segments

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
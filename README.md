🤟 ASL Sign Language Viewer

A beginner-level AI project that converts spoken audio into American Sign Language (ASL) — word by word.

What it does

The program provides two modes:

* 🎵 Audio File Mode — Select an audio file and convert the speech into text.
* 🎤 Live Microphone Mode — Record speech through the microphone in short chunks and convert it into text.

After transcription:

* Whisper AI converts speech into text.
* A webpage opens automatically.
* Each word is displayed as a clickable card.
* Click a word to view its ASL sign.
* Full captions are displayed at the top.
* Links to ASL sign resources are provided for each word.

Tech Stack

Tool	Purpose
Python	Core programming language
OpenAI Whisper	Speech-to-text
tkinter	File picker and user interface
HTML + JavaScript	Webpage and interactive sign viewer
sounddevice	Microphone audio recording
NumPy	Audio data processing
ffmpeg	Audio decoding

How to Run

1. Install ffmpeg

On macOS:

brew install ffmpeg

2. Install Python dependencies

Open Terminal and run:

pip3 install -r requirements.txt

3. Run the program

python3 sign_language.py

4. Choose a mode

A window will appear with two options:

* Audio File — Select an .mp3, .wav, .m4a, .ogg, or .flac file.
* Live Microphone — Record speech using your microphone.

The browser will open automatically with the generated sign language page.

Project Structure

Sign_Language_Project/
├── sign_language.py       # Main Python program
├── README.md              # Project documentation
├── requirements.txt       # Python dependencies
│
└── demo/
    ├── Demo.mp3           # Sample audio file
    └── harvard.wav        # Sample audio file

How It Works

Audio / Microphone
        ↓
   Whisper AI
        ↓
   Speech-to-Text
        ↓
    Individual Words
        ↓
   Interactive Webpage
        ↓
    ASL Sign Resources

Notes

* The project uses the Whisper base model for speech recognition.
* An internet connection may be required when Whisper needs to download the model.
* ffmpeg is required for processing supported audio formats.
* The project is intended as a beginner-level educational/expo project.

Built By

Ashwin

A beginner-level AI project developed for an educational expo.
# 🎙️ VoiceBox — Local Text-to-Speech Studio

VoiceBox is a fully offline text-to-speech tool powered by Piper TTS, wrapped in a clean, lightweight Flask UI. No accounts. No API keys. No internet dependency. Just text → speech running locally on your machine.

## ✨ Features

- 🎤 Fully offline text-to-speech conversion
- 🔊 Built-in voice model selector
- ⚙️ Adjustable speed and pause timing
- 🎧 Optional audio enhancements:
  - Noise reduction
  - Volume normalization
  - Clarity enhancement
- 🎛 Simple browser-based UI (Light/Dark themes)
- 💾 Automatic file saving with timestamps
- ⚡ Fast inference using Piper models

## 🖥️ Supported Platforms

| OS | Status |
|---|---|
| Windows 10/11 | ✅ Tested |
| Linux | ⚠ Works but not tested |
| macOS (M1/M2) | ❓ Untested |

## 🔧 Minimum System Requirements

| Component | Recommended |
|---|---|
| CPU | Any modern CPU (Intel i5 / Ryzen 5 or above) |
| RAM | 4GB min (8GB recommended) |
| Storage | ~200MB + space for downloaded models |
| Python | 3.10+ |

Works on low-end laptops too — Piper is lightweight compared to most neural TTS engines.

## 📂 Project Structure

```
VoiceBox/
├── output/                # Generated audio files
├── piper_models/          # Piper .onnx / .json files
├── static/                # UI assets
├── templates/             # HTML UI
├── app.py                 # Flask app
├── tts.py                 # TTS logic wrapper
└── README.md
```

## 📦 Installation

You need Python 3.10+ installed.

### 1️⃣ Clone the project:

```bash
git clone https://github.com/netguy001/Audiobox.git
cd VoiceBox
```

### 2️⃣ Create and activate a virtual environment (recommended):

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3️⃣ Install dependencies:

```bash
pip install -r requirements.txt
```

## ▶️ Running the App

```bash
python app.py
```

The app will automatically open in your browser at:

```
http://localhost:5005
```

## 🎤 Downloading Voice Models

Voice models are not included (they're big). Download from:

- https://github.com/rhasspy/piper
- https://huggingface.co/rhasspy/piper-voices

Place downloaded `.onnx` and `.json` files here:

```
piper_models/
```

Example:

```
piper_models/en_US-danny-low.onnx
```

## 🛠 Upcoming Features

- 🔥 SSML-like markup support
- 🎭 Voice emotion/style presets
- 🌍 Multi-language UI
- 🧱 Windows EXE build
- 🚀 Auto model downloader

## 🤝 Contributing

PRs, ideas, and UI improvements are welcome. If you break something and fix it — even better.

## 📄 License

MIT — do whatever, just don't sue me.

## 📸 Screenshots & Demos

Check out the `ui_images/` folder for:
- 🖼️ Application UI screenshots (light/dark themes)
- 🖥️ Terminal/console output examples
- 🎵 Sample generated audio output

These will give you a quick preview of what VoiceBox looks like in action!

## 🎬 Perfect for Content Creation

VoiceBox is ideal for:
- 🎥 YouTube explanation videos and tutorials
- 🎙️ Podcast intros/outros
- 📚 Audiobook narration
- 🎮 Game voiceovers
- 🔊 Accessibility tools

**Need customization?** This tool is designed to be easily modified for your specific content creation workflow. Feel free to fork and adapt it to your needs!

## 💬 Questions or Feedback?

Have questions about functionality, customization, or how to integrate VoiceBox into your workflow? 

**Contact me:**
- Open an issue on GitHub
- Reach out directly for collaboration or custom features

I'm happy to help with implementation details, feature requests, or technical guidance!

## 👤 Author

**Meganathan M**  
Cloud · AI · Automation
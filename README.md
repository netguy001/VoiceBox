# **Piper TTS Studio**

A fully offline text-to-speech interface powered by **Piper TTS**.
No API keys. No cloud calls. No tracking.
Just fast, local inference — running on your hardware.

---

## 🚀 What This Does

* Convert text to natural-sounding speech locally
* Switch between multiple voices (if models available)
* Control speaking speed and pause timing
* Enable audio enhancements (normalization, clarity, noise reduction)
* Export generated audio for reuse
* Runs entirely in the browser at: `http://localhost:5005`

If you’re tired of cloud-locked TTS tools or overpriced subscriptions — this is your alternative.

---

## 🧩 Tech Used

| Layer      | Tech                                                    |
| ---------- | ------------------------------------------------------- |
| Backend    | Python (FastAPI/Flask depending on your implementation) |
| TTS Engine | Piper                                                   |
| Frontend   | HTML + CSS + JS (lightweight UI)                        |
| Extras     | FFmpeg (audio processing), Local model inference        |

---

## 📦 Folder Structure

```
piper-tts-studio/
│
├── backend/
│   ├── app.py
│   ├── inference.py
│   └── requirements.txt
│
├── templates/ (UI)
├── piper_models/ (Not included — user downloads models)
├── scripts/ (optional helpers)
└── README.md
```

---

## 🎤 Models (IMPORTANT)

Models are **NOT included** because they're **huge** (multiple GB).

To run this project, download models from:

* [https://github.com/rhasspy/piper](https://github.com/rhasspy/piper)
* [https://huggingface.co/rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices)

Place downloaded `.onnx` voice models here:

```
piper_models/
```

Example:

```
piper_models/
 └── en_US-danny-low.onnx
```

---

## ▶️ How to Run

1. Install dependencies:

```
pip install -r backend/requirements.txt
```

2. Start the server:

```
python backend/app.py
```

3. Open the UI in your browser:

```
http://localhost:5005
```

That’s it.

---

## 🔧 Optional (FFmpeg Required)

Some enhancement features use FFmpeg.

Install:

* **Windows:** [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
* **Linux:** `sudo apt install ffmpeg`
* **Mac:** `brew install ffmpeg`

---

## 🛠 Planned Improvements

* 🔉 Emotion/style markers (SSML-like control)
* 🎛 UI presets for voices & tonal options
* 📦 One-click installer
* 🧠 Model auto-downloader
* 🎚 Voice mixing & chaining

---

## 🤝 Contributing

If you have voice models, improvements, UI fixes, or ideas — PRs are welcome.

---

## 📄 License

MIT — use it, break it, improve it, ship it.

---

## 👤 Author

**Meganathan M**

Backend • Cloud • AI-assisted Engineering
GitHub: [https://github.com/netguy001](https://github.com/netguy001)


from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

# Your existing routes here...


# Add this route for assets
@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory("assets", filename)


from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import os
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile
import datetime
import webbrowser
import threading
import time

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "piper_models"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


def scan_voice_models():
    """Scan for available Piper voice models"""
    models = []

    if MODELS_DIR.exists():
        for file in MODELS_DIR.glob("*.onnx"):
            if file.with_suffix(".onnx.json").exists():
                models.append({"name": file.stem, "path": str(file)})

    for file in BASE_DIR.glob("*.onnx"):
        if file.with_suffix(".onnx.json").exists():
            models.append({"name": file.stem, "path": str(file.absolute())})

    return models


def enhance_audio(input_file, output_file, noise_reduction, normalize, enhance_clarity):
    """Apply audio enhancements"""
    try:
        sample_rate, audio_data = wavfile.read(input_file)

        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32)
        else:
            audio_float = audio_data.astype(np.float32)

        if noise_reduction:
            try:
                sos = signal.butter(2, 100, "hp", fs=sample_rate, output="sos")
                audio_float = signal.sosfilt(sos, audio_float)
            except:
                pass

        if enhance_clarity:
            try:
                sos = signal.butter(1, [2000, 6000], "bp", fs=sample_rate, output="sos")
                clarity_boost = signal.sosfilt(sos, audio_float) * 0.15
                audio_float = audio_float + clarity_boost
            except:
                pass

        if normalize:
            max_val = np.abs(audio_float).max()
            if max_val > 1000:
                rms = np.sqrt(np.mean(audio_float**2))
                if rms > 0:
                    target_rms = 3000
                    audio_float = audio_float * (target_rms / rms)
                    max_after = np.abs(audio_float).max()
                    if max_after > 32000:
                        audio_float = audio_float * (32000 / max_after)

        audio_float = np.clip(audio_float, -32767, 32767)
        enhanced_audio = audio_float.astype(np.int16)

        wavfile.write(output_file, sample_rate, enhanced_audio)
        return True

    except Exception as e:
        print(f"Enhancement failed: {e}")
        import shutil

        shutil.copy(input_file, output_file)
        return False


# ROUTES
@app.route("/")
def index():
    """Serve the main page"""
    return render_template("index.html")


@app.route("/api/voices", methods=["GET"])
def get_voices():
    """Get available voice models"""
    models = scan_voice_models()
    return jsonify({"voices": models})


@app.route("/api/generate", methods=["POST"])
def generate_speech():
    """Generate speech from text"""
    try:
        data = request.json
        text = data.get("text", "").strip()
        voice_path = data.get("voice_path", "")
        speed = float(data.get("speed", 1.0))
        pause = float(data.get("pause", 0.2))
        noise_reduction = data.get("noise_reduction", True)
        normalize = data.get("normalize", True)
        enhance_clarity = data.get("enhance_clarity", True)

        if not text:
            return jsonify({"error": "No text provided"}), 400

        if not voice_path or not os.path.exists(voice_path):
            return jsonify({"error": "Voice model not found"}), 400

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = OUTPUT_DIR / f"temp_{timestamp}.wav"
        output_file = OUTPUT_DIR / f"output_{timestamp}.wav"

        cmd = [
            "piper",
            "--model",
            voice_path,
            "--output_file",
            str(temp_file),
            "--length_scale",
            str(1.0 / speed),
            "--sentence_silence",
            str(pause),
        ]

        result = subprocess.run(
            cmd, input=text, text=True, capture_output=True, encoding="utf-8"
        )

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "Unknown error"
            return jsonify({"error": f"Piper failed: {error_msg}"}), 500

        if noise_reduction or normalize or enhance_clarity:
            enhance_audio(
                str(temp_file),
                str(output_file),
                noise_reduction,
                normalize,
                enhance_clarity,
            )
            if temp_file.exists():
                temp_file.unlink()
        else:
            temp_file.rename(output_file)

        return jsonify(
            {"success": True, "filename": output_file.name, "path": str(output_file)}
        )

    except FileNotFoundError:
        return (
            jsonify({"error": "Piper not found. Install with: pip install piper-tts"}),
            500,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/audio/<filename>")
def get_audio(filename):
    """Serve audio file"""
    return send_from_directory(OUTPUT_DIR, filename)


@app.route("/api/outputs")
def list_outputs():
    """List all generated audio files"""
    files = []
    if OUTPUT_DIR.exists():
        for file in OUTPUT_DIR.glob("output_*.wav"):
            files.append(
                {
                    "filename": file.name,
                    "size": file.stat().st_size,
                    "created": file.stat().st_mtime,
                }
            )
    files.sort(key=lambda x: x["created"], reverse=True)
    return jsonify({"files": files})


def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5005")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  PIPER TTS WEB SERVER")
    print("=" * 60)
    print(f"  Output: {OUTPUT_DIR.absolute()}")
    print(f"  Models: {MODELS_DIR.absolute()}")
    print(f"  URL: http://localhost:5005")
    print("=" * 60 + "\n")

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(debug=False, host="127.0.0.1", port=5005)

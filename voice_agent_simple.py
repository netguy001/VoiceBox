"""
Simple Local Voice Agent
Uses: Google Speech Recognition → Ollama → Piper TTS
Requires brief internet for speech recognition only
"""

import speech_recognition as sr
import subprocess
import os
from pathlib import Path
import wave
import pyaudio
import requests
import json
import datetime
import threading


class SimpleVoiceAgent:
    def __init__(self, ollama_model="mistral", voice_model_path=None):
        """
        Initialize simple voice agent

        Args:
            ollama_model: Name of Ollama model (mistral, llama2, etc.)
            voice_model_path: Path to Piper voice model
        """
        self.ollama_model = ollama_model

        # Auto-detect voice model if not provided
        if voice_model_path is None:
            voice_model_path = self.find_voice_model()

        self.voice_model_path = voice_model_path

        # Setup directories
        self.output_dir = Path("voice_output")
        self.output_dir.mkdir(exist_ok=True)

        # Audio settings
        self.is_speaking = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True

        # Conversation history
        self.conversation_history = []

        print("\n" + "=" * 60)
        print("🤖 SIMPLE VOICE AGENT STARTED")
        print("=" * 60)
        print(f"🧠 LLM Model: {ollama_model}")
        print(
            f"🎙️ Voice Model: {Path(voice_model_path).stem if voice_model_path else 'Not found'}"
        )
        print(f"📁 Output Dir: {self.output_dir.absolute()}")
        print("=" * 60 + "\n")

    def find_voice_model(self):
        """Auto-detect first available voice model"""
        models_dir = Path("piper_models")

        if models_dir.exists():
            for model_file in models_dir.glob("*.onnx"):
                if model_file.with_suffix(".onnx.json").exists():
                    return str(model_file)

        # Check current directory
        for model_file in Path(".").glob("*.onnx"):
            if model_file.with_suffix(".onnx.json").exists():
                return str(model_file.absolute())

        return None

    def listen(self):
        """Listen to microphone and convert speech to text"""
        print("🎤 Listening... (speak now)")

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                # Listen for audio
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)

                print("🔄 Processing speech...")

                # Recognize speech using Google
                text = self.recognizer.recognize_google(audio)

                print(f"✅ You said: {text}")
                return text

        except sr.WaitTimeoutError:
            print("⏱️ No speech detected (timeout)")
            return None
        except sr.UnknownValueError:
            print("❌ Could not understand audio")
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def ask_ollama(self, user_message):
        """Send message to Ollama and get response"""
        print(f"🧠 Thinking with {self.ollama_model}...")

        try:
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_message})

            # Prepare the prompt with history
            messages = self.conversation_history.copy()

            # Call Ollama API
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                ai_response = result["message"]["content"]

                # Add AI response to history
                self.conversation_history.append(
                    {"role": "assistant", "content": ai_response}
                )

                print(f"💬 AI: {ai_response}")
                return ai_response
            else:
                print(f"❌ Ollama error: {response.status_code}")
                return "Sorry, I encountered an error."

        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama. Is it running?")
            return "I cannot connect to my brain right now."
        except Exception as e:
            print(f"❌ Error: {e}")
            return "Sorry, something went wrong."

    def speak(self, text):
        """Convert text to speech using Piper TTS"""
        if not self.voice_model_path:
            print("❌ No voice model available")
            return False

        print("🎙️ Generating speech...")

        try:
            # Generate unique filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"response_{timestamp}.wav"

            # Run Piper TTS
            cmd = [
                "piper",
                "--model",
                self.voice_model_path,
                "--output_file",
                str(output_file),
                "--length_scale",
                "1.0",
                "--sentence_silence",
                "0.2",
            ]

            result = subprocess.run(
                cmd, input=text, text=True, capture_output=True, encoding="utf-8"
            )

            if result.returncode == 0 and output_file.exists():
                print("🔊 Playing response...")
                # Play audio directly (not in thread)
                self._play_audio(str(output_file))
                return True
            else:
                print(f"❌ TTS failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Speech generation error: {e}")
            return False

    def _play_audio(self, audio_file):
        """Play audio file"""
        try:
            print(f"📂 Opening audio file: {audio_file}")
            wf = wave.open(audio_file, "rb")
            p = pyaudio.PyAudio()

            print(
                f"🔊 Audio info: {wf.getnchannels()} channels, {wf.getframerate()} Hz"
            )

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            print("▶️ Playing audio...")

            # Read and play audio
            chunk = 1024
            data = wf.readframes(chunk)

            while data:
                stream.write(data)
                data = wf.readframes(chunk)

            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            print("✅ Playback finished\n")

        except Exception as e:
            print(f"❌ Playback error: {e}")
            import traceback

            traceback.print_exc()

    def run(self):
        """Main conversation loop"""
        print("💡 Say 'exit', 'quit', or 'goodbye' to stop")
        print("💡 Press Ctrl+C to force quit\n")

        try:
            while True:
                # Listen for user input
                user_text = self.listen()

                if user_text is None:
                    continue

                # Check for exit commands
                if user_text.lower() in ["exit", "quit", "goodbye", "bye", "stop"]:
                    farewell = "Goodbye! Have a great day!"
                    print(f"👋 {farewell}")
                    self.speak(farewell)
                    break

                # Get AI response
                ai_response = self.ask_ollama(user_text)

                # Speak the response
                self.speak(ai_response)

                print("\n" + "-" * 60 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Voice agent stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")


def main():
    """Entry point"""
    import sys

    # Parse command line arguments
    ollama_model = "mistral"  # Default

    if len(sys.argv) > 1:
        ollama_model = sys.argv[1]

    print("\n🚀 Starting Simple Voice Agent...")
    print(f"📝 Usage: python voice_agent_simple.py [model_name]")
    print(f"📝 Example: python voice_agent_simple.py llama2\n")

    # Create and run agent
    agent = SimpleVoiceAgent(ollama_model=ollama_model)

    if agent.voice_model_path is None:
        print("\n❌ ERROR: No voice model found!")
        print("💡 Download a voice model to piper_models/ first")
        print("💡 Visit: https://github.com/rhasspy/piper")
        return

    agent.run()


if __name__ == "__main__":
    main()

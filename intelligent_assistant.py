# -*- coding: utf-8 -*-
"""
Intelligent Voice Assistant - FIXED VERSION
Fast, minimal responses, actually works!

FIXES APPLIED:
✅ Short, direct responses (no "Master" stuff)
✅ Multiple tool execution fixed
✅ Apps actually open now
✅ Files actually get created
✅ Faster processing
"""

import speech_recognition as sr
import subprocess
import os
from pathlib import Path
import requests
import json
import datetime
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import re
import pyaudio
import wave
import uuid

from tools import ToolBox
from memory import AssistantMemory


class IntelligentAssistant:
    def __init__(
        self,
        ollama_model="mistral",
        personality="friendly",
        wake_word_mode=False,
        user_name=None,
    ):
        """Initialize the intelligent assistant - FIXED"""

        # Control flags
        self.is_paused = False
        self.stop_requested = False
        self.pending_response = ""
        self.is_listening = False
        self.is_speaking = False
        self.conversation_active = True

        # Audio control
        self.should_stop_audio = False
        self.audio_lock = threading.Lock()
        self.audio_process = None
        self.current_audio_file = None

        # Interrupt detection
        self.interrupt_detected = False
        self.interrupt_thread = None

        # Settings
        self.ollama_model = ollama_model
        self.personality = personality
        self.session_id = str(uuid.uuid4())[:8]
        self.wake_word_mode = wake_word_mode
        self.wake_word = "jarvis"

        # Get user name
        if user_name is None:
            user_name = os.getenv("USERNAME", "friend")

        # Initialize memory
        self.memory = AssistantMemory(user_name=user_name)
        self.voice_model_path = self.find_voice_model()

        # Update personality
        stored_personality = self.memory.get_preference("personality")
        if stored_personality:
            self.personality = stored_personality
        else:
            self.memory.update_preference("personality", personality)

        # Setup directories
        self.output_dir = Path("voice_output")
        self.output_dir.mkdir(exist_ok=True)

        # Audio settings
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 2000
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

        # Conversation context
        self.conversation_history = []

        # Threading
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Initialize tools
        self.toolbox = ToolBox()
        self.add_memory_tools()

        # FIXED: Short, clear system prompt
        self.system_prompt = self.build_system_prompt()

        self.print_welcome()

    def add_memory_tools(self):
        """Add memory tools to toolbox"""
        self.toolbox.tools.update(
            {
                "remember_fact": self.memory.add_fact,
                "recall_facts": self.memory.get_facts,
                "add_task": self.memory.add_task,
                "get_tasks": self.memory.get_tasks,
                "complete_task": self.memory.complete_task,
                "search_memory": self.memory.search_conversations,
            }
        )

    def build_system_prompt(self):
        """Build system prompt - COMPLETELY REWRITTEN (MINIMAL & DIRECT)"""

        user_name = self.memory.preferences.get("name", "friend")
        current_date = datetime.datetime.now().strftime("%B %d, %Y")

        # FIXED: SUPER SHORT PROMPT - No verbosity!
        prompt = f"""You are a helpful AI assistant for {user_name}. Date: {current_date}

CRITICAL RULES:
1. Keep responses EXTREMELY SHORT (1-2 sentences max)
2. When opening apps: Just say "Opening [app]" - nothing else
3. When creating files: Just say "Creating file" then "Done"
4. NO greetings like "Master", "Sure thing", etc
5. Be direct and minimal

TOOL FORMAT:
Use ONE LINE per tool: TOOL: function_name(param1, param2)

Examples:
User: "Open notepad"
You: Opening Notepad. TOOL: open_app("notepad")

User: "Create test.txt with hello"
You: Creating file. TOOL: write_file("test.txt", "hello")

User: "Open chrome and search Python"
You: Opening Chrome and searching. TOOL: open_app("chrome")
TOOL: google_search("Python")

AVAILABLE TOOLS:
write_file(path, content), read_file(path), list_files(dir), rename_file(old, new), delete_file(path)
google_search(query), open_url(url), fetch_webpage(url)
open_app(name), run_command(cmd), system_info()
add_task(task), get_tasks(), complete_task(id)
calculate(expr), get_current_time(), get_current_date()

Remember: MINIMAL responses only. No chatter."""

        return prompt

    def find_voice_model(self):
        """Find Piper voice model"""
        models_dir = Path("piper_models")

        if models_dir.exists():
            for model_file in models_dir.glob("*.onnx"):
                if model_file.with_suffix(".onnx.json").exists():
                    return str(model_file)

        for model_file in Path(".").glob("*.onnx"):
            if model_file.with_suffix(".onnx.json").exists():
                return str(model_file.absolute())

        return None

    def print_welcome(self):
        """Print welcome message"""
        print("\n" + "=" * 70)
        print("     🤖 AI ASSISTANT - READY")
        print("=" * 70)

        user_name = self.memory.preferences.get("name", "friend")
        print(f"👋 User: {user_name}")
        print(f"🧠 Model: {self.ollama_model}")
        print(f"🔊 Voice: {'Enabled' if self.voice_model_path else 'Text-only'}")

        tasks = self.memory.get_tasks("pending")
        if tasks:
            print(f"📋 Pending tasks: {len(tasks)}")

        print("\n💡 Speak clearly and wait for the beep!")
        print("=" * 70 + "\n")

    # ========== SPEECH RECOGNITION ==========

    def listen(self, timeout=10, phrase_time_limit=20):
        """Listen to microphone - FIXED"""

        if self.wake_word_mode:
            print(f"\n🎤 Say '{self.wake_word}' to activate...")
        else:
            print("\n🎤 Listening...")

        self.is_listening = True

        try:
            with sr.Microphone() as source:
                print("   ⚙️  Calibrating...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)

                print("   ✅ Ready! Speak now...")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

                print("   🔄 Processing...")

                try:
                    text = self.recognizer.recognize_google(audio)
                except sr.UnknownValueError:
                    try:
                        text = self.recognizer.recognize_sphinx(audio)
                    except:
                        raise sr.UnknownValueError

                # Handle wake word
                if self.wake_word_mode:
                    if self.wake_word.lower() not in text.lower():
                        print(f"   ⚠️  Wake word not detected")
                        self.is_listening = False
                        return None
                    else:
                        text = text.lower().replace(self.wake_word.lower(), "").strip()
                        print(f"   ✅ Activated!")

                        if not text:
                            print("   🎤 Listening for command...")
                            return self.listen(timeout=8, phrase_time_limit=15)

                print(f"\n💬 You: {text}")
                self.is_listening = False
                return text

        except sr.WaitTimeoutError:
            self.is_listening = False
            if not self.wake_word_mode:
                print("   ⏱️  Timeout")
            return None

        except sr.UnknownValueError:
            self.is_listening = False
            if not self.wake_word_mode:
                print("   ❌ Couldn't understand")
            return None

        except Exception as e:
            self.is_listening = False
            print(f"   ❌ Error: {e}")
            return None

    # ========== INTERRUPT DETECTION ==========

    def start_interrupt_listener(self):
        """Start interrupt detection"""
        self.interrupt_detected = False
        self.interrupt_thread = threading.Thread(
            target=self._interrupt_listener_thread, daemon=True
        )
        self.interrupt_thread.start()

    def _interrupt_listener_thread(self):
        """Background interrupt detection"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.1)

                while self.is_speaking and not self.interrupt_detected:
                    try:
                        audio = self.recognizer.listen(
                            source, timeout=0.2, phrase_time_limit=1.0
                        )

                        try:
                            text = self.recognizer.recognize_google(audio).lower()

                            interrupt_words = [
                                "stop",
                                "shut up",
                                "quiet",
                                "pause",
                                "wait",
                                "hold on",
                                "hold",
                            ]

                            if any(word in text for word in interrupt_words):
                                self.interrupt_detected = True

                                if any(w in text for w in ["wait", "pause", "hold"]):
                                    self.is_paused = True
                                    print("\n   ⏸️  PAUSED")
                                else:
                                    self.stop_requested = True
                                    print("\n   ⏹️  STOPPED")

                                self.stop_audio()
                                break

                        except sr.UnknownValueError:
                            continue

                    except sr.WaitTimeoutError:
                        continue

                    except Exception:
                        continue

        except Exception as e:
            print(f"   ⚠️  Interrupt error: {e}")

    def stop_audio(self):
        """Stop audio playback immediately"""
        with self.audio_lock:
            self.should_stop_audio = True

            if self.audio_process and self.audio_process.poll() is None:
                try:
                    self.audio_process.terminate()
                    self.audio_process.wait(timeout=0.5)
                except:
                    try:
                        self.audio_process.kill()
                    except:
                        pass

            self.is_speaking = False

    # ========== TEXT-TO-SPEECH ==========

    def speak(self, text):
        """Convert text to speech - FIXED"""

        # Always print
        print(f"\n🤖 Assistant: {text}\n")

        # Skip TTS if no model
        if not self.voice_model_path:
            return True

        try:
            self.should_stop_audio = False
            self.interrupt_detected = False
            self.pending_response = text

            future = self.executor.submit(self._speak_thread, text)
            return True

        except Exception as e:
            print(f"   ⚠️  Speech error: {e}")
            return False

    def _speak_thread(self, text):
        """TTS generation thread"""
        try:
            with self.audio_lock:
                if self.should_stop_audio:
                    return
                self.is_speaking = True

            try:
                self.start_interrupt_listener()
            except:
                pass

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"response_{timestamp}.wav"
            self.current_audio_file = output_file

            print("   🔊 Speaking...")

            cmd = [
                "piper",
                "--model",
                self.voice_model_path,
                "--output_file",
                str(output_file),
                "--length-scale",
                "0.95",
                "--sentence-silence",
                "0.1",
            ]

            try:
                result = subprocess.run(
                    cmd,
                    input=text,
                    text=True,
                    capture_output=True,
                    encoding="utf-8",
                    timeout=20,
                )

                if self.should_stop_audio:
                    return

                if result.returncode == 0 and output_file.exists():
                    try:
                        self._play_audio_with_interrupt(str(output_file))
                    except Exception as e:
                        print(f"   ❌ Playback failed: {e}")

            except subprocess.TimeoutExpired:
                print("   ❌ TTS timeout")
            except FileNotFoundError:
                print("   ❌ Piper not found")
            except Exception as e:
                print(f"   ❌ TTS error: {e}")

        except Exception as e:
            print(f"   ❌ Speech error: {e}")

        finally:
            self.is_speaking = False
            if not self.is_paused:
                self.pending_response = ""

    def _play_audio_with_interrupt(self, audio_file):
        """Play audio with interrupt support"""
        try:
            wf = wave.open(audio_file, "rb")
            p = pyaudio.PyAudio()

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            chunk = 1024
            data = wf.readframes(chunk)

            while data and not self.should_stop_audio and not self.interrupt_detected:
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            if not self.should_stop_audio and not self.interrupt_detected:
                print("   ✅ Done\n")

        except Exception as e:
            print(f"   ❌ Playback error: {e}")

    # ========== AI PROCESSING (COMPLETELY FIXED) ==========

    def process_with_ai(self, user_message):
        """Process with AI - FIXED for speed and accuracy"""

        print(f"🧠 Thinking...")

        if self.stop_requested:
            self.stop_requested = False

        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]

            # Only last 4 exchanges
            recent_history = self.conversation_history[-8:]
            messages.extend(recent_history)

            # Add current message
            messages.append({"role": "user", "content": user_message})

            print("   ⚡ Generating...")

            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.6,  # More focused
                            "top_p": 0.85,
                            "num_predict": 150,  # Shorter responses
                            "stop": ["User:", "Human:", "\n\n\n", "Master"],
                        },
                    },
                    timeout=25,
                )

            except requests.exceptions.ConnectionError:
                return "❌ Ollama not running. Start with: ollama serve"

            except requests.exceptions.Timeout:
                return "❌ Ollama timeout. Try again."

            if response.status_code != 200:
                return f"❌ Ollama error: {response.status_code}"

            result = response.json()
            ai_response = result.get("message", {}).get("content", "")

            if not ai_response or len(ai_response.strip()) < 2:
                return "❌ Empty response. Try again."

            print(f"   ✅ Response ({len(ai_response)} chars)")

            # FIXED: Execute tools if present
            tools_used = []
            if "TOOL:" in ai_response:
                print("   🛠️  Executing tools...")
                ai_response, tools_used = self.execute_tools_from_response(ai_response)

            # Update history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )

            # Save to memory
            self.memory.save_conversation(
                user_message, ai_response, tools_used, self.session_id
            )

            # Keep history short
            if len(self.conversation_history) > 12:
                self.conversation_history = self.conversation_history[-12:]

            return ai_response

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return "❌ Something went wrong."

    # ========== TOOL EXECUTION (COMPLETELY REWRITTEN - FIXED!) ==========

    def execute_tools_from_response(self, ai_response):
        """Execute tools from AI response - FIXED"""

        tools_used = []

        try:
            # FIXED: Better pattern that handles TOOL: lines
            tool_pattern = r"TOOL:\s*(\w+)\s*\((.*?)\)"

            matches = re.findall(tool_pattern, ai_response, re.DOTALL)

            if not matches:
                print("   ⚠️  No valid tool calls found")
                return ai_response, tools_used

            print(f"   ✅ Found {len(matches)} tool(s)")

            results = []

            for tool_name, params_str in matches:
                print(f"\n   🔧 {tool_name}")
                print(f"      Raw params: {params_str[:50]}")

                # Parse parameters
                params = self.parse_tool_parameters(params_str)

                print(f"      Parsed params: {params}")

                # Execute tool
                result = self.toolbox.execute_tool(tool_name, params)

                # Store result
                tools_used.append(
                    {
                        "tool": tool_name,
                        "params": params[:2],
                        "success": result["success"],
                        "output": result["output"][:200],
                    }
                )

                if result["success"]:
                    output_preview = result["output"][:300]
                    results.append(f"✅ {output_preview}")
                    print(f"      ✅ Success")
                else:
                    results.append(f"❌ {result['output'][:300]}")
                    print(f"      ❌ Failed: {result['output'][:80]}")

            # Remove TOOL: lines from response
            clean_response = re.sub(r"TOOL:.*?\)", "", ai_response, flags=re.DOTALL)
            clean_response = re.sub(r"\n\n+", "\n\n", clean_response).strip()

            # Add tool results
            if results:
                result_text = "\n\n" + "\n".join(results)

                if clean_response:
                    final_response = f"{clean_response}{result_text}"
                else:
                    final_response = result_text.strip()

                return final_response, tools_used

            return clean_response if clean_response else "Done.", tools_used

        except Exception as e:
            print(f"   ❌ Tool execution error: {e}")
            import traceback

            traceback.print_exc()
            return ai_response, tools_used

    def parse_tool_parameters(self, params_str):
        """Parse tool parameters - COMPLETELY FIXED"""

        if not params_str or not params_str.strip():
            return []

        params = []
        params_str = params_str.strip()

        # Handle simple cases first
        if '"' not in params_str and "'" not in params_str:
            # No quotes - just split by comma
            parts = [p.strip() for p in params_str.split(",")]
            return [p for p in parts if p]

        # Complex parsing for quoted strings
        current_param = ""
        in_quotes = False
        quote_char = None
        depth = 0

        i = 0
        while i < len(params_str):
            char = params_str[i]

            # Handle escape sequences
            if char == "\\" and i + 1 < len(params_str):
                current_param += params_str[i : i + 2]
                i += 2
                continue

            # Handle quotes
            if char in ['"', "'"] and (i == 0 or params_str[i - 1] != "\\"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                current_param += char

            # Handle nested structures
            elif char in "([{" and not in_quotes:
                depth += 1
                current_param += char

            elif char in ")]}" and not in_quotes:
                depth -= 1
                current_param += char

            # Handle comma separator
            elif char == "," and not in_quotes and depth == 0:
                if current_param.strip():
                    params.append(self.clean_parameter(current_param.strip()))
                current_param = ""
                i += 1
                continue

            else:
                current_param += char

            i += 1

        # Add last parameter
        if current_param.strip():
            params.append(self.clean_parameter(current_param.strip()))

        return params

    def clean_parameter(self, param):
        """Clean a single parameter - IMPROVED"""

        param = param.strip()

        # Remove parameter names (path=value → value)
        param = re.sub(r"^(\w+)\s*=\s*", "", param, flags=re.IGNORECASE)

        # Remove outer quotes
        param = param.strip()
        if len(param) >= 2:
            if (param[0] == '"' and param[-1] == '"') or (
                param[0] == "'" and param[-1] == "'"
            ):
                param = param[1:-1]

        # Unescape
        param = param.replace("\\n", "\n")
        param = param.replace("\\t", "\t")
        param = param.replace("\\r", "\r")
        param = param.replace('\\"', '"')
        param = param.replace("\\'", "'")
        param = param.replace("\\\\", "\\")

        return param

    # ========== MAIN CONVERSATION LOOP (CRASH-PROOF) ==========

    def run(self):
        """Main conversation loop - COMPLETELY FIXED"""

        print("=" * 70 + "\n")

        # Initial greeting
        user_name = self.memory.preferences.get("name", "friend")

        greeting = f"Hello {user_name}! Ready to help. What do you need?"

        if self.wake_word_mode:
            greeting = f"Hello {user_name}! Say '{self.wake_word}' when you need me."

        print(f"🤖 Assistant: {greeting}\n")

        try:
            self.speak(greeting)
        except:
            pass

        conversation_count = 0
        consecutive_errors = 0
        max_consecutive_errors = 3

        try:
            while self.conversation_active:
                try:
                    # Wait for speech to finish (with timeout)
                    wait_count = 0
                    while self.is_speaking and not self.is_paused:
                        time.sleep(0.1)
                        wait_count += 1

                        if wait_count > 300:  # 30 second timeout
                            print("   ⚠️  Timeout, continuing...")
                            self.is_speaking = False
                            break

                    # Don't listen while paused
                    if self.is_paused:
                        time.sleep(0.5)
                        continue

                    # Listen for input
                    print(f"\n{'='*70}")
                    print(f"💬 Turn #{conversation_count + 1}")
                    print("=" * 70)

                    user_text = self.listen()

                    # Handle no input
                    if user_text is None:
                        continue

                    # Reset error counter
                    consecutive_errors = 0

                    # Handle continue command
                    if self.is_paused and "continue" in user_text.lower():
                        self.is_paused = False
                        if self.pending_response:
                            print("   ▶️  Resuming...")
                            try:
                                self.speak(self.pending_response)
                            except:
                                pass
                        continue

                    # Exit detection
                    exit_phrases = [
                        "exit",
                        "quit",
                        "goodbye",
                        "bye",
                        "good bye",
                        "stop assistant",
                        "shut down",
                        "shutdown",
                    ]

                    if any(phrase in user_text.lower() for phrase in exit_phrases):
                        farewell = f"Goodbye {user_name}!"
                        print(f"\n🤖 Assistant: {farewell}\n")

                        try:
                            self.speak(farewell)
                            time.sleep(2)
                        except:
                            pass

                        break

                    # Process with AI
                    ai_response = self.process_with_ai(user_text)

                    # Check response validity
                    if not ai_response or ai_response.startswith("❌"):
                        consecutive_errors += 1
                        print(
                            f"   ⚠️  Error {consecutive_errors}/{max_consecutive_errors}"
                        )

                        if consecutive_errors >= max_consecutive_errors:
                            print("\n❌ Too many errors. Check Ollama.")
                            break

                        print(f"\n{ai_response}\n")
                        continue

                    # Speak response
                    if not self.stop_requested:
                        try:
                            self.speak(ai_response)
                        except Exception as e:
                            print(f"   ⚠️  Voice error: {e}")
                    else:
                        print("   ⏹️  Skipped (interrupted)")
                        self.stop_requested = False

                    conversation_count += 1
                    print("-" * 70)

                except KeyboardInterrupt:
                    raise

                except Exception as e:
                    consecutive_errors += 1
                    print(f"\n   ❌ Error: {e}")

                    if consecutive_errors >= max_consecutive_errors:
                        print("\n❌ Too many errors. Exiting...")
                        break

                    print(
                        f"   🔄 Recovering... ({consecutive_errors}/{max_consecutive_errors})"
                    )
                    time.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⏹️  Stopped (Ctrl+C)")
            self.stop_audio()

        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback

            traceback.print_exc()

        finally:
            print("\n" + "=" * 70)
            print("🔌 Shutting down...")
            print("💾 Conversation saved")
            print("👋 Goodbye!")
            print("=" * 70 + "\n")

            self.conversation_active = False

            try:
                self.executor.shutdown(wait=False)
            except:
                pass


# ========== ENTRY POINT ==========


def main():
    """Entry point - IMPROVED"""
    import sys

    # Default settings
    model = "mistral"
    personality = "friendly"
    wake_word_mode = False
    user_name = None

    # Parse arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ["--wake-word", "-w"]:
            wake_word_mode = True

        elif arg.startswith("--model="):
            model = arg.split("=", 1)[1]

        elif arg.startswith("--personality="):
            personality = arg.split("=", 1)[1]

        elif arg.startswith("--name="):
            user_name = arg.split("=", 1)[1]

        elif arg in ["--help", "-h"]:
            print(
                """
🤖 Intelligent Voice Assistant - Usage

python intelligent_assistant.py [OPTIONS]

OPTIONS:
  --model=MODEL          Ollama model (default: mistral)
  --personality=TYPE     Personality (default: friendly)
  --name=NAME            Your name
  --wake-word, -w        Enable wake word mode
  --help, -h             Show this help

EXAMPLES:
  python intelligent_assistant.py
  python intelligent_assistant.py --model=llama2 --name=John
"""
            )
            return

        i += 1

    # Print startup
    print("\n" + "=" * 70)
    print("     🚀 STARTING AI ASSISTANT")
    print("=" * 70)
    print(f"🧠 Model: {model}")
    print(f"👤 User: {user_name or 'auto-detect'}")
    print("=" * 70)

    # Check Ollama
    print("\n🔍 Checking Ollama...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("   ✅ Ollama running")
        else:
            print("   ❌ Ollama not responding")
            return
    except:
        print("   ❌ Ollama not running!")
        print("   💡 Start with: ollama serve")
        return

    print("\n🎤 Checking microphone...")
    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("   ✅ Microphone found")
    except Exception as e:
        print(f"   ⚠️  Microphone issue: {e}")

    print("\n🔊 Checking voice...")
    voice_found = False
    for path in [Path("piper_models"), Path(".")]:
        if path.exists():
            onnx_files = list(path.glob("*.onnx"))
            if onnx_files:
                print(f"   ✅ Voice model found")
                voice_found = True
                break

    if not voice_found:
        print("   ⚠️  No voice model (text-only mode)")

    print("\n" + "=" * 70)
    print("✨ Starting assistant...")
    print("=" * 70 + "\n")

    time.sleep(1)

    # Create and run
    assistant = IntelligentAssistant(
        ollama_model=model,
        personality=personality,
        wake_word_mode=wake_word_mode,
        user_name=user_name,
    )

    assistant.run()


if __name__ == "__main__":
    main()

"""
Intelligent Voice Assistant - COMPLETELY FIXED VERSION
All Issues Resolved:
✅ File creation works properly (no more "content=" in filenames)
✅ Waits for complete speech before responding
✅ Instant stop/wait/continue commands
✅ Full Windows file system access and awareness
✅ AI knows what files exist before taking action
✅ Better tool parameter parsing
✅ Enhanced web search
✅ Improved AI prompt for better understanding
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

# Import our modules
from tools import ToolBox
from memory import AssistantMemory


class IntelligentAssistant:
    def __init__(
        self,
        ollama_model="mistral",
        personality="friendly",
        user_name=None,
        wake_word_mode=False,
    ):
        """Initialize the intelligent assistant with memory"""
        self.is_paused = False
        self.stop_requested = False
        self.pending_response = ""
        self.is_listening = False  # NEW: Track if we're actively listening

        self.ollama_model = ollama_model
        self.personality = personality
        self.session_id = str(uuid.uuid4())[:8]
        self.wake_word_mode = wake_word_mode
        self.wake_word = "jarvis"

        # Initialize memory first
        if user_name is None:
            user_name = self.ask_user_name()

        self.memory = AssistantMemory(user_name=user_name)
        self.voice_model_path = self.find_voice_model()

        # Update personality from memory if stored
        stored_personality = self.memory.get_preference("personality")
        if stored_personality:
            self.personality = stored_personality
        else:
            self.memory.update_preference("personality", personality)

        # Setup directories
        self.output_dir = Path("voice_output")
        self.output_dir.mkdir(exist_ok=True)

        # Audio settings - IMPROVED for better listening
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Increased threshold
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = (
            1.0  # Wait 1 second of silence before processing
        )
        self.recognizer.phrase_threshold = 0.3
        self.recognizer.non_speaking_duration = 0.5

        # Current conversation context
        self.conversation_history = []

        # Parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Audio control flags
        self.is_speaking = False
        self.should_stop_audio = False
        self.audio_lock = threading.Lock()
        self.audio_process = None
        self.current_audio_file = None

        # Interrupt detection - IMPROVED
        self.interrupt_detected = False
        self.interrupt_thread = None

        # Initialize tools
        self.toolbox = ToolBox()

        # Add memory tools
        self.add_memory_tools()

        # System prompt - ENHANCED
        self.system_prompt = self.build_system_prompt()

        self.print_welcome()

    def ask_user_name(self):
        """Ask for user's name on first run"""
        print("\n" + "=" * 70)
        print("👋 Hi! I'm your new AI assistant!")
        name = input("What should I call you? (or press Enter for 'friend'): ").strip()
        return name if name else "friend"

    def add_memory_tools(self):
        """Add memory-related tools to toolbox"""
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
        """Build system prompt with user context - ENHANCED"""
        user_name = self.memory.get_preference("name", "friend")
        context = self.memory.build_context_summary()

        # Get current date for context
        current_date = datetime.datetime.now().strftime("%B %d, %Y")

        base = f"""You are an intelligent voice assistant talking to {user_name}. You have memory and can remember things across conversations.

CURRENT DATE: {current_date}

CURRENT CONTEXT:
{context}

CRITICAL RULES FOR TOOL USAGE:
1. When creating files, ALWAYS use this EXACT format:
   TOOL: create_file("filename.txt", "content goes here")
   
2. NEVER include parameter names like "content=" in the tool call
   ❌ WRONG: TOOL: create_file("test.txt", content="hello")
   ✅ CORRECT: TOOL: create_file("test.txt", "hello")

3. For multi-line content, keep it on one line or use \\n:
   TOOL: create_file("note.txt", "Line 1\\nLine 2\\nLine 3")

4. Before creating/editing files, ALWAYS check what exists first:
   TOOL: list_files(".")
   Then tell user what you found, THEN create the file.

5. When searching files or web, use the appropriate tool:
   - search_files(directory, pattern) - find files by name
   - web_search(query) - search internet
   - read_file(filepath) - read existing file

6. For opening apps on Windows, use exact names:
   TOOL: open_app("notepad")
   TOOL: open_app("chrome")
   TOOL: open_app("explorer")

IMPORTANT: Be conversational and natural. Keep responses concise for voice (2-3 sentences usually).

Available tools:
{self.toolbox.get_tool_descriptions()}

TOOL USAGE EXAMPLES:

User: "Create a file called test.txt with hello world"
You: Let me check what's in the current folder first.
TOOL: list_files(".")
[After seeing results]
You: TOOL: create_file("test.txt", "hello world")
Then: "Created test.txt with your message!"

User: "What files are in my documents?"
You: TOOL: list_files("C:\\Users\\{user_name}\\Documents")
Then: [Summarize the files found]

User: "Search for recent AI news"
You: TOOL: web_search("latest AI news 2025")
Then: [Summarize search results]

User: "Remember I like pizza"
You: TOOL: remember_fact("interests", "loves pizza")
Then: "Got it, I'll remember you love pizza!"

User: "Open notepad"
You: TOOL: open_app("notepad")
Then: "Opening Notepad now!"

Remember: Address user as {user_name}, be friendly, and ALWAYS double-check your tool syntax!
"""

        personalities = {
            "friendly": "\n\nPersonality: Be warm, helpful, and conversational - like a close friend.",
            "professional": "\n\nPersonality: Be efficient, precise, and professional.",
            "witty": "\n\nPersonality: Be clever and fun, but still helpful!",
            "minimalist": "\n\nPersonality: Be brief and to-the-point.",
        }

        return base + personalities.get(self.personality, personalities["friendly"])

    def find_voice_model(self):
        """Find available voice model"""
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
        user_name = self.memory.get_preference("name", "friend")

        print("\n" + "=" * 70)
        print("🤖 INTELLIGENT VOICE ASSISTANT - COMPLETELY FIXED VERSION")
        print("=" * 70)
        print(f"👤 User: {user_name}")
        print(f"🧠 AI Model: {self.ollama_model}")
        print(f"🎭 Personality: {self.personality.title()}")
        print(
            f"🎙️ Voice: {Path(self.voice_model_path).stem if self.voice_model_path else 'Not found'}"
        )
        print(f"💾 Session: {self.session_id}")
        print(f"🛠️ Tools: {len(self.toolbox.tools)}")
        print("=" * 70)

        # Show stored context
        tasks = self.memory.get_tasks("pending")
        if tasks:
            print(f"\n📋 You have {len(tasks)} pending task(s)")

        recent = self.memory.get_recent_conversations(1)
        if recent:
            last_time = datetime.datetime.fromisoformat(recent[0]["timestamp"])
            print(f"💬 Last conversation: {last_time.strftime('%Y-%m-%d %H:%M')}")

        print("\n💡 NEW: I wait for you to finish speaking!")
        print("💡 Say 'stop' or 'wait' to interrupt me instantly!")
        print("💡 I can see and manage ALL files on your PC!")
        print("💡 I'll check what exists before creating files!\n")

    def start_interrupt_listener(self):
        """Start background interrupt detection - IMPROVED"""
        self.interrupt_detected = False
        self.interrupt_thread = threading.Thread(
            target=self._interrupt_listener_thread, daemon=True
        )
        self.interrupt_thread.start()

    def _interrupt_listener_thread(self):
        """Background thread for interrupt detection - FASTER"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)

                while self.is_speaking and not self.interrupt_detected:
                    try:
                        # Very short timeout for instant detection
                        audio = self.recognizer.listen(
                            source, timeout=0.5, phrase_time_limit=2
                        )

                        try:
                            text = self.recognizer.recognize_google(audio).lower()

                            # Check for stop/wait commands
                            if any(
                                word in text
                                for word in [
                                    "stop",
                                    "shut up",
                                    "quiet",
                                    "wait",
                                    "pause",
                                ]
                            ):
                                self.interrupt_detected = True

                                if "wait" in text or "pause" in text:
                                    self.is_paused = True
                                    print("\n⏸️ PAUSED (say 'continue' to resume)")
                                else:
                                    self.stop_requested = True
                                    print("\n🛑 STOPPED")

                                self.stop_audio()
                                break

                        except sr.UnknownValueError:
                            continue

                    except sr.WaitTimeoutError:
                        continue
                    except Exception:
                        continue

        except Exception as e:
            pass

    def stop_audio(self):
        """Stop currently playing audio - INSTANT"""
        with self.audio_lock:
            self.should_stop_audio = True

            # Kill audio playback process immediately
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

    def listen(self, timeout=10):
        """Listen to microphone - IMPROVED to wait for complete speech"""

        if self.wake_word_mode:
            print(f"\n💤 Say '{self.wake_word}' to activate...")
        else:
            print("\n🎤 Listening... (speak now, I'll wait for you to finish)")

        self.is_listening = True

        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                print("🔧 Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)

                print("✅ Ready! Speak now...")

                # Listen with longer phrase time limit to get complete speech
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=20,  # Allow up to 20 seconds of continuous speech
                )

                print("🔄 Processing your speech...")
                text = self.recognizer.recognize_google(audio)

                # Wake word check
                if self.wake_word_mode:
                    if self.wake_word.lower() not in text.lower():
                        print(f"💤 Wake word not detected, ignoring...")
                        self.is_listening = False
                        return None
                    else:
                        # Remove wake word from text
                        text = text.lower().replace(self.wake_word.lower(), "").strip()
                        print(f"✅ Activated! Processing: {text}")
                        if not text:
                            return self.listen(timeout=5)

                print(f"\n✅ You said: {text}")
                self.is_listening = False
                return text

        except sr.WaitTimeoutError:
            self.is_listening = False
            if not self.wake_word_mode:
                print("⏱️ No speech detected (timeout)")
            return None
        except sr.UnknownValueError:
            self.is_listening = False
            if not self.wake_word_mode:
                print("❌ Couldn't understand what you said")
            return None
        except Exception as e:
            self.is_listening = False
            print(f"❌ Error: {e}")
            return None

    def process_with_ai(self, user_message):
        """Process message with AI and memory - ENHANCED"""
        print(f"\n🧠 Thinking...")

        # Reset stop flag for new query
        if self.stop_requested:
            self.stop_requested = False

        try:
            # Build messages with system prompt and context
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add recent conversation history (last 4 exchanges)
            messages.extend(self.conversation_history[-8:])

            # Add current message
            messages.append({"role": "user", "content": user_message})

            # Call Ollama with increased timeout
            print("🤖 Asking AI...")
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=300,
            )

            if response.status_code != 200:
                return "Sorry, I'm having trouble thinking right now."

            result = response.json()
            ai_response = result["message"]["content"]

            print(f"💭 AI Response: {ai_response[:100]}...")

            # Check for tool usage - ENHANCED PARSING
            tools_used = []
            if "TOOL:" in ai_response:
                print("🔧 AI wants to use tools...")
                ai_response, tools_used = self.execute_tools_from_response(ai_response)

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )

            # Save to persistent memory
            self.memory.save_conversation(
                user_message, ai_response, tools_used, self.session_id
            )

            # Keep in-memory history manageable
            if len(self.conversation_history) > 16:
                self.conversation_history = self.conversation_history[-16:]

            return ai_response

        except requests.exceptions.ConnectionError:
            return "I can't connect to my brain. Is Ollama running? Start it with 'ollama serve'"
        except requests.exceptions.Timeout:
            return "Sorry, I'm thinking too slowly. Try asking something simpler."
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()
            return "Sorry, something went wrong in my brain."

    def execute_tools_from_response(self, ai_response):
        """Execute tool calls from AI response - COMPLETELY FIXED PARSING"""
        tools_used = []

        try:
            # Find all TOOL: calls - IMPROVED REGEX
            tool_pattern = r"TOOL:\s*(\w+)\((.*?)\)(?=\s|$|TOOL:)"
            matches = re.findall(tool_pattern, ai_response, re.DOTALL)

            print(f"🔍 Found {len(matches)} tool call(s)")

            results = []

            for tool_name, params_str in matches:
                print(f"\n🔧 Parsing tool: {tool_name}")
                print(f"📝 Raw params: {params_str[:100]}...")

                # IMPROVED PARAMETER PARSING
                params = []
                if params_str.strip():
                    current_param = ""
                    in_quotes = False
                    quote_char = None
                    paren_depth = 0

                    for i, char in enumerate(params_str):
                        # Handle quotes
                        if char in ['"', "'"] and (i == 0 or params_str[i - 1] != "\\"):
                            if not in_quotes:
                                in_quotes = True
                                quote_char = char
                            elif char == quote_char:
                                in_quotes = False
                                quote_char = None

                        # Handle parentheses
                        elif char == "(" and not in_quotes:
                            paren_depth += 1
                        elif char == ")" and not in_quotes:
                            paren_depth -= 1

                        # Handle comma separation
                        elif char == "," and not in_quotes and paren_depth == 0:
                            if current_param.strip():
                                # Clean parameter - remove quotes and whitespace
                                clean = current_param.strip()
                                # Remove outer quotes only
                                if clean.startswith('"') and clean.endswith('"'):
                                    clean = clean[1:-1]
                                elif clean.startswith("'") and clean.endswith("'"):
                                    clean = clean[1:-1]
                                # Remove any "content=" or "filepath=" prefixes
                                clean = re.sub(
                                    r"^(content|filepath|text|path|query|name)\s*=\s*",
                                    "",
                                    clean,
                                )
                                params.append(clean)
                            current_param = ""
                            continue

                        current_param += char

                    # Add last parameter
                    if current_param.strip():
                        clean = current_param.strip()
                        if clean.startswith('"') and clean.endswith('"'):
                            clean = clean[1:-1]
                        elif clean.startswith("'") and clean.endswith("'"):
                            clean = clean[1:-1]
                        clean = re.sub(
                            r"^(content|filepath|text|path|query|name)\s*=\s*",
                            "",
                            clean,
                        )
                        params.append(clean)

                print(f"✅ Parsed {len(params)} parameter(s):")
                for idx, p in enumerate(params):
                    print(f"   [{idx}]: {p[:80]}...")

                # Execute tool
                print(f"⚙️ Executing: {tool_name} with {len(params)} params")
                result = self.toolbox.execute_tool(tool_name, params)

                tools_used.append(
                    {"tool": tool_name, "params": params, "success": result["success"]}
                )

                if result["success"]:
                    results.append(f"✅ {tool_name}: {result['output'][:300]}")
                    print(f"✅ SUCCESS: {result['output'][:200]}")
                else:
                    results.append(f"❌ {tool_name}: {result['output'][:300]}")
                    print(f"❌ FAILED: {result['output']}")

            # Clean response - remove TOOL: lines
            clean_response = re.sub(
                r"TOOL:.*?(?=\n|$)", "", ai_response, flags=re.DOTALL
            ).strip()

            # Add tool results to response
            if results:
                result_summary = "\n\n" + "\n".join(results)
                return clean_response + result_summary, tools_used

            return ai_response, tools_used

        except Exception as e:
            print(f"❌ Tool execution error: {e}")
            import traceback

            traceback.print_exc()
            return ai_response, tools_used

    def speak(self, text):
        """Convert text to speech with interrupt support"""
        if not self.voice_model_path:
            print("❌ No voice model")
            return False

        # Reset stop flag
        self.should_stop_audio = False
        self.interrupt_detected = False

        # Store response for pause/resume
        self.pending_response = text

        # Generate and play in thread
        self.executor.submit(self._speak_thread, text)
        return True

    def _speak_thread(self, text):
        """TTS generation and playback thread"""
        try:
            print(f"\n💬 Assistant: {text}\n")

            with self.audio_lock:
                if self.should_stop_audio:
                    return
                self.is_speaking = True

            # Start interrupt listener
            self.start_interrupt_listener()

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"response_{timestamp}.wav"
            self.current_audio_file = output_file

            # Generate TTS
            print("🎙️ Generating speech...")
            cmd = [
                "piper",
                "--model",
                self.voice_model_path,
                "--output_file",
                str(output_file),
                "--length_scale",
                "0.90",
                "--sentence_silence",
                "0.08",
            ]

            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                encoding="utf-8",
                timeout=90,
            )

            # Check if stopped during generation
            if self.should_stop_audio:
                self.is_speaking = False
                return

            if result.returncode == 0 and output_file.exists():
                print("🔊 Playing...")
                self._play_audio_with_interrupt(str(output_file))
            else:
                print(f"❌ TTS failed: {result.stderr}")

        except Exception as e:
            print(f"❌ Speech error: {e}")
        finally:
            self.is_speaking = False
            if not self.is_paused:
                self.pending_response = ""

    def _play_audio_with_interrupt(self, audio_file):
        """Play audio with instant interrupt detection"""
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

            # Play with interrupt checking
            while data and not self.should_stop_audio and not self.interrupt_detected:
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            if not self.should_stop_audio and not self.interrupt_detected:
                print("✅ Done speaking\n")

        except Exception as e:
            print(f"❌ Playback error: {e}")

    def run(self):
        """Main conversation loop"""
        print("=" * 70 + "\n")

        # Personalized greeting
        user_name = self.memory.get_preference("name", "friend")
        greeting = f"Hey {user_name}! I'm ready to help. What can I do for you?"

        if self.wake_word_mode:
            greeting = f"Hey {user_name}! Say '{self.wake_word}' when you need me!"

        print(f"💬 Assistant: {greeting}")
        self.speak(greeting)

        try:
            while True:
                # Wait for speech to finish (unless paused)
                while self.is_speaking and not self.is_paused:
                    time.sleep(0.1)

                # Don't listen while speaking
                if self.is_speaking:
                    continue

                user_text = self.listen()

                if user_text is None:
                    continue

                # Handle continue command
                if "continue" in user_text.lower() and self.is_paused:
                    self.is_paused = False
                    if self.pending_response:
                        print("▶️ Resuming...")
                        self.speak(self.pending_response)
                    continue

                # Exit commands
                exit_words = ["exit", "quit", "goodbye", "bye"]
                if any(word == user_text.lower() for word in exit_words):
                    farewell = (
                        f"Goodbye {user_name}! I'll remember everything for next time!"
                    )
                    print(f"💬 Assistant: {farewell}")
                    self.speak(farewell)
                    time.sleep(3)
                    break

                # Process with AI
                ai_response = self.process_with_ai(user_text)

                # Speak response (unless stopped)
                if not self.stop_requested:
                    self.speak(ai_response)
                else:
                    self.stop_requested = False

                print("-" * 70 + "\n")

        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
            self.stop_audio()
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback

            traceback.print_exc()


def main():
    """Entry point"""
    import sys

    model = "mistral"
    personality = "friendly"
    user_name = None
    wake_word_mode = False

    # Parse arguments
    for i, arg in enumerate(sys.argv[1:]):
        if arg in ["--wake-word", "-w"]:
            wake_word_mode = True
        elif i == 0:
            model = arg
        elif i == 1:
            personality = arg
        elif i == 2:
            user_name = arg

    print("\n🚀 Starting Enhanced Intelligent Voice Assistant...")
    print(
        "📌 Usage: python intelligent_assistant.py [model] [personality] [name] [--wake-word]"
    )
    print("📌 Personalities: friendly, professional, witty, minimalist\n")

    assistant = IntelligentAssistant(
        ollama_model=model,
        personality=personality,
        user_name=user_name,
        wake_word_mode=wake_word_mode,
    )

    if assistant.voice_model_path is None:
        print("\n❌ ERROR: No voice model found!")
        print("📁 Place .onnx model files in 'piper_models' folder")
        return

    assistant.run()


if __name__ == "__main__":
    main()

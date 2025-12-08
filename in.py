"""
Intelligent Voice Assistant - Main File
A friend-like AI assistant that actually DOES things!

Features:
- Web search and browsing
- File operations
- System control
- Fast parallel processing
- Natural conversation with personality
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

# Import our custom tools
from tools import ToolBox


class IntelligentAssistant:
    def __init__(self, ollama_model="mistral", personality="friendly"):
        """
        Initialize the intelligent assistant
        
        Args:
            ollama_model: Ollama model name
            personality: friendly, professional, witty, minimalist
        """
        self.ollama_model = ollama_model
        self.personality = personality
        self.voice_model_path = self.find_voice_model()
        
        # Setup directories
        self.output_dir = Path("voice_output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Audio settings
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
        
        # Conversation context
        self.conversation_history = []
        self.user_name = "friend"
        
        # Parallel processing
        self.tts_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.is_speaking = False
        
        # Initialize tools
        self.toolbox = ToolBox()
        
        # System prompt based on personality
        self.system_prompt = self.get_system_prompt()
        
        print("\n" + "=" * 70)
        print("🤖 INTELLIGENT VOICE ASSISTANT")
        print("=" * 70)
        print(f"🧠 AI Model: {ollama_model}")
        print(f"🎭 Personality: {personality.title()}")
        print(f"🎙️ Voice: {Path(self.voice_model_path).stem if self.voice_model_path else 'Not found'}")
        print(f"🛠️  Available Tools: {len(self.toolbox.get_tool_descriptions())}")
        print("=" * 70)
        print("\n💡 I can help you with:")
        print("   • Web searches and information")
        print("   • File management (create, read, move, delete)")
        print("   • Opening applications")
        print("   • System commands")
        print("   • Analyzing documents")
        print("   • And much more!\n")
        
    def get_system_prompt(self):
        """Get system prompt based on personality"""
        base = """You are an intelligent voice assistant with real capabilities. You can actually perform actions, not just talk about them.

IMPORTANT RULES:
1. When user asks you to DO something, use tools immediately
2. Be conversational and natural
3. Keep responses concise for voice (2-3 sentences max usually)
4. After using a tool, briefly explain what you found or did
5. Ask clarifying questions if needed

Available tools:
{tools}

To use a tool, respond with:
TOOL: tool_name(parameter1, parameter2)

Then explain the result naturally.

Examples:
User: "Search for Python news"
You: TOOL: web_search("Python news latest")
Then: "I found some interesting Python news! The latest version 3.13 was just released with performance improvements..."

User: "What's in my Downloads?"
You: TOOL: list_files("Downloads")
Then: "You have 15 files in Downloads. The most recent ones are..."

User: "Open Chrome"
You: TOOL: open_app("chrome")
Then: "Opening Chrome for you!"
"""
        
        personalities = {
            "friendly": "\n\nPersonality: Be warm, helpful, and conversational - like a good friend who's tech-savvy.",
            "professional": "\n\nPersonality: Be efficient, precise, and professional - like an executive assistant.",
            "witty": "\n\nPersonality: Be clever, fun, and add light humor when appropriate - but still helpful!",
            "minimalist": "\n\nPersonality: Be brief and to-the-point. Minimal words, maximum efficiency."
        }
        
        tools_desc = self.toolbox.get_tool_descriptions()
        return base.format(tools=tools_desc) + personalities.get(self.personality, personalities["friendly"])
    
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
    
    def listen(self):
        """Listen to microphone and convert speech to text"""
        print("\n🎤 Listening... (speak now)")
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                print("🔄 Processing speech...")
                text = self.recognizer.recognize_google(audio)
                
                print(f"✅ You: {text}")
                return text
                
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            print("❌ Couldn't understand that")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def process_with_ai(self, user_message):
        """Send message to AI and get response with tool execution"""
        print(f"🧠 Thinking...")
        
        try:
            # Build conversation with system prompt
            messages = [{"role": "system", "content": self.system_prompt}]
            messages.extend(self.conversation_history[-6:])  # Keep last 6 messages for context
            messages.append({"role": "user", "content": user_message})
            
            # Call Ollama
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": messages,
                    "stream": False,
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return "Sorry, I'm having trouble thinking right now."
            
            result = response.json()
            ai_response = result["message"]["content"]
            
            # Check if AI wants to use a tool
            if "TOOL:" in ai_response:
                ai_response = self.execute_tool_from_response(ai_response)
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return ai_response
            
        except requests.exceptions.ConnectionError:
            return "I can't connect to my brain right now. Is Ollama running?"
        except Exception as e:
            print(f"❌ Error: {e}")
            return "Sorry, something went wrong with my thinking."
    
    def execute_tool_from_response(self, ai_response):
        """Extract and execute tool calls from AI response"""
        try:
            # Extract tool call using regex
            tool_match = re.search(r'TOOL:\s*(\w+)\((.*?)\)', ai_response)
            
            if tool_match:
                tool_name = tool_match.group(1)
                params_str = tool_match.group(2)
                
                # Parse parameters (simple parsing)
                params = [p.strip().strip('"').strip("'") for p in params_str.split(",") if p.strip()]
                
                print(f"🔧 Using tool: {tool_name}({', '.join(params)})")
                
                # Execute the tool
                result = self.toolbox.execute_tool(tool_name, params)
                
                # Remove TOOL: line from response and add result
                clean_response = re.sub(r'TOOL:.*?\n', '', ai_response).strip()
                
                if result["success"]:
                    # Add result context to response
                    return f"{clean_response}\n\nResult: {result['output']}"
                else:
                    return f"I tried to {tool_name}, but got an error: {result['output']}"
            
            return ai_response
            
        except Exception as e:
            print(f"❌ Tool execution error: {e}")
            return ai_response
    
    def speak(self, text):
        """Convert text to speech using Piper TTS"""
        if not self.voice_model_path:
            print("❌ No voice model available")
            return False
        
        # Start TTS in background thread for faster response
        self.executor.submit(self._speak_thread, text)
        return True
    
    def _speak_thread(self, text):
        """TTS generation thread"""
        try:
            print(f"💬 Assistant: {text}\n")
            print("🎙️ Speaking...")
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"response_{timestamp}.wav"
            
            # Generate speech with Piper
            cmd = [
                "piper",
                "--model", self.voice_model_path,
                "--output_file", str(output_file),
                "--length_scale", "0.95",  # Slightly faster
                "--sentence_silence", "0.1",  # Less pause
            ]
            
            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                encoding="utf-8"
            )
            
            if result.returncode == 0 and output_file.exists():
                self._play_audio(str(output_file))
            else:
                print(f"❌ TTS failed: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Speech error: {e}")
    
    def _play_audio(self, audio_file):
        """Play audio file"""
        try:
            self.is_speaking = True
            wf = wave.open(audio_file, 'rb')
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            chunk = 1024
            data = wf.readframes(chunk)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
            
            self.is_speaking = False
            print("✅ Done speaking\n")
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            self.is_speaking = False
    
    def run(self):
        """Main conversation loop"""
        print("💡 Tips:")
        print("   - Say 'exit', 'quit', or 'goodbye' to stop")
        print("   - Press Ctrl+C to force quit")
        print("   - Ask me to DO things, not just chat!\n")
        print("=" * 70 + "\n")
        
        # Greeting
        greeting = self.get_greeting()
        print(f"💬 Assistant: {greeting}")
        self.speak(greeting)
        
        try:
            while True:
                # Listen for user
                user_text = self.listen()
                
                if user_text is None:
                    continue
                
                # Check for exit
                if user_text.lower() in ["exit", "quit", "goodbye", "bye", "stop"]:
                    farewell = self.get_farewell()
                    print(f"💬 Assistant: {farewell}")
                    self.speak(farewell)
                    break
                
                # Process with AI
                ai_response = self.process_with_ai(user_text)
                
                # Speak response
                self.speak(ai_response)
                
                print("-" * 70 + "\n")
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
    
    def get_greeting(self):
        """Get personality-appropriate greeting"""
        greetings = {
            "friendly": "Hey there! I'm your AI assistant. What can I help you with today?",
            "professional": "Good day. I'm ready to assist you. How may I help?",
            "witty": "Hey! Your friendly neighborhood AI here. What adventure are we embarking on today?",
            "minimalist": "Ready. What do you need?"
        }
        return greetings.get(self.personality, greetings["friendly"])
    
    def get_farewell(self):
        """Get personality-appropriate farewell"""
        farewells = {
            "friendly": "Goodbye! It was great helping you. See you next time!",
            "professional": "Goodbye. Have a productive day.",
            "witty": "Catch you later! Don't do anything I wouldn't do... which leaves you a lot of options!",
            "minimalist": "Bye."
        }
        return farewells.get(self.personality, farewells["friendly"])


def main():
    """Entry point"""
    import sys
    
    # Parse arguments
    model = "mistral"
    personality = "friendly"
    
    if len(sys.argv) > 1:
        model = sys.argv[1]
    if len(sys.argv) > 2:
        personality = sys.argv[2]
    
    print("\n🚀 Starting Intelligent Voice Assistant...")
    print(f"📝 Usage: python intelligent_assistant.py [model] [personality]")
    print(f"📝 Personalities: friendly, professional, witty, minimalist\n")
    
    # Create assistant
    assistant = IntelligentAssistant(
        ollama_model=model,
        personality=personality
    )
    
    if assistant.voice_model_path is None:
        print("\n❌ ERROR: No voice model found!")
        print("💡 Download models to piper_models/ directory")
        return
    
    # Run assistant
    assistant.run()


if __name__ == "__main__":
    main()

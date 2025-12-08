"""
Component Test Script
Tests: Ollama, Piper TTS, Microphone
Run this FIRST to verify everything works
"""

import subprocess
import os
from pathlib import Path
import requests
import json

def test_ollama():
    """Test if Ollama is running and accessible"""
    print("\n" + "="*60)
    print("🧠 Testing Ollama...")
    print("="*60)
    
    try:
        # Test connection
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json().get('models', [])
            print("✅ Ollama is running!")
            print(f"📦 Available models: {len(models)}")
            
            for model in models:
                print(f"   - {model['name']}")
            
            # Test a simple generation
            print("\n🧪 Testing generation with first model...")
            if models:
                test_model = models[0]['name']
                test_response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": test_model,
                        "prompt": "Say hello in one sentence.",
                        "stream": False
                    },
                    timeout=30
                )
                
                if test_response.status_code == 200:
                    result = test_response.json()
                    print(f"✅ Test response: {result.get('response', '')[:100]}...")
                    return True
            
        else:
            print("❌ Ollama not responding properly")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("💡 Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_piper():
    """Test if Piper TTS is installed and working"""
    print("\n" + "="*60)
    print("🎙️ Testing Piper TTS...")
    print("="*60)
    
    try:
        # Check if piper command exists
        result = subprocess.run(
            ["piper", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Piper is installed!")
            
            # Check for voice models
            models_dir = Path("piper_models")
            models = list(models_dir.glob("*.onnx")) if models_dir.exists() else []
            
            if models:
                print(f"✅ Found {len(models)} voice model(s):")
                for model in models:
                    if model.with_suffix(".onnx.json").exists():
                        print(f"   ✓ {model.stem}")
                    else:
                        print(f"   ⚠ {model.stem} (missing .json file)")
                
                # Test generation
                print("\n🧪 Testing speech generation...")
                test_model = models[0]
                test_output = Path("test_output.wav")
                
                cmd = [
                    "piper",
                    "--model", str(test_model),
                    "--output_file", str(test_output)
                ]
                
                result = subprocess.run(
                    cmd,
                    input="Testing one two three.",
                    text=True,
                    capture_output=True
                )
                
                if result.returncode == 0 and test_output.exists():
                    print("✅ TTS generation works!")
                    test_output.unlink()  # Clean up
                    return True
                else:
                    print(f"❌ TTS generation failed")
                    print(f"   Return code: {result.returncode}")
                    print(f"   STDERR: {result.stderr}")
                    print(f"   STDOUT: {result.stdout}")
                    return False
            else:
                print("❌ No voice models found!")
                print("💡 Download models to: piper_models/")
                return False
        else:
            print("❌ Piper not installed")
            print("💡 Install: pip install piper-tts")
            return False
            
    except FileNotFoundError:
        print("❌ Piper command not found")
        print("💡 Install: pip install piper-tts")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_microphone():
    """Test if microphone is accessible"""
    print("\n" + "="*60)
    print("🎤 Testing Microphone...")
    print("="*60)
    
    try:
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        mic_list = sr.Microphone.list_microphone_names()
        
        print(f"✅ Found {len(mic_list)} microphone(s):")
        for i, mic_name in enumerate(mic_list):
            print(f"   {i}: {mic_name}")
        
        print("\n🧪 Testing microphone access...")
        with sr.Microphone() as source:
            print("✅ Microphone accessible!")
            print("🔧 Adjusting for ambient noise... (2 seconds)")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone ready!")
            return True
            
    except ImportError:
        print("❌ SpeechRecognition not installed")
        print("💡 Install: pip install SpeechRecognition pyaudio")
        return False
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        print("💡 Make sure a microphone is connected")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🔍 VOICE AGENT COMPONENT TEST")
    print("="*60)
    
    results = {
        "Ollama": test_ollama(),
        "Piper TTS": test_piper(),
        "Microphone": test_microphone()
    }
    
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Ready to run voice agent!")
    else:
        print("\n⚠️ Some components need attention. Fix errors above.")
    
    print("\n💡 Next step: Run voice_agent_simple.py")

if __name__ == "__main__":
    main()
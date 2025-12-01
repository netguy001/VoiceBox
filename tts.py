import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import threading
from pathlib import Path
import wave
import pyaudio
import numpy as np
from scipy import signal
from scipy.io import wavfile


class EnhancedPiperTTS:
    def __init__(self, root):
        self.root = root
        self.root.title("Piper TTS Studio Pro - Enhanced")

        self.root.geometry("1000x900")
        self.root.minsize(800, 700)
        self.root.configure(bg="#1e1e1e")

        # Audio playback variables
        self.audio_stream = None
        self.is_playing = False
        self.current_audio_file = None

        # Voice models directory
        self.models_dir = Path("piper_models")
        self.models_dir.mkdir(exist_ok=True)

        # Configure style
        self.setup_styles()
        self.setup_ui()
        self.scan_voice_models()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TCombobox",
            fieldbackground="#2d2d2d",
            background="#2d2d2d",
            foreground="#ffffff",
            arrowcolor="#ffffff",
            bordercolor="#3d3d3d",
            padding=[5, 10, 5, 10],
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#2d2d2d")],
            selectbackground=[("readonly", "#2d2d2d")],
            selectforeground=[("readonly", "#ffffff")],
        )

        style.configure(
            "TProgressbar",
            troughcolor="#2d2d2d",
            background="#7c3aed",
            thickness=10,
        )

    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True, padx=40, pady=30)

        main_frame.grid_columnconfigure(0, weight=1)

        row_index = 0

        # Title
        title = tk.Label(
            main_frame,
            text="🎙️ Piper TTS Studio Pro",
            font=("Segoe UI", 32, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
        )
        title.grid(row=row_index, column=0, sticky="w", pady=(0, 20))
        row_index += 1

        # Voice Model Section
        voice_label = tk.Label(
            main_frame,
            text="Voice Model",
            font=("Segoe UI", 11),
            bg="#1e1e1e",
            fg="#b0b0b0",
        )
        voice_label.grid(row=row_index, column=0, sticky="w", pady=(10, 5))
        row_index += 1

        voice_frame = tk.Frame(main_frame, bg="#1e1e1e")
        voice_frame.grid(row=row_index, column=0, sticky="ew")

        self.voice_var = tk.StringVar()
        self.voice_dropdown = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            font=("Segoe UI", 11),
            state="readonly",
            style="TCombobox",
        )
        self.voice_dropdown.pack(side="left", fill="x", expand=True)

        refresh_btn = tk.Button(
            voice_frame,
            text="↻",
            command=self.scan_voice_models,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 12),
            relief="flat",
            cursor="hand2",
            width=3,
            bd=0,
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
        )
        refresh_btn.pack(side="left", padx=(10, 0), ipady=6)

        download_btn = tk.Button(
            voice_frame,
            text="Get Voices",
            command=self.open_voice_downloads,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=20,
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
        )
        download_btn.pack(side="left", padx=(10, 0), ipady=8)
        row_index += 1

        # Speech Settings - FIXED
        settings_frame = tk.Frame(main_frame, bg="#1e1e1e")
        settings_frame.grid(row=row_index, column=0, sticky="ew", pady=(20, 5))

        # Speed control
        speed_container = tk.Frame(settings_frame, bg="#1e1e1e")
        speed_container.pack(side="left", padx=(0, 30))

        tk.Label(
            speed_container,
            text="Speed:",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#b0b0b0",
        ).pack(side="left", padx=(0, 10))

        self.speed_var = tk.DoubleVar(value=1.0)
        self.speed_slider = tk.Scale(
            speed_container,
            from_=0.5,
            to=2.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.speed_var,
            bg="#2d2d2d",
            fg="#ffffff",
            troughcolor="#1e1e1e",
            highlightthickness=0,
            length=150,
            command=self.update_speed_label,
        )
        self.speed_slider.pack(side="left", padx=(0, 10))

        self.speed_label = tk.Label(
            speed_container,
            text="1.0x",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            width=5,
        )
        self.speed_label.pack(side="left")

        # Pause control
        pause_container = tk.Frame(settings_frame, bg="#1e1e1e")
        pause_container.pack(side="left")

        tk.Label(
            pause_container,
            text="Pause:",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#b0b0b0",
        ).pack(side="left", padx=(0, 10))

        self.silence_var = tk.DoubleVar(value=0.2)
        self.silence_slider = tk.Scale(
            pause_container,
            from_=0.0,
            to=1.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.silence_var,
            bg="#2d2d2d",
            fg="#ffffff",
            troughcolor="#1e1e1e",
            highlightthickness=0,
            length=150,
            command=self.update_silence_label,
        )
        self.silence_slider.pack(side="left", padx=(0, 10))

        self.silence_label = tk.Label(
            pause_container,
            text="0.2s",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e",
            fg="#ffffff",
            width=5,
        )
        self.silence_label.pack(side="left")

        row_index += 1

        # AUDIO ENHANCEMENT OPTIONS - FIXED
        enhance_label = tk.Label(
            main_frame,
            text="🎛️ Audio Enhancement",
            font=("Segoe UI", 11, "bold"),
            bg="#1e1e1e",
            fg="#10b981",
        )
        enhance_label.grid(row=row_index, column=0, sticky="w", pady=(20, 10))
        row_index += 1

        enhance_frame = tk.Frame(main_frame, bg="#1e1e1e")
        enhance_frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 10))

        self.noise_reduction_var = tk.BooleanVar(value=True)
        noise_check = tk.Checkbutton(
            enhance_frame,
            text=" Noise Reduction",
            variable=self.noise_reduction_var,
            bg="#1e1e1e",
            fg="#ffffff",
            selectcolor="#2d2d2d",
            activebackground="#1e1e1e",
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        noise_check.pack(side="left", padx=(0, 20))

        self.normalize_var = tk.BooleanVar(value=True)
        normalize_check = tk.Checkbutton(
            enhance_frame,
            text=" Normalize Volume",
            variable=self.normalize_var,
            bg="#1e1e1e",
            fg="#ffffff",
            selectcolor="#2d2d2d",
            activebackground="#1e1e1e",
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        normalize_check.pack(side="left", padx=(0, 20))

        self.enhance_clarity_var = tk.BooleanVar(value=True)
        clarity_check = tk.Checkbutton(
            enhance_frame,
            text=" Enhance Clarity",
            variable=self.enhance_clarity_var,
            bg="#1e1e1e",
            fg="#ffffff",
            selectcolor="#2d2d2d",
            activebackground="#1e1e1e",
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        clarity_check.pack(side="left")

        row_index += 1

        # Text Input Section
        text_header = tk.Frame(main_frame, bg="#1e1e1e")
        text_header.grid(row=row_index, column=0, sticky="ew", pady=(15, 5))

        text_label = tk.Label(
            text_header,
            text="Text to Speak",
            font=("Segoe UI", 11),
            bg="#1e1e1e",
            fg="#b0b0b0",
        )
        text_label.pack(side="left")

        self.char_count_label = tk.Label(
            text_header,
            text="0 characters",
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#666666",
        )
        self.char_count_label.pack(side="right")
        row_index += 1

        # Text box
        text_container = tk.Frame(
            main_frame,
            bg="#2d2d2d",
            highlightthickness=1,
            highlightbackground="#3d3d3d",
        )
        text_container.grid(row=row_index, column=0, sticky="ew", pady=(0, 15))

        scrollbar = tk.Scrollbar(
            text_container,
            bg="#2d2d2d",
            troughcolor="#2d2d2d",
            activebackground="#4d4d4d",
        )
        scrollbar.pack(side="right", fill="y")

        self.text_input = tk.Text(
            text_container,
            font=("Segoe UI", 11),
            wrap="word",
            yscrollcommand=scrollbar.set,
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            padx=20,
            pady=20,
            selectbackground="#404040",
            selectforeground="#ffffff",
            height=8,
        )
        self.text_input.pack(fill="both", expand=True)
        scrollbar.config(command=self.text_input.yview)
        self.text_input.bind("<KeyRelease>", self.update_char_count)
        row_index += 1

        # Output File Section
        output_label = tk.Label(
            main_frame,
            text="Output File Path",
            font=("Segoe UI", 11),
            bg="#1e1e1e",
            fg="#b0b0b0",
        )
        output_label.grid(row=row_index, column=0, sticky="w", pady=(0, 5))
        row_index += 1

        output_frame = tk.Frame(main_frame, bg="#1e1e1e")
        output_frame.grid(row=row_index, column=0, sticky="ew", pady=(0, 15))

        self.output_entry = tk.Entry(
            output_frame,
            font=("Segoe UI", 11),
            bg="#2d2d2d",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground="#3d3d3d",
            highlightcolor="#3d3d3d",
        )
        self.output_entry.pack(
            side="left", fill="x", expand=True, ipady=10, padx=(0, 10)
        )
        self.output_entry.insert(0, str(Path.cwd() / "output_enhanced.wav"))

        browse_btn = tk.Button(
            output_frame,
            text="Browse",
            command=self.browse_output,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=20,
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
        )
        browse_btn.pack(side="left", ipady=8)
        row_index += 1

        # Action Buttons - FIXED
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.grid(row=row_index, column=0, sticky="ew", pady=(5, 10))

        self.generate_btn = tk.Button(
            button_frame,
            text="🎤 Generate Enhanced Audio",
            command=self.generate_speech,
            bg="#7c3aed",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=40,
            pady=15,
            activebackground="#6d28d9",
            activeforeground="#ffffff",
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.play_btn = tk.Button(
            button_frame,
            text="▶  Play",
            command=self.toggle_playback,
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=40,
            pady=15,
            state="disabled",
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
        )
        self.play_btn.pack(side="left", fill="x", expand=True)
        row_index += 1

        # Progress bar
        self.progress = ttk.Progressbar(
            main_frame, mode="indeterminate", style="TProgressbar"
        )

        # Status
        self.status_label = tk.Label(
            main_frame,
            text="💡 Ready to generate - Audio enhancement enabled!",
            font=("Segoe UI", 10),
            bg="#1e1e1e",
            fg="#10b981",
            anchor="w",
        )
        self.status_label.grid(row=row_index, column=0, sticky="ew", pady=(15, 0))

    def update_speed_label(self, value):
        self.speed_label.config(text=f"{float(value):.1f}x")

    def update_silence_label(self, value):
        self.silence_label.config(text=f"{float(value):.1f}s")

    def update_char_count(self, event=None):
        text = self.text_input.get("1.0", "end-1c")
        char_count = len(text)
        self.char_count_label.config(text=f"{char_count} characters")

    def scan_voice_models(self):
        """Scan for available voice models"""
        models = []

        if self.models_dir.exists():
            for file in self.models_dir.glob("*.onnx"):
                if file.with_suffix(".onnx.json").exists():
                    models.append(str(file))

        for file in Path(".").glob("*.onnx"):
            if file.with_suffix(".onnx.json").exists():
                full_path = str(file.absolute())
                if full_path not in models:
                    models.append(full_path)

        if models:
            display_names = [Path(m).stem for m in models]
            self.voice_dropdown["values"] = display_names
            self.voice_models = {Path(m).stem: m for m in models}
            self.voice_dropdown.current(0)
            self.status_label.config(
                text=f"✓ Found {len(models)} voice model(s)", fg="#10b981"
            )
        else:
            self.voice_dropdown["values"] = []
            self.voice_models = {}
            self.status_label.config(
                text="⚠ No voice models found. Click 'Get Voices' to download.",
                fg="#f59e0b",
            )

    def open_voice_downloads(self):
        """Open the voice models download page"""
        import webbrowser

        webbrowser.open(
            "https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US"
        )
        messagebox.showinfo(
            "Download Voice Models",
            f"Save voice files to:\n{self.models_dir.absolute()}\n\n"
            "🎙️ RECOMMENDED HIGH-QUALITY VOICES:\n\n"
            "• en_US-lessac-high (very natural male)\n"
            "• en_US-ryan-high (expressive male)\n"
            "• en_US-amy-high (natural female)\n"
            "• en_US-libritts-high (multi-speaker)\n\n"
            "⚠️ Download BOTH .onnx and .onnx.json files!\n"
            "Then click ↻ to refresh.",
            parent=self.root,
        )

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
            parent=self.root,
        )
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def enhance_audio(self, input_file, output_file):
        """Apply audio enhancements: noise reduction, normalization, clarity boost"""

        try:
            # Read audio file
            sample_rate, audio_data = wavfile.read(input_file)

            # Convert to float for processing
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32)
            else:
                audio_float = audio_data.astype(np.float32)

            # 1. NOISE REDUCTION (Gentle high-pass filter)
            if self.noise_reduction_var.get():
                try:
                    sos = signal.butter(2, 100, "hp", fs=sample_rate, output="sos")
                    audio_float = signal.sosfilt(sos, audio_float)
                except:
                    pass  # Skip if filter fails

            # 2. ENHANCE CLARITY (Very gentle boost)
            if self.enhance_clarity_var.get():
                try:
                    sos = signal.butter(
                        1, [2000, 6000], "bp", fs=sample_rate, output="sos"
                    )
                    clarity_boost = signal.sosfilt(sos, audio_float) * 0.15
                    audio_float = audio_float + clarity_boost
                except:
                    pass  # Skip if filter fails

            # 3. NORMALIZE VOLUME (Fixed)
            if self.normalize_var.get():
                max_val = np.abs(audio_float).max()
                if max_val > 1000:  # Only normalize if audio has actual content
                    # Calculate RMS for better normalization
                    rms = np.sqrt(np.mean(audio_float**2))
                    if rms > 0:
                        target_rms = 3000  # Target RMS value
                        audio_float = audio_float * (target_rms / rms)
                        # Prevent clipping after normalization
                        max_after = np.abs(audio_float).max()
                        if max_after > 32000:
                            audio_float = audio_float * (32000 / max_after)

            # 4. SOFT LIMITER (Prevent clipping)
            audio_float = np.clip(audio_float, -32767, 32767)

            # Convert back to int16
            enhanced_audio = audio_float.astype(np.int16)

            # Save enhanced audio
            wavfile.write(output_file, sample_rate, enhanced_audio)
            return True

        except Exception as e:
            # If enhancement fails, just copy the original file
            print(f"Enhancement failed: {e}, using original audio")
            import shutil

            shutil.copy(input_file, output_file)
            return False

    def generate_speech(self):
        text = self.text_input.get("1.0", "end-1c").strip()

        if not text:
            messagebox.showwarning(
                "Warning", "Please enter some text!", parent=self.root
            )
            return

        model_name = self.voice_var.get()
        if not model_name:
            messagebox.showwarning(
                "Warning", "Please select a voice model!", parent=self.root
            )
            return

        model_path = self.voice_models.get(model_name)
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror(
                "Error", "Selected voice model file not found!", parent=self.root
            )
            return

        output_file = self.output_entry.get()
        if not output_file:
            messagebox.showwarning(
                "Warning", "Please specify an output file!", parent=self.root
            )
            return

        if self.is_playing:
            self.stop_audio()

        thread = threading.Thread(
            target=self._generate_speech_thread, args=(text, model_path, output_file)
        )
        thread.start()

    def _generate_speech_thread(self, text, model_path, output_file):
        self.root.after(0, self._update_ui_generating)

        try:
            # Create temp file for raw TTS output
            temp_file = output_file.replace(".wav", "_temp.wav")

            # Generate speech with Piper
            cmd = [
                "piper",
                "--model",
                model_path,
                "--output_file",
                temp_file,
                "--length_scale",
                str(1.0 / self.speed_var.get()),
                "--sentence_silence",
                str(self.silence_var.get()),
            ]

            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                encoding="utf-8",
            )

            if result.returncode == 0:
                # Apply audio enhancements
                if (
                    self.noise_reduction_var.get()
                    or self.normalize_var.get()
                    or self.enhance_clarity_var.get()
                ):

                    self.root.after(
                        0,
                        lambda: self.status_label.config(
                            text="🎛️ Enhancing audio quality...", fg="#8b5cf6"
                        ),
                    )

                    self.enhance_audio(temp_file, output_file)

                    # Clean up temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                else:
                    # Just rename temp to output if no enhancements
                    os.rename(temp_file, output_file)

                self.root.after(0, lambda: self._update_ui_success(output_file))
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                self.root.after(0, lambda: self._update_ui_error(error_msg))

        except FileNotFoundError:
            self.root.after(
                0,
                lambda: self._update_ui_error(
                    "Piper not found!\n\nInstall with: pip install piper-tts"
                ),
            )
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda msg=error_message: self._update_ui_error(msg))

    def _update_ui_generating(self):
        self.generate_btn.config(state="disabled", text="Generating...")
        self.play_btn.config(
            state="disabled", bg="#2d2d2d", activebackground="#3d3d3d", text="▶  Play"
        )
        self.status_label.config(text="⏳ Generating speech...", fg="#8b5cf6")

        self.progress.grid(
            row=self.status_label.grid_info()["row"] - 1,
            column=0,
            sticky="ew",
            pady=(5, 10),
        )
        self.progress.start(10)

    def _update_ui_success(self, output_file):
        self.progress.stop()
        self.progress.grid_forget()
        self.generate_btn.config(state="normal", text="🎤 Generate Enhanced Audio")

        enhancements = []
        if self.noise_reduction_var.get():
            enhancements.append("Noise Reduction")
        if self.normalize_var.get():
            enhancements.append("Volume Normalization")
        if self.enhance_clarity_var.get():
            enhancements.append("Clarity Enhancement")

        enhancement_text = ", ".join(enhancements) if enhancements else "None"

        messagebox.showinfo(
            "Success!",
            f"🎉 Enhanced audio generated successfully!\n\n"
            f"Enhancements Applied:\n{enhancement_text}\n\n"
            f"Saved to:\n{output_file}",
            parent=self.root,
        )

        self.play_btn.config(
            state="normal",
            text="▶  Play",
            bg="#10b981",
            activebackground="#059669",
        )

        self.current_audio_file = output_file
        self.status_label.config(
            text=f"✓ Enhanced audio generated successfully!", fg="#10b981"
        )

    def _update_ui_error(self, error_msg):
        self.progress.stop()
        self.progress.grid_forget()
        self.generate_btn.config(state="normal", text="🎤 Generate Enhanced Audio")
        self.play_btn.config(state="disabled", bg="#2d2d2d", activebackground="#3d3d3d")
        self.status_label.config(text="✗ Generation failed", fg="#ef4444")
        messagebox.showerror(
            "Error", f"Failed to generate speech:\n\n{error_msg}", parent=self.root
        )

    def toggle_playback(self):
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()

    def play_audio(self):
        """Play the generated audio file"""
        if not self.current_audio_file or not os.path.exists(self.current_audio_file):
            messagebox.showwarning(
                "Warning", "No audio file to play!", parent=self.root
            )
            return

        thread = threading.Thread(target=self._play_audio_thread)
        thread.start()

    def _play_audio_thread(self):
        try:
            self.root.after(
                0,
                lambda: self.play_btn.config(
                    text="⏸  Stop", bg="#ef4444", activebackground="#dc2626"
                ),
            )
            self.root.after(
                0,
                lambda: self.status_label.config(
                    text="▶ Playing enhanced audio...", fg="#8b5cf6"
                ),
            )
            self.is_playing = True

            wf = wave.open(self.current_audio_file, "rb")
            p = pyaudio.PyAudio()

            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            chunk = 1024
            data = wf.readframes(chunk)

            while data and self.is_playing:
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()

            if self.is_playing:
                self.is_playing = False
                self.root.after(0, self._update_ui_playback_stopped_finished)

        except Exception as e:
            self.is_playing = False
            self.root.after(0, self._update_ui_playback_stopped_finished)
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Playback Error", f"Could not play audio:\n{e}", parent=self.root
                ),
            )

    def _update_ui_playback_stopped_finished(self):
        self.is_playing = False

        if self.current_audio_file and os.path.exists(self.current_audio_file):
            bg_color = "#10b981"
            active_bg_color = "#059669"
            status_text = "✓ Playback finished"
            status_fg = "#10b981"
            self.play_btn.config(state="normal")
        else:
            bg_color = "#2d2d2d"
            active_bg_color = "#3d3d3d"
            status_text = "Playback stopped"
            status_fg = "#666666"
            self.play_btn.config(state="disabled")

        self.play_btn.config(
            text="▶  Play", bg=bg_color, activebackground=active_bg_color
        )
        self.status_label.config(text=status_text, fg=status_fg)

    def stop_audio(self):
        self.is_playing = False
        self.root.after(0, self._update_ui_playback_stopped_finished)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnhancedPiperTTS(root)
    root.mainloop()

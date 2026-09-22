import json
import os
import re
import threading
from tkinter import filedialog, messagebox
import customtkinter as ctk

from core.ffmpeg_renderer import render_video_ffmpeg
from core.script_cloner import clone_competitor_script
from core.tts_engine import generate_speech
from core.whisper_sync import extract_speech_timestamps

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class StudioFlowApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("StudioFlow AI - Multi-Platform Automation Studio")
        self.geometry("680x660")

        # Variables
        self.audio_path = ctk.StringVar()
        self.images_dir = ctk.StringVar()
        self.gemini_api_key = ctk.StringVar()

        # UI Layout
        self.lbl_header = ctk.CTkLabel(
            self,
            text="StudioFlow Automation Engine",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.lbl_header.pack(pady=10)

        # Tab Navigation
        self.tabview = ctk.CTkTabview(self, width=640, height=520)
        self.tabview.pack(padx=20, pady=5)

        self.tab_cloner = self.tabview.add("Competitor Cloner")
        self.tab_quick = self.tabview.add("Fast Local Sync")
        self.tab_tts = self.tabview.add("Free TTS Generator")

        self.setup_cloner_tab()
        self.setup_quick_sync_tab()
        self.setup_tts_tab()

        # Status Bar
        self.lbl_status = ctk.CTkLabel(
            self, text="Status: Ready", text_color="#00FF00"
        )
        self.lbl_status.pack(pady=5)

    def set_status(self, text, color="#00FF00"):
        """Thread-safe status text update."""
        self.lbl_status.configure(text=f"Status: {text}", text_color=color)

    def setup_cloner_tab(self):
        ctk.CTkLabel(
            self.tab_cloner, text="1. Gemini API Key (Free Tier):"
        ).pack(anchor="w", padx=15, pady=(10, 2))
        ctk.CTkEntry(
            self.tab_cloner,
            textvariable=self.gemini_api_key,
            width=500,
            show="*",
            placeholder_text="Enter your Gemini API key...",
        ).pack(padx=15, pady=2)

        ctk.CTkLabel(
            self.tab_cloner, text="2. Competitor Video Link / ID:"
        ).pack(anchor="w", padx=15, pady=(10, 2))
        self.entry_comp_url = ctk.CTkEntry(
            self.tab_cloner,
            width=500,
            placeholder_text="e.g. https://www.youtube.com/watch?v=...",
        )
        self.entry_comp_url.pack(padx=15, pady=2)

        ctk.CTkLabel(self.tab_cloner, text="3. Your New Topic:").pack(
            anchor="w", padx=15, pady=(10, 2)
        )
        self.entry_new_topic = ctk.CTkEntry(
            self.tab_cloner,
            width=500,
            placeholder_text="e.g. 5 Untold Secrets of Ancient Persia",
        )
        self.entry_new_topic.pack(padx=15, pady=2)

        self.btn_cloner = ctk.CTkButton(
            self.tab_cloner,
            text="Analyze & Clone Script",
            fg_color="#1F6AA5",
            font=ctk.CTkFont(weight="bold"),
            height=35,
            command=self.start_cloner_thread,
        )
        self.btn_cloner.pack(pady=12)

        ctk.CTkLabel(self.tab_cloner, text="Generated Script Output:").pack(
            anchor="w", padx=15, pady=(2, 2)
        )
        self.txt_cloned_output = ctk.CTkTextbox(
            self.tab_cloner, width=580, height=160
        )
        self.txt_cloned_output.pack(padx=15, pady=2)

    def setup_quick_sync_tab(self):
        ctk.CTkLabel(self.tab_quick, text="1. Select Voiceover File:").pack(
            anchor="w", padx=15, pady=(10, 2)
        )
        ctk.CTkEntry(
            self.tab_quick, textvariable=self.audio_path, width=420
        ).pack(side="top", padx=15)
        ctk.CTkButton(
            self.tab_quick, text="Browse Audio", command=self.browse_audio
        ).pack(padx=15, pady=5)

        ctk.CTkLabel(self.tab_quick, text="2. Select Image Folder:").pack(
            anchor="w", padx=15, pady=(10, 2)
        )
        ctk.CTkEntry(
            self.tab_quick, textvariable=self.images_dir, width=420
        ).pack(side="top", padx=15)
        ctk.CTkButton(
            self.tab_quick, text="Browse Folder", command=self.browse_folder
        ).pack(padx=15, pady=5)

        ctk.CTkLabel(self.tab_quick, text="3. Target Aspect Ratio:").pack(
            anchor="w", padx=15, pady=(10, 2)
        )
        self.combo_ratio = ctk.CTkOptionMenu(
            self.tab_quick,
            values=[
                "16:9 (YouTube Long-Form)",
                "9:16 (TikTok/Reels/Shorts)",
                "1:1 (Facebook Square)",
            ],
        )
        self.combo_ratio.pack(padx=15, pady=5)

        self.btn_render = ctk.CTkButton(
            self.tab_quick,
            text="Render Auto-Synced Video",
            fg_color="#1F6AA5",
            font=ctk.CTkFont(weight="bold"),
            height=40,
            command=self.start_quick_sync_thread,
        )
        self.btn_render.pack(pady=15)

    def setup_tts_tab(self):
        ctk.CTkLabel(self.tab_tts, text="Script Text:").pack(
            anchor="w", padx=15, pady=(10, 2)
        )
        self.txt_script = ctk.CTkTextbox(self.tab_tts, width=500, height=180)
        self.txt_script.pack(padx=15, pady=5)

        # Progress Bar Widget
        self.progress_tts = ctk.CTkProgressBar(self.tab_tts, width=500)
        self.progress_tts.pack(padx=15, pady=(10, 5))
        self.progress_tts.set(0)

        self.btn_tts = ctk.CTkButton(
            self.tab_tts,
            text="Generate Voiceover MP3",
            command=self.start_tts_thread,
        )
        self.btn_tts.pack(pady=15)

    def browse_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file_path:
            self.audio_path.set(file_path)

    def browse_folder(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.images_dir.set(dir_path)

    # --- Thread Controllers ---

    def start_quick_sync_thread(self):
        threading.Thread(
            target=self.run_quick_sync, daemon=True
        ).start()

    def start_cloner_thread(self):
        threading.Thread(
            target=self.run_script_cloner, daemon=True
        ).start()

    def start_tts_thread(self):
        threading.Thread(
            target=self.run_tts_generation, daemon=True
        ).start()

    # --- Processing Logic ---

    def run_quick_sync(self):
        audio = self.audio_path.get()
        folder = self.images_dir.get()

        if not audio or not folder:
            messagebox.showwarning(
                "Input Error", "Please select both audio and image inputs."
            )
            return

        files = os.listdir(folder)
        image_map = {}
        for fname in files:
            match = re.match(r"^(\d+)_\d+\.(jpeg|jpg|png|JPEG|JPG|PNG)$", fname)
            if match:
                image_map[int(match.group(1))] = os.path.join(folder, fname)

        sorted_keys = sorted(image_map.keys())
        image_paths = [image_map[k] for k in sorted_keys]

        if not image_paths:
            messagebox.showerror(
                "Error",
                "No matching image files found (e.g. 1_..., 2_...) in folder.",
            )
            return

        ratio_raw = self.combo_ratio.get()
        ratio = (
            "9:16"
            if "9:16" in ratio_raw
            else "1:1" if "1:1" in ratio_raw else "16:9"
        )

        try:
            self.btn_render.configure(state="disabled")
            self.set_status("Extracting timestamps with Whisper AI...", "#FFFF00")
            self.update_idletasks()

            durations = extract_speech_timestamps(audio, len(image_paths))

            self.set_status("Rendering video with FFmpeg...", "#FFFF00")
            self.update_idletasks()

            output_file = os.path.join("output", "final_synced_video.mp4")
            os.makedirs("output", exist_ok=True)

            render_video_ffmpeg(
                image_paths, durations, audio, output_file, aspect_ratio=ratio
            )

            self.set_status("Render Complete!", "#00FF00")
            messagebox.showinfo(
                "Success",
                f"Video rendering completed successfully!\nSaved to: {output_file}",
            )
        except Exception as e:
            self.set_status("Render Failed", "#FF0000")
            messagebox.showerror("Execution Error", str(e))
        finally:
            self.btn_render.configure(state="normal")
            self.update_idletasks()

    def run_script_cloner(self):
        api_key = self.gemini_api_key.get().strip()
        comp_url = self.entry_comp_url.get().strip()
        new_topic = self.entry_new_topic.get().strip()

        if not api_key or not comp_url or not new_topic:
            messagebox.showwarning(
                "Input Error",
                "Please fill in Gemini API Key, Competitor URL, and New Topic.",
            )
            return

        try:
            self.btn_cloner.configure(state="disabled")
            self.set_status("Cloning competitor script via Gemini...", "#FFFF00")

            result = clone_competitor_script(comp_url, new_topic, api_key)

            self.txt_cloned_output.delete("1.0", "end")
            self.txt_cloned_output.insert(
                "1.0", json.dumps(result, indent=2)
            )
            self.set_status("Script Cloned Successfully!", "#00FF00")
            messagebox.showinfo(
                "Success", "Competitor script cloned successfully!"
            )
        except Exception as e:
            self.set_status("Cloning Failed", "#FF0000")
            messagebox.showerror("Execution Error", str(e))
        finally:
            self.btn_cloner.configure(state="normal")

    def update_tts_progress(self, value):
        """Thread-safe UI update for TTS progress bar."""
        self.progress_tts.set(value)
        self.update_idletasks()

    def run_tts_generation(self):
        text = self.txt_script.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter script text.")
            return

        try:
            self.btn_tts.configure(state="disabled")
            self.progress_tts.set(0)
            self.set_status("Generating neural voiceover...", "#FFFF00")

            os.makedirs("output", exist_ok=True)
            out_path = os.path.join("output", "generated_voiceover.mp3")

            generate_speech(
                text, out_path, progress_callback=self.update_tts_progress
            )

            self.progress_tts.set(1.0)
            self.set_status("Voiceover Ready!", "#00FF00")
            messagebox.showinfo(
                "Success",
                f"Voiceover generated successfully!\nSaved to: {out_path}",
            )
        except Exception as e:
            self.set_status("TTS Failed", "#FF0000")
            messagebox.showerror("Execution Error", str(e))
        finally:
            self.btn_tts.configure(state="normal")


if __name__ == "__main__":
    app = StudioFlowApp()
    app.mainloop()
import os
import json
import threading
from dotenv import load_dotenv

# Automatically load environment variables from .env file
load_dotenv()

import customtkinter as ctk
from tkinter import filedialog, messagebox

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class StudioFlowApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("StudioFlow AI - Multi-Platform Automation Studio")
        self.geometry("680x820")
        self.resizable(True, True)
        self.minsize(640, 500)

        self.is_compact = False
        self.full_height = 820

        # Header Title Area
        self.frame_header = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_header.pack(fill="x", padx=20, pady=(10, 0))

        self.lbl_title = ctk.CTkLabel(
            self.frame_header, 
            text="StudioFlow Automation Engine", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_title.pack(side="left")

        self.btn_compact = ctk.CTkButton(
            self.frame_header,
            text="🗗 Compact Display",
            width=120,
            height=28,
            fg_color="#2B2D31",
            hover_color="#3B3D41",
            command=self.toggle_compact_mode
        )
        self.btn_compact.pack(side="right")

        self.lbl_subtitle = ctk.CTkLabel(
            self, 
            text="Faceless Content & Video Assembly Studio", 
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#8A8D93"
        )
        self.lbl_subtitle.pack(anchor="w", padx=20, pady=(0, 5))

        # Main Tab Container
        self.tabview = ctk.CTkTabview(self, width=640, height=660)
        self.tabview.pack(padx=20, pady=5, fill="both", expand=True)

        self.tabview.add("Competitor Cloner")
        self.tabview.add("Fast Local Sync")
        self.tabview.add("Free TTS Generator")

        self.setup_cloner_tab()
        self.setup_fast_sync_tab()
        self.setup_tts_tab()

        # Footer Status Bar
        self.lbl_status = ctk.CTkLabel(
            self, 
            text="Status: System Ready", 
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4CAF50"
        )
        self.lbl_status.pack(side="bottom", pady=8)

    def toggle_compact_mode(self):
        if not self.is_compact:
            self.geometry("680x220")
            self.btn_compact.configure(text="🗖 Expand Display")
            self.is_compact = True
        else:
            self.geometry(f"680x{self.full_height}")
            self.btn_compact.configure(text="🗗 Compact Display")
            self.is_compact = False

    # ---------------------------------------------------------
    # TAB 1: COMPETITOR CHANNEL CLONER ENGINE (YouTube API v3)
    # ---------------------------------------------------------
    def setup_cloner_tab(self):
        tab = self.tabview.tab("Competitor Cloner")

        lbl_info = ctk.CTkLabel(tab, text="1. Enter Competitor Channel (@handle or ID):", font=ctk.CTkFont(weight="bold"))
        lbl_info.pack(anchor="w", padx=15, pady=(10, 2))

        input_frame = ctk.CTkFrame(tab, fg_color="transparent")
        input_frame.pack(fill="x", padx=15, pady=2)

        self.entry_channel = ctk.CTkEntry(input_frame, width=420, placeholder_text="@MackExplains7 or @TheAncients")
        self.entry_channel.pack(side="left", padx=(0, 10))

        self.btn_scrape = ctk.CTkButton(
            input_frame, 
            text="Analyze Channel", 
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.start_channel_scraping
        )
        self.btn_scrape.pack(side="left")

        lbl_out = ctk.CTkLabel(tab, text="2. Channel Deep Extraction & Blueprint Report:", font=ctk.CTkFont(weight="bold"))
        lbl_out.pack(anchor="w", padx=15, pady=(10, 2))

        self.txt_cloner_report = ctk.CTkTextbox(tab, width=580, height=210)
        self.txt_cloner_report.pack(padx=15, pady=2, fill="x")

        lbl_ai = ctk.CTkLabel(tab, text="3. Master Prompt Strategy (Copy for ChatGPT / Claude / DeepSeek):", font=ctk.CTkFont(weight="bold"))
        lbl_ai.pack(anchor="w", padx=15, pady=(10, 2))

        self.txt_ai_prompt = ctk.CTkTextbox(tab, width=580, height=130)
        self.txt_ai_prompt.pack(padx=15, pady=2, fill="x")

        btn_copy = ctk.CTkButton(
            tab, 
            text="Copy AI Master Prompt to Clipboard", 
            fg_color="#2B2D31",
            hover_color="#3B3D41",
            command=self.copy_prompt_to_clipboard
        )
        btn_copy.pack(pady=10)

    def start_channel_scraping(self):
        channel_input = self.entry_channel.get().strip()
        if not channel_input:
            messagebox.showwarning("Warning", "Please enter a valid YouTube channel handle or ID.")
            return

        self.btn_scrape.configure(state="disabled")
        self.lbl_status.configure(text="Status: Fetching YouTube Data API metrics & transcripts...", text_color="#FF9800")

        thread = threading.Thread(target=self.process_channel_scrape, args=(channel_input,), daemon=True)
        thread.start()

    def process_channel_scrape(self, channel_input):
        try:
            from core.channel_cloner import analyze_and_clone_channel
            json_path, full_output = analyze_and_clone_channel(channel_input)
            self.after(0, lambda: self.on_scrape_success(json_path, full_output))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self.on_scrape_error(err_msg))

    def on_scrape_success(self, json_path, full_output):
        self.btn_scrape.configure(state="normal")
        self.lbl_status.configure(text="Status: Channel Blueprint Created!", text_color="#4CAF50")

        meta = full_output.get("channel_metadata", {})
        summary = full_output.get("summary_analytics", {})
        videos = full_output.get("videos", [])

        report = (
            f"=== YOUTUBE DATA API ANALYSIS REPORT ===\n"
            f"Channel Title: {meta.get('title', 'N/A')}\n"
            f"Channel ID: {meta.get('id', 'N/A')}\n"
            f"Subscribers: {meta.get('subscribers', 0):,}\n"
            f"Total Videos Analyzed: {len(videos)}\n"
            f"Upload Cadence: Avg {summary.get('upload_cadence', {}).get('avg_days_between_uploads', 'N/A')} days between posts\n"
            f"Full Analysis JSON: {json_path}\n\n"
            f"--- TOP OUTLIER VIDEOS ---\n"
        )

        outliers = [v for v in videos if v.get('is_outlier')]
        for i, vid in enumerate(outliers[:5], 1):
            views_val = vid.get('views', 0)
            velocity = vid.get('metrics', {}).get('view_velocity', 0)
            report += f"{i}. {vid.get('title')} ({views_val:,} views | {velocity:.1f} v/day)\n   URL: https://youtube.com/watch?v={vid.get('id')}\n"

        self.txt_cloner_report.delete("0.0", "end")
        self.txt_cloner_report.insert("0.0", report)

        llm_prompt = (
            f"Act as a Master YouTube Content Strategist.\n"
            f"I have exported a complete channel analysis JSON blueprint to: '{json_path}'.\n\n"
            f"Target Channel Summary:\n"
            f"- Channel Name: {meta.get('title')}\n"
            f"- Subscribers: {meta.get('subscribers'):,}\n"
            f"- Total Videos Analyzed: {len(videos)}\n"
            f"- Title Pattern Info: {summary.get('title_patterns', {})}\n\n"
            f"INSTRUCTIONS:\n"
            f"Please analyze the data in the specified JSON file. Deconstruct the hook mechanics, video format lengths, "
            f"outlier transcript styles, and thumbnail aesthetics. Create a complete Master Prompt Framework to replicate "
            f"this channel's viral success for a new channel."
        )

        self.txt_ai_prompt.delete("0.0", "end")
        self.txt_ai_prompt.insert("0.0", llm_prompt)

        messagebox.showinfo("Analysis Complete", f"Channel JSON Blueprint successfully exported to:\n{json_path}")

    def on_scrape_error(self, err_msg):
        self.btn_scrape.configure(state="normal")
        self.lbl_status.configure(text="Status: Channel Extraction Error", text_color="#F44336")
        messagebox.showerror("Extraction Error", err_msg)

    def copy_prompt_to_clipboard(self):
        prompt_text = self.txt_ai_prompt.get("0.0", "end").strip()
        if not prompt_text:
            messagebox.showwarning("Warning", "No AI prompt generated yet. Scrape a channel first.")
            return

        self.clipboard_clear()
        self.clipboard_append(prompt_text)
        messagebox.showinfo("Copied", "Master Prompt copied to clipboard! Paste it into ChatGPT, Claude, Gemini, or DeepSeek.")

    # ---------------------------------------------------------
    # TAB 2: FAST LOCAL SYNC
    # ---------------------------------------------------------
    def setup_fast_sync_tab(self):
        tab = self.tabview.tab("Fast Local Sync")

        lbl_vo = ctk.CTkLabel(tab, text="1. Select Voiceover File:", font=ctk.CTkFont(weight="bold"))
        lbl_vo.pack(anchor="w", padx=15, pady=(8, 2))

        self.entry_vo_path = ctk.CTkEntry(tab, width=580, placeholder_text="Path to .mp3 or .wav file...")
        self.entry_vo_path.pack(padx=15, pady=2, fill="x")

        btn_browse_vo = ctk.CTkButton(tab, text="Browse Audio", command=self.browse_audio)
        btn_browse_vo.pack(pady=(2, 6))

        lbl_img = ctk.CTkLabel(tab, text="2. Select Image Folder:", font=ctk.CTkFont(weight="bold"))
        lbl_img.pack(anchor="w", padx=15, pady=(4, 2))

        self.entry_img_path = ctk.CTkEntry(tab, width=580, placeholder_text="Path to folder with images...")
        self.entry_img_path.pack(padx=15, pady=2, fill="x")

        btn_browse_img = ctk.CTkButton(tab, text="Browse Folder", command=self.browse_folder)
        btn_browse_img.pack(pady=(2, 6))

        lbl_seq = ctk.CTkLabel(tab, text="3. Paste Image Sequence / Timestamps (Optional):", font=ctk.CTkFont(weight="bold"))
        lbl_seq.pack(anchor="w", padx=15, pady=(4, 2))

        self.txt_sequence = ctk.CTkTextbox(tab, width=580, height=130, activate_scrollbars=True)
        self.txt_sequence.pack(padx=15, pady=2, fill="x")
        
        placeholder = (
            "image 1. 0:00–0:05\n"
            "image 2. 0:05–0:09\n"
            "image 3. 0:09–0:19\n"
            "...\n"
            "(Leave blank to auto-sync uniformly across voiceover length)"
        )
        self.txt_sequence.insert("0.0", placeholder)

        lbl_ratio = ctk.CTkLabel(tab, text="4. Target Aspect Ratio:", font=ctk.CTkFont(weight="bold"))
        lbl_ratio.pack(anchor="w", padx=15, pady=(6, 2))

        self.combo_ratio = ctk.CTkOptionMenu(
            tab, 
            values=["16:9 (YouTube Long-Form)", "9:16 (TikTok/Reels/Shorts)", "1:1 (Square)"]
        )
        self.combo_ratio.pack(anchor="w", padx=15, pady=2)

        self.btn_render = ctk.CTkButton(
            tab, 
            text="Render Auto-Synced Video", 
            fg_color="#1f538d", 
            hover_color="#14375e",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_render_thread
        )
        self.btn_render.pack(pady=(12, 6))

    def browse_audio(self):
        file_path = filedialog.askopenfilename(
            title="Select Voiceover Audio",
            filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a")]
        )
        if file_path:
            self.entry_vo_path.delete(0, "end")
            self.entry_vo_path.insert(0, file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Image Folder")
        if folder_path:
            self.entry_img_path.delete(0, "end")
            self.entry_img_path.insert(0, folder_path)

    def start_render_thread(self):
        vo_path = self.entry_vo_path.get().strip()
        img_folder = self.entry_img_path.get().strip()
        raw_sequence = self.txt_sequence.get("0.0", "end").strip()

        if not os.path.exists(vo_path):
            messagebox.showerror("Error", "Please select a valid Voiceover Audio file.")
            return

        if not os.path.exists(img_folder):
            messagebox.showerror("Error", "Please select a valid Image Folder.")
            return

        self.btn_render.configure(state="disabled")
        self.lbl_status.configure(text="Status: Rendering video in background... Please wait.", text_color="#FF9800")

        thread = threading.Thread(target=self.process_render, args=(vo_path, img_folder, raw_sequence), daemon=True)
        thread.start()

    def process_render(self, vo_path, img_folder, raw_sequence):
        try:
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            output_file = os.path.join(downloads_folder, "final_synced_video.mp4")

            if raw_sequence and "0:00" in raw_sequence:
                from core.ffmpeg_renderer import render_from_custom_sequence
                render_from_custom_sequence(vo_path, img_folder, raw_sequence, output_file)
            else:
                from core.ffmpeg_renderer import render_auto_sync
                render_auto_sync(vo_path, img_folder, output_file)

            self.after(0, lambda: self.on_render_success(output_file))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self.on_render_error(err_msg))

    def on_render_success(self, output_file):
        self.lbl_status.configure(text="Status: Render Complete! Saved to Downloads.", text_color="#4CAF50")
        self.btn_render.configure(state="normal")
        os.system(f'explorer /select,"{output_file}"')
        messagebox.showinfo("Success", f"Video successfully saved to Downloads:\n{output_file}")

    def on_render_error(self, err_msg):
        self.lbl_status.configure(text="Status: Render Error", text_color="#F44336")
        self.btn_render.configure(state="normal")
        messagebox.showerror("Render Error", err_msg)

    # ---------------------------------------------------------
    # TAB 3: FREE TTS GENERATOR WITH VOICE DEMO PLAYER
    # ---------------------------------------------------------
    def setup_tts_tab(self):
        tab = self.tabview.tab("Free TTS Generator")

        lbl_script = ctk.CTkLabel(tab, text="1. Enter Voiceover Script:", font=ctk.CTkFont(weight="bold"))
        lbl_script.pack(anchor="w", padx=15, pady=(10, 2))

        self.txt_tts_script = ctk.CTkTextbox(tab, width=580, height=170)
        self.txt_tts_script.pack(padx=15, pady=2, fill="x")

        lbl_voice = ctk.CTkLabel(tab, text="2. Select AI Voice Profile & Preview:", font=ctk.CTkFont(weight="bold"))
        lbl_voice.pack(anchor="w", padx=15, pady=(8, 2))

        voice_frame = ctk.CTkFrame(tab, fg_color="transparent")
        voice_frame.pack(anchor="w", padx=15, pady=2, fill="x")

        self.combo_voice = ctk.CTkOptionMenu(
            voice_frame, 
            width=360,
            values=[
                "Adam - Energetic Male (US)",
                "Bella - Natural Female (US)",
                "Charlie - Deep Cinematic Male (UK)",
                "Sonia - Professional Female (UK)",
                "Liam - Storyteller Male (AU)",
                "Prabhat - Narrative Male (IN)"
            ]
        )
        self.combo_voice.pack(side="left", padx=(0, 10))

        btn_demo = ctk.CTkButton(
            voice_frame,
            text="▶ Play Demo",
            width=110,
            fg_color="#2B2D31",
            hover_color="#3B3D41",
            command=self.play_demo_audio
        )
        btn_demo.pack(side="left")

        self.progress_tts = ctk.CTkProgressBar(tab, width=580, mode="indeterminate")
        self.progress_tts.pack(padx=15, pady=(15, 5), fill="x")
        self.progress_tts.set(0)

        self.btn_generate_tts = ctk.CTkButton(
            tab, 
            text="Generate Full AI Voiceover (.mp3)", 
            fg_color="#1f538d",
            hover_color="#14375e",
            font=ctk.CTkFont(weight="bold"),
            command=self.start_tts_thread
        )
        self.btn_generate_tts.pack(pady=10)

    def play_demo_audio(self):
        voice_choice = self.combo_voice.get()
        self.lbl_status.configure(text=f"Status: Playing demo for {voice_choice}...", text_color="#2196F3")
        
        def _thread_demo():
            from core.tts_engine import play_voice_demo
            play_voice_demo(voice_choice)
            self.after(0, lambda: self.lbl_status.configure(text="Status: System Ready", text_color="#4CAF50"))

        threading.Thread(target=_thread_demo, daemon=True).start()

    def start_tts_thread(self):
        text = self.txt_tts_script.get("0.0", "end").strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to generate speech.")
            return

        self.btn_generate_tts.configure(state="disabled")
        self.progress_tts.start()
        self.lbl_status.configure(text="Status: Generating AI Voiceover in background...", text_color="#FF9800")

        thread = threading.Thread(target=self.process_tts, args=(text,), daemon=True)
        thread.start()

    def process_tts(self, text):
        try:
            from core.tts_engine import generate_voiceover

            voice_choice = self.combo_voice.get()
            output_path = os.path.abspath(os.path.join("output", "generated_voiceover.mp3"))

            generate_voiceover(text, voice_choice, output_path)

            self.after(0, lambda: self.on_tts_success(output_path))
        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: self.on_tts_error(err_msg))

    def on_tts_success(self, output_path):
        self.progress_tts.stop()
        self.progress_tts.set(1)
        self.lbl_status.configure(text="Status: Voiceover Generated!", text_color="#4CAF50")
        self.btn_generate_tts.configure(state="normal")

        self.entry_vo_path.delete(0, "end")
        self.entry_vo_path.insert(0, output_path)

        messagebox.showinfo(
            "TTS Complete", 
            f"Voiceover successfully generated!\nSaved to: {output_path}\n\nPath automatically set in 'Fast Local Sync' tab."
        )

    def on_tts_error(self, err_msg):
        self.progress_tts.stop()
        self.progress_tts.set(0)
        self.lbl_status.configure(text="Status: TTS Generation Error", text_color="#F44336")
        self.btn_generate_tts.configure(state="normal")
        messagebox.showerror("TTS Error", err_msg)

if __name__ == "__main__":
    app = StudioFlowApp()
    app.mainloop()
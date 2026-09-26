# StudioFlow AI 🎬
> Multi-Platform Video Automation & Competitor Intelligence Engine

StudioFlow is a Python-powered desktop automation engine built for faceless content creators, video strategists, and multi-platform automation channels. It combines YouTube Data API v3 competitor analysis, Edge TTS generation with native previewing, and automated FFmpeg video assembly into a unified CustomTkinter desktop interface.

---

## ⚡ Core Features

* **Competitor Cloner (YouTube Data API v3)**: Resolves handles, computes video view velocities, flags viral outliers (>1.5x median velocity), fetches first-90s transcript clips, collects top comments, and exports comprehensive strategic JSON blueprints (`_full_analysis.json`).
* **Fast Local Sync Engine**: Automatically matches voiceover audio tracks with image folders, generating synced video deliverables across standard aspect ratios (`16:9`, `9:16`, `1:1`).
* **Free AI TTS Generator**: Converts text scripts into natural AI voiceovers via `edge-tts` with built-in voice previewing.
* **Modern CustomTkinter Interface**: Dark-themed UI featuring a responsive "Compact Display" mode, asynchronous background thread processing, and real-time status reporting.

---

## 🚀 Setup & Installation

### 1. Prerequisites
* Python 3.10+
* FFmpeg installed and added to system PATH

### 2. Clone Repository & Install Dependencies
```bash
git clone [https://github.com/arbaazmeo/StudioFlow.git](https://github.com/arbaazmeo/StudioFlow.git)
cd StudioFlow
pip install -r requirements.txt
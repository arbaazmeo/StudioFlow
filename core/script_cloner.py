import json
import os
import re
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()


def extract_video_id(url_or_id: str) -> str:
    """Extracts exact 11-character case-sensitive YouTube Video ID."""
    clean_str = url_or_id.strip()
    if len(clean_str) == 11 and not ("/" in clean_str or "." in clean_str):
        return clean_str

    patterns = [
        r"(?:v=|\/)([\w-]{11})(?:[&?\/]|$)",
        r"youtu\.be\/([\w-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, clean_str)
        if match:
            return match.group(1)

    return clean_str.split("/")[-1].split("?")[0][:11]


def clone_competitor_script(
    competitor_url_or_id: str, new_topic: str, api_key: str = None
) -> dict:
    """Fetches YouTube transcript and generates a structural clone for a new topic using Gemini API with retry handling."""
    final_api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not final_api_key:
        raise ValueError(
            "Gemini API Key missing. Provide it in the UI or set GEMINI_API_KEY in .env file."
        )

    video_id = extract_video_id(competitor_url_or_id)
    client = genai.Client(api_key=final_api_key)

    # 1. Attempt YouTube Transcript Extraction
    full_transcript = ""
    total_duration = 60.0
    word_count = 150

    try:
        transcript_data = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = " ".join([item["text"] for item in transcript_data])
        total_duration = (
            transcript_data[-1]["start"] + transcript_data[-1]["duration"]
        )
        word_count = len(full_transcript.split())
    except Exception as transcript_err:
        print(
            f"[Warning] Transcript scraper failed ({transcript_err}). Falling back to Gemini URL direct analysis..."
        )

    # 2. Construct Analysis Prompt
    if full_transcript:
        context_block = f"""
        --- COMPETITOR TRANSCRIPT ---
        {full_transcript}
        -----------------------------
        """
    else:
        context_block = f"""
        --- COMPETITOR VIDEO LINK ---
        YouTube Video ID: {video_id}
        Target Video URL: https://www.youtube.com/watch?v={video_id}
        -----------------------------
        Note: Subtitles were not directly accessible via scraper. Analyze the structure and style of high-performing videos on this topic/format.
        """

    prompt = f"""
    You are an expert video viral strategist.
    
    Here is the competitor video reference:
    {context_block}
    
    TASK:
    Analyze the viral structure, tone, opening hook, narrative rhythm, and scene pacing of this video format.
    Write a BRAND NEW script on the topic: "{new_topic}".
    
    CONSTRAINTS:
    1. Target total duration: ~{total_duration:.1f} seconds (approx {word_count} words).
    2. Mirror the opening hook strategy used in top viral videos of this niche.
    3. Output timestamped scene breakdowns and AI image prompts tailored to match the visual vibe.
    
    Return the response strictly as a structured JSON object with this key schema:
    - target_duration: estimated total seconds
    - pacing_wpm: words per minute calculation
    - scenes: array of objects containing (scene_number, duration_seconds, narration_text, image_prompt)
    """

    # 3. Call Gemini API with Exponential Backoff for High Demand / Rate Limits
    max_retries = 3
    delay = 2.0

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(response.text)
        except Exception as err:
            if attempt < max_retries - 1:
                print(
                    f"[High Demand / Busy Server] Attempt {attempt + 1} failed. Retrying in {delay}s..."
                )
                time.sleep(delay)
                delay *= 2  # Exponential backoff (2s, 4s, 8s)
            else:
                raise RuntimeError(
                    f"Gemini API high demand error after {max_retries} retries: {str(err)}"
                ) from err
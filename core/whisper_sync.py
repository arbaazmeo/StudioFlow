import sys
import whisper


def extract_speech_timestamps(audio_path: str, total_images: int):
    """Uses local Whisper AI to detect speech timing segments for auto-syncing images."""
    print("\n[Whisper] Loading model 'base' into memory (this takes a moment on first run)...")
    sys.stdout.flush()
    
    model = whisper.load_model("base")

    print("[Whisper] Analyzing audio timestamps...")
    sys.stdout.flush()

    # Disabling fp16 eliminates CPU warnings and ensures stable execution
    result = model.transcribe(
        audio_path, word_timestamps=True, fp16=False
    )

    cut_points = [segment["end"] for segment in result.get("segments", [])]

    if not cut_points:
        print("[Whisper] Warning: No cut points detected, using uniform spacing.")
        return [3.0] * total_images

    durations = []
    prev_time = 0.0

    for i in range(total_images - 1):
        if i < len(cut_points):
            dur = cut_points[i] - prev_time
            prev_time = cut_points[i]
        else:
            dur = 3.0
        durations.append(max(0.8, dur))

    durations.append(max(1.0, cut_points[-1] - prev_time if cut_points else 3.0))

    print(f"[Whisper] Successfully mapped {len(durations)} visual scene segments.")
    sys.stdout.flush()
    return durations
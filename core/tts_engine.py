import asyncio
import edge_tts


async def generate_speech_async(
    text: str,
    output_path: str,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "+0%",
    progress_callback=None,
):
    """Generates MP3 audio file from input text with real-time chunk progress reporting."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)

    # Estimate rough total chunks based on character length for progress tracking
    total_estimated = max(1, len(text) // 20)
    current_chunk = 0

    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                current_chunk += 1
                if progress_callback:
                    # Calculate progress percentage (clamped between 0.0 and 0.95 until completed)
                    pct = min(0.95, current_chunk / total_estimated)
                    progress_callback(pct)

    if progress_callback:
        progress_callback(1.0)


def generate_speech(
    text: str,
    output_path: str,
    voice: str = "en-US-ChristopherNeural",
    rate: str = "+0%",
    progress_callback=None,
):
    """Synchronous wrapper for Edge TTS generation with progress support."""
    asyncio.run(
        generate_speech_async(
            text, output_path, voice, rate, progress_callback
        )
    )
    return output_path
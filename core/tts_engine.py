import os
import asyncio
import edge_tts

VOICE_MAPPING = {
    "Adam - Energetic Male (US)": "en-US-GuyNeural",
    "Bella - Natural Female (US)": "en-US-JennyNeural",
    "Charlie - Deep Cinematic Male (UK)": "en-GB-RyanNeural",
    "Sonia - Professional Female (UK)": "en-GB-SoniaNeural",
    "Liam - Storyteller Male (AU)": "en-AU-WilliamNeural",
    "Prabhat - Narrative Male (IN)": "en-IN-PrabhatNeural"
}

DEMO_CACHE_DIR = os.path.join("output", "voice_demos")

def generate_voiceover(text, voice_choice, output_path):
    voice = VOICE_MAPPING.get(voice_choice, "en-US-GuyNeural")
    
    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    asyncio.run(_generate())
    return output_path

def play_voice_demo(voice_choice):
    voice = VOICE_MAPPING.get(voice_choice, "en-US-GuyNeural")
    os.makedirs(DEMO_CACHE_DIR, exist_ok=True)
    
    demo_file = os.path.abspath(os.path.join(DEMO_CACHE_DIR, f"{voice}_demo.mp3"))
    demo_text = "Hello! This is a preview of my voice for your video project."

    # Generate sample if not already cached
    if not os.path.exists(demo_file):
        async def _gen_demo():
            comm = edge_tts.Communicate(demo_text, voice)
            await comm.save(demo_file)
        
        asyncio.run(_gen_demo())

    # Native Windows MP3 Audio Playback via PowerShell COM Player
    ps_command = f'$player = New-Object -ComObject WMPlayer.OCX; $player.URL = "{demo_file}"; $player.controls.play(); Start-Sleep -s 3'
    os.system(f'powershell -c "{ps_command}"')
import os
import re
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.concatenate import concatenate_videoclips

def parse_custom_sequence(raw_sequence_text):
    parsed = []
    # Flexible regex matching standard hyphens, en-dashes, em-dashes, and varying whitespace
    pattern = re.compile(
        r"(?:image\s*)?(\d+)[\.\:]?\s*(\d+):(\d+)\s*[\-\–\—\to]+\s*(\d+):(\d+)", 
        re.IGNORECASE
    )
    
    for line in raw_sequence_text.splitlines():
        # Skip guide placeholder text
        if "leave blank" in line.lower() or "..." in line or not line.strip():
            continue
            
        matches = pattern.findall(line)
        for match in matches:
            img_num = int(match[0])
            start_sec = int(match[1]) * 60 + int(match[2])
            end_sec = int(match[3]) * 60 + int(match[4])
            duration = end_sec - start_sec
            
            if duration > 0:
                parsed.append((img_num, start_sec, duration))
            
    return parsed

def render_from_custom_sequence(audio_path, image_folder, raw_sequence_text, output_file):
    mapping = parse_custom_sequence(raw_sequence_text)
    if not mapping:
        raise ValueError("Could not parse sequence timestamps. Check format.")

    # 1. Fetch and numerically sort ALL image files in folder
    valid_exts = (".png", ".jpg", ".jpeg", ".webp")
    all_files = [f for f in os.listdir(image_folder) if f.lower().endswith(valid_exts)]
    
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]
    
    all_files.sort(key=natural_sort_key)

    if not all_files:
        raise FileNotFoundError(f"No image files found inside {image_folder}")

    # Load audio track
    audio_clip = AudioFileClip(audio_path)
    video_clips = []

    # 2. Match timestamp entry to sorted images
    for idx, (img_num, start_sec, duration) in enumerate(mapping):
        found_path = None

        if idx < len(all_files):
            found_path = os.path.join(image_folder, all_files[idx])
        else:
            possible_names = [
                f"image_{img_num}.png", f"image_{img_num}.jpg",
                f"image {img_num}.png", f"image {img_num}.jpg",
                f"{img_num}.png", f"{img_num}.jpg"
            ]
            for name in possible_names:
                full_path = os.path.join(image_folder, name)
                if os.path.exists(full_path):
                    found_path = full_path
                    break

        if found_path and os.path.exists(found_path):
            clip = ImageClip(found_path).set_duration(duration)
            video_clips.append(clip)

    if not video_clips:
        raise FileNotFoundError("No matching images could be loaded from the selected folder.")

    print(f"Assembling {len(video_clips)} image clips with audio track...")
    
    # Build visual sequence and force audio attachment
    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.audio = audio_clip
    
    if final_video.duration > audio_clip.duration:
        final_video = final_video.subclip(0, audio_clip.duration)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Export with strict audio parameters
    final_video.write_videofile(
        output_file,
        fps=24,
        codec="libx264",
        audio=True,
        audio_codec="aac",
        audio_bitrate="192k",
        audio_fps=44100,
        temp_audiofile="temp_audio.m4a",
        remove_temp=True
    )
    
    audio_clip.close()
    final_video.close()

def render_auto_sync(audio_path, image_folder, output_file):
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration
    
    valid_exts = (".png", ".jpg", ".jpeg", ".webp")
    image_files = sorted([
        os.path.join(image_folder, f) for f in os.listdir(image_folder)
        if f.lower().endswith(valid_exts)
    ])

    if not image_files:
        raise FileNotFoundError("No valid image files found in folder.")

    per_image_duration = total_duration / len(image_files)
    video_clips = [ImageClip(img).set_duration(per_image_duration) for img in image_files]

    final_video = concatenate_videoclips(video_clips, method="compose")
    final_video.audio = audio_clip
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    final_video.write_videofile(
        output_file, 
        fps=24, 
        codec="libx264", 
        audio=True, 
        audio_codec="aac",
        audio_bitrate="192k",
        audio_fps=44100,
        temp_audiofile="temp_audio.m4a",
        remove_temp=True
    )
    
    audio_clip.close()
    final_video.close()
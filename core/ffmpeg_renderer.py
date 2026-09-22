import os
import shutil
import subprocess


def get_ffmpeg_cmd():
    """Finds the ffmpeg executable on the system."""
    # Check if ffmpeg is in system PATH
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin

    # Common winget / manual installation paths on Windows
    possible_paths = [
        os.path.expanduser(
            r"~\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.0.2-full_build\bin\ffmpeg.exe"
        ),
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    # If still not found, return 'ffmpeg' and let subprocessing raise clear error
    return "ffmpeg"


def render_video_ffmpeg(
    image_paths: list,
    durations: list,
    audio_path: str,
    output_path: str,
    aspect_ratio: str = "16:9",
):
    """Stitches images and audio into an MP4 video using fast local FFmpeg rendering."""
    concat_file = "concat_manifest.txt"
    ffmpeg_bin = get_ffmpeg_cmd()

    # Write FFmpeg concatenation file
    with open(concat_file, "w", encoding="utf-8") as f:
        for idx, img in enumerate(image_paths):
            clean_path = os.path.abspath(img).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")
            f.write(f"duration {durations[idx]:.3f}\n")
        # Duplicate last frame for FFmpeg specification
        clean_last = os.path.abspath(image_paths[-1]).replace("\\", "/")
        f.write(f"file '{clean_last}'\n")

    # Set crop and aspect filters
    if aspect_ratio == "9:16":
        video_filter = (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
        )
    elif aspect_ratio == "1:1":
        video_filter = (
            "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080"
        )
    else:  # Default 16:9
        video_filter = (
            "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
        )

    ffmpeg_command = [
        ffmpeg_bin,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_file,
        "-i",
        audio_path,
        "-vf",
        video_filter,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-shortest",
        output_path,
    ]

    subprocess.run(ffmpeg_command, check=True)

    if os.path.exists(concat_file):
        os.remove(concat_file)

    return output_path
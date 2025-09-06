# app/workers/video_utils.py

import os
import subprocess
import shutil

def downscale_video(input_path: str, output_path: str, max_size_mb: int = 16) -> str:
    """
    Downscale/compress a video to fit within WhatsApp's 16MB limit using ffmpeg.
    Returns the path to the output file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    # If already under limit, just copy
    size_mb = os.path.getsize(input_path) / (1024 * 1024)
    if size_mb <= max_size_mb:
        shutil.copy(input_path, output_path)
        return output_path

    # Run ffmpeg to compress
    cmd = [
        "ffmpeg",
        "-y",  # overwrite
        "-i", input_path,
        "-vf", "scale=-2:480",  # scale height to 480px, keep aspect
        "-b:v", "800k",
        "-bufsize", "800k",
        "-maxrate", "800k",
        "-c:a", "aac",
        "-b:a", "96k",
        output_path,
    ]
    subprocess.run(cmd, check=True)

    return output_path

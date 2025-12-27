"""
download.py
──────────────────────────────────────────────
Module for downloading YouTube video metadata and subtitles.

This module handles:
- Video info extraction (title, ID)
- Subtitle downloading (English auto-generated)
"""

import os
import yt_dlp


def extract_video_info(video_url: str) -> dict:
    """
    Extract video metadata from YouTube URL.

    Args:
        video_url: YouTube video URL

    Returns:
        dict: Video metadata (id, title)

    Raises:
        Exception: If video info extraction fails
    """
    print(f"🔍 Extracting video info...")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_id = info.get('id')
            video_title = info.get('title', 'unknown_title')

            print(f"   Video ID: {video_id}")
            print(f"   Title: {video_title}")

            return {
                'id': video_id,
                'title': video_title,
                'url': video_url
            }
    except Exception as e:
        raise Exception(f"Failed to extract video info: {e}")


def download_subtitles(video_url: str, video_id: str, output_dir: str) -> str:
    """
    Download English subtitles for a video.

    Args:
        video_url: YouTube video URL
        video_id: Video ID
        output_dir: Directory to save subtitles

    Returns:
        str: Path to downloaded VTT file

    Raises:
        Exception: If subtitle download fails or no subtitles available
    """
    print(f"📥 Downloading subtitles...")

    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en'],
        'skip_download': True,
        'outtmpl': f"{output_dir}/{video_id}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
        # Add extractor args to handle PO token requirement
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        vtt_path = os.path.join(output_dir, f"{video_id}.en.vtt")

        if not os.path.exists(vtt_path):
            raise Exception("No subtitles available for this video")

        print(f"   ✅ Subtitles downloaded")
        return vtt_path

    except Exception as e:
        raise Exception(f"Failed to download subtitles: {e}")

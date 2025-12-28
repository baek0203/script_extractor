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
    Download subtitles for a video (any available language).

    Priority: English > Korean > Any available language

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

    # Try downloading with error handling
    import glob

    ydl_opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'ko'],  # Prefer English, then Korean
        'skip_download': True,
        'outtmpl': f"{output_dir}/{video_id}.%(ext)s",
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,  # Continue on download errors
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

        # Try to find downloaded subtitle file
        # Priority: en > ko > any other language
        possible_paths = [
            os.path.join(output_dir, f"{video_id}.en.vtt"),
            os.path.join(output_dir, f"{video_id}.ko.vtt"),
        ]

        # Check if any of the preferred subtitles exist
        for vtt_path in possible_paths:
            if os.path.exists(vtt_path):
                lang = "English" if ".en." in vtt_path else "Korean"
                print(f"   ✅ Subtitles downloaded ({lang})")
                return vtt_path

        # If no preferred language, find any .vtt file
        vtt_files = glob.glob(os.path.join(output_dir, f"{video_id}.*.vtt"))
        if vtt_files:
            print(f"   ✅ Subtitles downloaded")
            return vtt_files[0]

        raise Exception("No subtitles available for this video")

    except Exception as e:
        # Check if any subtitle was downloaded despite the error
        vtt_files = glob.glob(os.path.join(output_dir, f"{video_id}.*.vtt"))
        if vtt_files:
            print(f"   ✅ Subtitles downloaded (with warnings)")
            return vtt_files[0]

        raise Exception(f"Failed to download subtitles: {e}")

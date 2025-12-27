"""
main.py
──────────────────────────────────────────────
CLI entry point for video transcript extraction.

Usage:
    python main.py <video_url>
"""

import sys
import os
import shutil
from src.pipeline import process_video


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <video_url>")
        print("\nExample:")
        print("  python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        sys.exit(1)

    video_url = sys.argv[1]

    # Save to /home/bihsb/CD/src/extractor/data
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, "data")

    # Clean up temp folder before processing
    temp_dir = os.path.join(output_dir, "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print("🗑️  Cleaned up previous temp files")

    # Semantic segmentation enabled by default
    process_video(video_url, output_dir, use_semantic=True)

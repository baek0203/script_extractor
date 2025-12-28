"""
pipeline.py
──────────────────────────────────────────────
Video transcript extraction pipeline.

This module contains the main processing logic that coordinates
all extraction steps.
"""

import os
from datetime import datetime
from typing import Generator, Tuple, Dict

from .download import extract_video_info, download_subtitles
from .preprocessing import parse_vtt_file, merge_by_time_window
from .semantic_segmentation import segment_by_semantics
from .output import save_all_outputs


def process_video(video_url: str,
                 output_dir: str = "data/quick_start",
                 window_seconds: int = 25,
                 use_semantic: bool = True):
    """
    Complete video transcript extraction pipeline.

    Args:
        video_url: YouTube video URL
        output_dir: Directory to save output files
        window_seconds: Time window for merging segments (default: 25s)
        use_semantic: Enable semantic paragraph segmentation (default: True)

    Returns:
        dict: Paths to created output files

    Raises:
        Exception: If any step fails
    """
    print("=" * 80)
    title = "📹 Video Transcript Extractor"
    if use_semantic:
        title += " (Semantic Paragraphs)"
    print(title)
    print("=" * 80)

    # Create temp directory
    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Step 1: Extract video info
        print()
        video_info = extract_video_info(video_url)

        # Step 2: Download subtitles
        print()
        vtt_path = download_subtitles(video_url, video_info['id'], temp_dir)

        # Step 3: Parse and preprocess
        print()
        df = parse_vtt_file(vtt_path)

        if df.empty:
            raise Exception("No valid subtitle content found")

        # Step 4: Merge by time window
        df_merged = merge_by_time_window(df, window_seconds=window_seconds)

        if df_merged.empty:
            raise Exception("No data after merging")

        # Step 5: Semantic paragraph segmentation (if enabled)
        semantic_paragraphs = None
        topic_titles = None

        if use_semantic:
            print()
            print("🧠 Performing semantic segmentation...")
            semantic_paragraphs, topic_titles = segment_by_semantics(df_merged)

        # Step 6: Save outputs
        print()
        print("💾 Saving outputs...")
        output_paths = save_all_outputs(
            df_merged=df_merged,
            video_info=video_info,
            output_dir=output_dir,
            semantic_paragraphs=semantic_paragraphs,
            topic_titles=topic_titles
        )

        # Calculate stats
        total_words = sum(len(text.split()) for text in df_merged['text'].tolist())

        # Print summary
        print()
        print("✅ Processing complete!")
        print(f"   📊 CSV: {output_paths['csv']}")
        print(f"   📄 TXT (with titles): {output_paths['txt']}")
        if 'txt_plain' in output_paths:
            print(f"   📄 TXT (plain): {output_paths['txt_plain']}")
        if 'json' in output_paths:
            print(f"   📋 JSON: {output_paths['json']}")

        stats = f"   📈 Stats: {len(df_merged)} segments, {total_words} words"
        if use_semantic and semantic_paragraphs:
            stats += f", {len(semantic_paragraphs)} paragraphs"
        print(stats)

        # Cleanup temp files and folder
        print()
        print("🗑️  Cleaning up temporary files...")
        try:
            # Remove VTT file
            if os.path.exists(vtt_path):
                os.remove(vtt_path)
            # Remove entire temp directory
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            print("   ✅ Temporary files cleaned")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")

        print()
        print("=" * 80)
        print("✨ Done!")
        print("=" * 80)

        return output_paths

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


def process_video_progressive(video_url: str,
                              output_dir: str = "data/quick_start",
                              window_seconds: int = 25) -> Generator[Tuple[str, Dict], None, None]:
    """
    Progressive video transcript extraction pipeline.

    Yields results in two stages:
    1. Basic transcript (immediate)
    2. Semantic segmentation (advanced processing)

    Args:
        video_url: YouTube video URL
        output_dir: Directory to save output files
        window_seconds: Time window for merging segments (default: 25s)

    Yields:
        tuple: (stage, data)
            - stage: "basic" or "semantic"
            - data: dict with file paths and content

    Raises:
        Exception: If any step fails
    """
    import shutil

    # Create temp directory
    temp_dir = os.path.join(output_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Step 1: Extract video info
        video_info = extract_video_info(video_url)

        # Step 2: Download subtitles
        vtt_path = download_subtitles(video_url, video_info['id'], temp_dir)

        # Step 3: Parse and preprocess
        df = parse_vtt_file(vtt_path)

        if df.empty:
            raise Exception("No valid subtitle content found")

        # Step 4: Merge by time window
        df_merged = merge_by_time_window(df, window_seconds=window_seconds)

        if df_merged.empty:
            raise Exception("No data after merging")

        # Step 5: Save basic output (WITHOUT semantic segmentation)
        # This happens FAST
        basic_paths = save_all_outputs(
            df_merged=df_merged,
            video_info=video_info,
            output_dir=output_dir,
            semantic_paragraphs=None,  # No semantic yet
            topic_titles=None
        )

        # Read basic plain text
        basic_content = ""
        if basic_paths.get('txt') and os.path.exists(basic_paths['txt']):
            with open(basic_paths['txt'], 'r', encoding='utf-8') as f:
                basic_content = f.read()

        # Yield stage 1: Basic transcript (IMMEDIATE)
        yield ("basic", {
            "paths": basic_paths,
            "content": basic_content,
            "video_info": video_info
        })

        # Step 6: Semantic paragraph segmentation (SLOW - Advanced processing)
        semantic_paragraphs, topic_titles = segment_by_semantics(df_merged)

        # Step 7: Save semantic output
        semantic_paths = save_all_outputs(
            df_merged=df_merged,
            video_info=video_info,
            output_dir=output_dir,
            semantic_paragraphs=semantic_paragraphs,
            topic_titles=topic_titles
        )

        # Read semantic content
        semantic_content = ""
        if semantic_paths.get('txt') and os.path.exists(semantic_paths['txt']):
            with open(semantic_paths['txt'], 'r', encoding='utf-8') as f:
                semantic_content = f.read()

        # Yield stage 2: Semantic segmentation (DELAYED)
        yield ("semantic", {
            "paths": semantic_paths,
            "content": semantic_content,
            "video_info": video_info
        })

        # Cleanup temp files and folder
        try:
            if os.path.exists(vtt_path):
                os.remove(vtt_path)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Cleanup warning: {e}")

    except Exception as e:
        raise

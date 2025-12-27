"""
preprocessing.py
──────────────────────────────────────────────
Module for preprocessing subtitle files.

This module handles:
- VTT file parsing
- Text cleaning and deduplication
- Time window-based merging
"""

import re
import webvtt
import pandas as pd


def timestamp_to_seconds(timestamp: str) -> float:
    """
    Convert VTT timestamp to seconds.

    Args:
        timestamp: Timestamp in format "HH:MM:SS.mmm"

    Returns:
        float: Time in seconds
    """
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def clean_text(text: str) -> str:
    """
    Clean subtitle text by removing tags and normalizing whitespace.

    Args:
        text: Raw subtitle text

    Returns:
        str: Cleaned text
    """
    # Remove [Music], [Applause], etc.
    text = re.sub(r'\[.*?\]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def parse_vtt_file(vtt_path: str) -> pd.DataFrame:
    """
    Parse VTT subtitle file into DataFrame.

    Args:
        vtt_path: Path to VTT file

    Returns:
        DataFrame: Parsed subtitles with columns (start, end, start_sec, end_sec, text)
    """
    print(f"🔧 Processing subtitles...")
    records = []

    try:
        for caption in webvtt.read(vtt_path):
            text = caption.text.strip().replace('\n', ' ')
            if len(text.split()) >= 2:  # Only keep lines with 2+ words
                records.append({
                    "start": caption.start,
                    "end": caption.end,
                    "start_sec": timestamp_to_seconds(caption.start),
                    "end_sec": timestamp_to_seconds(caption.end),
                    "text": text
                })
    except Exception as e:
        print(f"⚠️ Error parsing VTT file: {e}")

    df = pd.DataFrame(records)
    if not df.empty:
        print(f"   📄 Original lines: {len(df)}")
    return df


def get_overlap_prefix(prev_words: list, curr_words: list) -> int:
    """
    Find overlapping words between two lists.

    Args:
        prev_words: Previous word list
        curr_words: Current word list

    Returns:
        int: Number of overlapping words
    """
    max_overlap = 0
    min_len = min(len(prev_words), len(curr_words))
    for i in range(1, min_len + 1):
        if prev_words[-i:] == curr_words[:i]:
            max_overlap = i
    return max_overlap


def remove_sequential_overlap(texts: list) -> str:
    """
    Remove sequential overlap from multiple text segments and merge.

    Example:
        Input: ["at some point you have", "you have to believe", "believe something"]
        Output: "at some point you have to believe something"

    Args:
        texts: List of text segments

    Returns:
        str: Merged text with duplicates removed
    """
    if not texts:
        return ""

    result_words = texts[0].lower().split()

    for i in range(1, len(texts)):
        curr_words = texts[i].lower().split()
        overlap = get_overlap_prefix(result_words, curr_words)
        new_words = curr_words[overlap:] if overlap > 0 else curr_words
        result_words.extend(new_words)

    return ' '.join(result_words)


def merge_by_time_window(df: pd.DataFrame, window_seconds: int = 25) -> pd.DataFrame:
    """
    Merge subtitle segments by time window.

    Args:
        df: DataFrame with parsed subtitles
        window_seconds: Time window for merging (default: 25s)

    Returns:
        DataFrame: Merged segments (start, end, text)
    """
    if df.empty:
        return pd.DataFrame()

    merged_segments = []
    current_segment = {
        'start': df.iloc[0]['start'],
        'start_sec': df.iloc[0]['start_sec'],
        'end': df.iloc[0]['end'],
        'end_sec': df.iloc[0]['end_sec'],
        'texts': [df.iloc[0]['text']]
    }

    for idx in range(1, len(df)):
        row = df.iloc[idx]

        segment_duration = row['start_sec'] - current_segment['start_sec']
        pause = row['start_sec'] - current_segment['end_sec']

        # End segment if: 1) window exceeded or 2) long pause (>3s)
        if segment_duration >= window_seconds or pause > 3.0:
            merged_text = remove_sequential_overlap(current_segment['texts'])
            merged_text = clean_text(merged_text)

            # Only save segments with 10+ words
            if merged_text and len(merged_text.split()) >= 10:
                merged_segments.append({
                    'start': current_segment['start'],
                    'end': current_segment['end'],
                    'text': merged_text
                })

            # Start new segment
            current_segment = {
                'start': row['start'],
                'start_sec': row['start_sec'],
                'end': row['end'],
                'end_sec': row['end_sec'],
                'texts': [row['text']]
            }
        else:
            # Add to current segment
            current_segment['texts'].append(row['text'])
            current_segment['end'] = row['end']
            current_segment['end_sec'] = row['end_sec']

    # Process last segment
    if current_segment['texts']:
        merged_text = remove_sequential_overlap(current_segment['texts'])
        merged_text = clean_text(merged_text)

        if merged_text and len(merged_text.split()) >= 10:
            merged_segments.append({
                'start': current_segment['start'],
                'end': current_segment['end'],
                'text': merged_text
            })

    df_merged = pd.DataFrame(merged_segments)
    if not df_merged.empty:
        print(f"   ⏱  Merged segments ({window_seconds}s window): {len(df_merged)}")
    return df_merged

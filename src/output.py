"""
output.py
──────────────────────────────────────────────
Module for saving processed transcripts in various formats.

This module handles:
- CSV output (structured data with timestamps)
- TXT output (human-readable text with semantic paragraphs)
- JSON output (structured semantic paragraphs with titles)
"""

import os
import re
import json
import pandas as pd
from datetime import datetime
from typing import List


def sanitize_filename(title: str) -> str:
    """
    Convert video title to valid filename.

    Args:
        title: Video title

    Returns:
        str: Sanitized filename (max 100 chars)
    """
    # Remove invalid filename characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores
    title = title.replace(' ', '_')
    # Limit length
    return title[:100]


def save_csv(df_merged: pd.DataFrame, output_path: str):
    """
    Save merged segments as CSV.

    Args:
        df_merged: DataFrame with merged segments
        output_path: Path to save CSV file
    """
    df_merged.to_csv(output_path, index=False, encoding="utf-8-sig")


def save_txt_basic(df_merged: pd.DataFrame, output_path: str, video_info: dict, max_line_length: int = 100):
    """
    Save transcript as plain text with sentences split by similar length.

    Args:
        df_merged: DataFrame with merged segments
        output_path: Path to save TXT file
        video_info: Video metadata
        max_line_length: Target maximum characters per line (default: 100)
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"Video: {video_info['title']}\n")
        f.write(f"URL: {video_info['url']}\n")
        f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Segments: {len(df_merged)}\n")
        f.write("=" * 80 + "\n\n")

        # Collect all text from segments
        all_text = ' '.join(df_merged['text'].tolist())

        # Split into sentences
        sentences = re.split(r'([.!?]+)', all_text)

        # Rebuild sentences with punctuation
        full_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i].strip()
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence:
                full_sentences.append(sentence)

        # Handle last part if no punctuation
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            full_sentences.append(sentences[-1].strip())

        # Combine sentences into lines with similar length
        current_line = ""
        for sentence in full_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # If adding this sentence exceeds max length and we have content, write the line
            if current_line and len(current_line) + len(sentence) + 1 > max_line_length:
                f.write(current_line.strip() + '\n')
                current_line = sentence + ' '
            else:
                current_line += sentence + ' '

        # Write remaining content
        if current_line.strip():
            f.write(current_line.strip() + '\n')


def save_txt_semantic_with_titles(paragraphs: List[List[str]], output_path: str, video_info: dict, titles: List[str] = None):
    """
    Save transcript as text with semantic paragraph segmentation and topic titles.

    Args:
        paragraphs: List of paragraphs (each paragraph is a list of sentences)
        output_path: Path to save TXT file
        video_info: Video metadata
        titles: Optional list of topic titles for each paragraph
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"Video: {video_info['title']}\n")
        f.write(f"URL: {video_info['url']}\n")
        f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Paragraphs: {len(paragraphs)}\n")
        f.write("=" * 80 + "\n\n")

        # Write each paragraph with title
        for i, paragraph in enumerate(paragraphs):
            # Write title if available
            if titles and i < len(titles):
                f.write(f"### {titles[i]}\n\n")
            
            # Join sentences in paragraph with space
            paragraph_text = ' '.join(paragraph)
            f.write(paragraph_text + '\n\n')


def save_txt_semantic_plain(paragraphs: List[List[str]], output_path: str, video_info: dict):
    """
    Save transcript as plain text with paragraph breaks only (no titles).

    Args:
        paragraphs: List of paragraphs (each paragraph is a list of sentences)
        output_path: Path to save TXT file
        video_info: Video metadata
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write(f"Video: {video_info['title']}\n")
        f.write(f"URL: {video_info['url']}\n")
        f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Paragraphs: {len(paragraphs)}\n")
        f.write("=" * 80 + "\n\n")

        # Write each paragraph with just line breaks
        for paragraph in paragraphs:
            paragraph_text = ' '.join(paragraph)
            f.write(paragraph_text + '\n\n')


def save_json_semantic(paragraphs: List[List[str]], output_path: str, video_info: dict, titles: List[str] = None):
    """
    Save transcript as JSON with semantic paragraphs and titles.

    Args:
        paragraphs: List of paragraphs (each paragraph is a list of sentences)
        output_path: Path to save JSON file
        video_info: Video metadata
        titles: Optional list of topic titles for each paragraph
    """
    # Build sections
    sections = []
    for i, paragraph in enumerate(paragraphs):
        section = {
            "title": titles[i] if titles and i < len(titles) else f"Topic {i+1}",
            "sentences": paragraph,
            "text": ' '.join(paragraph)
        }
        sections.append(section)
    
    # Build output data
    output_data = {
        "metadata": {
            "title": video_info['title'],
            "url": video_info['url'],
            "video_id": video_info.get('id', ''),
            "processed_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "num_sections": len(sections)
        },
        "sections": sections
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)


def save_all_outputs(df_merged: pd.DataFrame,
                    video_info: dict,
                    output_dir: str,
                    semantic_paragraphs: List[List[str]] = None,
                    topic_titles: List[str] = None) -> dict:
    """
    Save all output files (CSV, TXT with titles, TXT plain, JSON).

    Creates a dedicated folder for each video to organize outputs:
    data/
    └── Video_Title/
        ├── transcript.csv        # Raw transcript with timestamps
        ├── transcript.txt        # Semantic paragraphs with topic titles
        ├── transcript_plain.txt  # Semantic paragraphs (line breaks only)
        └── transcript.json       # Structured JSON with sections

    Args:
        df_merged: DataFrame with merged segments
        video_info: Video metadata
        output_dir: Base directory to save files
        semantic_paragraphs: Optional semantic paragraph segmentation
        topic_titles: Optional list of topic titles

    Returns:
        dict: Paths to created files
    """
    # Create video-specific folder
    safe_title = sanitize_filename(video_info['title'])
    video_folder = os.path.join(output_dir, safe_title)
    os.makedirs(video_folder, exist_ok=True)

    paths = {}

    # Save CSV (always)
    csv_path = os.path.join(video_folder, "transcript.csv")
    save_csv(df_merged, csv_path)
    paths['csv'] = csv_path

    # Save TXT files
    if semantic_paragraphs:
        # With titles
        txt_path = os.path.join(video_folder, "transcript.txt")
        save_txt_semantic_with_titles(semantic_paragraphs, txt_path, video_info, titles=topic_titles)
        paths['txt'] = txt_path
        
        # Plain (no titles, just line breaks)
        txt_plain_path = os.path.join(video_folder, "transcript_plain.txt")
        save_txt_semantic_plain(semantic_paragraphs, txt_plain_path, video_info)
        paths['txt_plain'] = txt_plain_path
    else:
        txt_path = os.path.join(video_folder, "transcript.txt")
        save_txt_basic(df_merged, txt_path, video_info)
        paths['txt'] = txt_path

    # Save JSON (if semantic paragraphs available)
    if semantic_paragraphs:
        json_path = os.path.join(video_folder, "transcript.json")
        save_json_semantic(semantic_paragraphs, json_path, video_info, titles=topic_titles)
        paths['json'] = json_path

    return paths

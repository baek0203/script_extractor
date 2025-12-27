"""
Video Transcript Extractor
──────────────────────────────────────────────
A modular system for extracting and processing YouTube video transcripts.

Modules:
- download: Video info extraction and subtitle downloading
- preprocessing: VTT parsing, text cleaning, and segment merging
- semantic_segmentation: AI-powered paragraph segmentation
- output: Multi-format output (CSV, TXT)
"""

from .download import extract_video_info, download_subtitles
from .preprocessing import parse_vtt_file, merge_by_time_window
from .semantic_segmentation import segment_by_semantics
from .output import save_all_outputs

__all__ = [
    'extract_video_info',
    'download_subtitles',
    'parse_vtt_file',
    'merge_by_time_window',
    'segment_by_semantics',
    'save_all_outputs',
]

# Technical Documentation

## System Architecture

### Overview
A modular Python system for extracting and processing YouTube video transcripts with semantic paragraph segmentation.

```
extractor/
├── main.py                      # CLI entry point
├── requirements.txt             # Python dependencies
└── src/
    ├── __init__.py              # Module exports
    ├── pipeline.py              # Main orchestrator
    ├── download.py              # Video info & subtitle downloading
    ├── preprocessing.py         # VTT parsing & text processing
    ├── speaker_detection.py     # Speaker identification (disabled by default)
    ├── semantic_segmentation.py # AI-powered paragraph segmentation
    └── output.py                # Multi-format output (CSV/TXT/JSON)
```

## Module Overview

### 1. download.py
Handles YouTube video metadata and subtitle downloading using yt-dlp.

**Key Functions:**
- `extract_video_info(video_url)` → dict
  - Extracts video ID and title
  - Returns: `{'id': str, 'title': str, 'url': str}`

- `download_subtitles(video_url, video_id, output_dir)` → str
  - Downloads English subtitles (manual or auto-generated)
  - Handles PO token requirements for YouTube
  - Returns: Path to VTT file

**Technical Details:**
- Uses yt-dlp with Android/Web client fallback
- Supports both manual and auto-generated subtitles
- Handles YouTube's SABR streaming requirements

### 2. preprocessing.py
Processes raw subtitle files into clean, merged segments.

**Key Functions:**
- `parse_vtt_file(vtt_path)` → pd.DataFrame
  - Parses WebVTT format
  - Extracts timestamps and text
  - Returns DataFrame with columns: `start`, `end`, `start_sec`, `end_sec`, `text`

- `merge_by_time_window(df, window_seconds=25)` → pd.DataFrame
  - Merges subtitle chunks within time windows
  - Default: 25-second windows
  - Removes sequential overlap

- `clean_text(text)` → str
  - Removes HTML tags and markup
  - Normalizes whitespace
  - Preserves sentence structure

- `remove_sequential_overlap(texts)` → list
  - Deduplicates repeated text across segments
  - Uses longest common substring algorithm

### 3. semantic_segmentation.py
AI-powered semantic paragraph segmentation using sentence embeddings.

**Key Functions:**
- `segment_by_semantics(df_merged, drop_ratio=0.65, min_paragraph_length=8, min_gap=5)` → List[List[str]]
  - Uses sentence-transformers (all-MiniLM-L6-v2)
  - Detects semantic shifts between sentences
  - Groups into human-like paragraphs (10-15 topics per video)

**Algorithm:**
1. Split text into sentences
2. Generate embeddings for each sentence
3. Compute cosine similarity between adjacent sentences
4. Detect boundaries where similarity drops below threshold
5. Enforce minimum gap (5 sentences) between boundaries
6. Group sentences into paragraphs (min 8 sentences each)

**Parameters:**
- `drop_ratio`: 0.65 (detects 35% similarity drop)
- `min_paragraph_length`: 8 sentences minimum
- `min_gap`: 5 sentences between boundaries

**Fallback:**
- If sentence-transformers not installed, uses simple 3-5 sentence grouping

### 4. speaker_detection.py
Identifies and normalizes speaker names (disabled by default).

**Key Functions:**
- `detect_speaker(text)` → str or None
  - Extracts speaker from "Name: text" pattern
  - Returns speaker name or None

- `extract_speakers_from_segments(df_merged)` → list
  - Attributes speakers to all segments
  - Propagates speaker labels forward

- `normalize_speaker_name(speaker, speaker_map)` → str
  - Handles abbreviations (e.g., "CA" → "Chris Anderson")
  - Matches initials to full names

### 5. output.py
Saves processed transcripts in multiple formats.

**Key Functions:**
- `save_csv(df_merged, output_path)`
  - Structured data with timestamps
  - UTF-8-BOM encoding for Excel compatibility

- `save_txt_semantic(paragraphs, output_path, video_info)`
  - Semantic paragraph formatting
  - Double-line breaks between paragraphs
  - Metadata header

- `save_txt_basic(df_merged, output_path, video_info, max_line_length=100)`
  - Fallback text formatting
  - Similar-length lines (~100 chars)

- `save_json(speaker_segments, output_path, video_info, unique_speakers)`
  - JSON with metadata and speaker attribution
  - Only generated with speaker detection enabled

### 6. pipeline.py
Main orchestrator that coordinates all extraction steps.

**Function:**
- `process_video(video_url, output_dir, window_seconds=25, with_speakers=False, use_semantic=True)`

**Pipeline Steps:**
1. Extract video info
2. Download subtitles
3. Parse VTT file
4. Merge by time window
5. Semantic paragraph segmentation (if enabled)
6. Speaker detection (if enabled)
7. Save outputs
8. Cleanup temp files

## Output Formats

### CSV Format
```csv
start,end,text
00:00:00.000,00:00:25.000,"Welcome to the show..."
00:00:25.000,00:00:50.000,"Thank you for having me..."
```

**Columns:**
- `start`: ISO timestamp (HH:MM:SS.mmm)
- `end`: ISO timestamp (HH:MM:SS.mmm)
- `text`: Merged and cleaned text

### TXT Format (Semantic)
```
Video: Example Video Title
URL: https://www.youtube.com/watch?v=VIDEO_ID
Processed: 2025-12-27 14:20:00
Paragraphs: 12
================================================================================

First semantic paragraph discussing topic A. Multiple sentences grouped together by meaning.

Second paragraph about topic B. Semantic shift detected automatically.
```

### JSON Format (with speakers)
```json
{
  "metadata": {
    "title": "Video Title",
    "url": "https://...",
    "video_id": "VIDEO_ID",
    "processed_time": "2025-12-27 14:20:00",
    "num_segments": 109,
    "num_speakers": 2
  },
  "speakers": ["Chris Anderson", "Sam Altman"],
  "transcript": [
    {
      "speaker": "Chris Anderson",
      "start": "00:00:00.000",
      "end": "00:00:25.000",
      "text": "..."
    }
  ]
}
```

## Dependencies

### Core Dependencies
- **yt-dlp** (>=2024.0.0): YouTube video/subtitle downloading
- **webvtt-py** (>=0.4.6): VTT file parsing
- **pandas** (>=2.0.0): Data processing and manipulation

### Optional Dependencies (Semantic Segmentation)
- **sentence-transformers** (>=2.2.0): Sentence embeddings
- **scikit-learn** (>=1.3.0): Cosine similarity computation
- **torch** (>=2.0.0): Deep learning backend

## Design Principles

### 1. Modularity
Each module has a single, clear responsibility:
- Download → Preprocessing → Segmentation → Output

### 2. Graceful Degradation
- Semantic segmentation falls back to simple grouping if dependencies missing
- Speaker detection is optional

### 3. Human-Centric
- Semantic segmentation tuned for 10-15 major topics (not 100+ micro-segments)
- Parameters designed for typical interview/talk formats

### 4. Error Handling
- Clear error messages at each pipeline step
- Informative output during processing

### 5. Clean Separation
- CLI (main.py) separate from business logic (src/)
- Data processing separate from I/O

## Advanced Usage

### Programmatic API

```python
from src.pipeline import process_video

# Full control over parameters
output_paths = process_video(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    output_dir="/custom/path",
    window_seconds=30,          # Merge 30-second chunks
    with_speakers=True,         # Enable speaker detection
    use_semantic=True           # Enable semantic segmentation
)
```

### Custom Semantic Parameters

Modify `src/semantic_segmentation.py`:

```python
# More aggressive topic separation (20-25 topics)
paragraphs = segment_by_semantics(
    df_merged,
    drop_ratio=0.75,           # Less strict (more boundaries)
    min_paragraph_length=5,    # Shorter paragraphs
    min_gap=3                  # Closer boundaries
)

# Fewer, longer topics (5-8 major themes)
paragraphs = segment_by_semantics(
    df_merged,
    drop_ratio=0.55,           # Very strict (fewer boundaries)
    min_paragraph_length=15,   # Longer paragraphs
    min_gap=10                 # Wide spacing
)
```

### Extending Output Formats

Add to `src/output.py`:

```python
def save_markdown(paragraphs, output_path, video_info):
    """Save transcript as Markdown with headers."""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {video_info['title']}\n\n")
        for i, paragraph in enumerate(paragraphs, 1):
            f.write(f"## Topic {i}\n\n")
            text = ' '.join(paragraph)
            f.write(f"{text}\n\n")
```

## Performance Considerations

### Memory Usage
- Sentence embeddings: ~100MB for 500 sentences
- Model loading: ~90MB (all-MiniLM-L6-v2)
- Typical video: <200MB total

### Processing Time
- Download: 5-10 seconds
- Parsing: <1 second
- Semantic segmentation: 10-30 seconds (CPU)
- Total: ~1 minute per video

### GPU Acceleration

Enable GPU for faster embeddings:

```python
paragraphs = segment_by_semantics(df_merged, use_gpu=True)
```

Requires CUDA-compatible GPU and PyTorch with CUDA support.

## Troubleshooting

### No Subtitles Available
- Check if video has captions enabled
- Try different video
- Some videos block automatic caption access

### PO Token Warnings
- Normal for certain YouTube videos
- System automatically tries multiple clients
- Usually resolves automatically

### Semantic Segmentation Not Working
- Install: `pip install sentence-transformers scikit-learn torch`
- Falls back to simple segmentation if not installed

### Too Many/Few Paragraphs
Adjust parameters in `src/semantic_segmentation.py`:
- Too many → Lower `drop_ratio`, increase `min_gap`
- Too few → Raise `drop_ratio`, decrease `min_gap`

## File Locations

### Output Files
- **Default**: `/home/bihsb/CD/src/extractor/data/`
- **Format**: `{Video_Title}.{csv|txt|json}`

### Temporary Files
- **Location**: `{output_dir}/temp/`
- **Contents**: Downloaded VTT files
- **Cleanup**: Automatic after processing

## Testing

```bash
# Test basic extraction
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Check output
ls data/
cat "data/Video_Title.txt"
```

## Future Extensions

Potential enhancements:
1. Multi-language support
2. Custom embedding models
3. Topic labeling (auto-generate titles)
4. Chapter detection
5. Highlight extraction
6. Summary generation
7. RAG integration

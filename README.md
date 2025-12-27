# YouTube Scripts Extractor

Extract and organize YouTube video transcripts with AI-powered semantic segmentation.

## Who Is This For?

- Anyone who wants to save video scripts as interview or lecture notes
- Those who need to find specific parts of video content
- People who want to organize video content as text
- Users who want to communicate with AI using transcripts

## Main Features

### 1. Automatic Download
Just insert the URL of the video you want to extract the script from.

### 2. Paragraph Segmentation
Separates sentences by topic using AI:
- For typical videos, the script is segmented into ~10-15 topic-based paragraphs
- Each paragraph consists of sentences with similar meaning

### 3. Output Formats
- **TXT file**: Easy to read, with optional topic titles
- **CSV file**: Viewable in Excel (includes timestamps)
- **JSON file**: Structured data with sections and metadata

## 📦 Installation

### Step 1: Check Python Installation
Run the following command in your terminal:

```bash
python --version
```

Python 3.8 or higher is required.

### Step 2: Install Dependencies

#### Basic Usage (Recommended)
```bash
pip install yt-dlp webvtt-py pandas
```

#### With AI Paragraph Segmentation
```bash
pip install -r requirements.txt
```

> **Note**: AI paragraph segmentation requires approximately 500MB of additional disk space.

## 🚀 Usage

### Basic Usage

1. Copy the URL of the YouTube video you want to extract.
2. Run the following command in your terminal:

```bash
python main.py VIDEO_URL
```

**Example:**
```bash
python main.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### View Results

When the program completes, files are created in the `data` folder:
```
data/
└── Video_Title/
    ├── transcript.txt        ← Open this file to read!
    ├── transcript_plain.txt  ← Plain text without topic titles
    ├── transcript.csv        ← Use this if you need timestamps
    └── transcript.json       ← Structured data for programmatic use
```

## 📄 Output Examples

### TXT File (With Topic Titles)
```
Video: OpenAI's Sam Altman Talks ChatGPT
URL: https://www.youtube.com/watch?v=...
Processed: 2025-12-27 14:20:00
Paragraphs: 12
================================================================================

### AI Future Discussion

Hello. Today we'll talk about the future of ChatGPT.
Artificial intelligence technology is rapidly advancing, and more changes
are expected in the future.

### AI Agents Overview

Moving on to the next topic, let's look at AI agents.
AI agents are systems that can perform complex tasks on behalf of users.
```

### CSV File (For Excel)
| Start Time | End Time | Content |
|------------|----------|---------|
| 00:00:00 | 00:00:25 | Hello. Today we'll... |
| 00:00:25 | 00:00:50 | Moving on to the next topic... |

### JSON File (Structured Data)
```json
{
  "metadata": {
    "title": "Video Title",
    "url": "https://...",
    "num_sections": 12
  },
  "sections": [
    {
      "title": "AI Future Discussion",
      "sentences": ["Hello.", "Today we'll talk about..."],
      "text": "Hello. Today we'll talk about..."
    }
  ]
}
```

## ❓ FAQ

### Q1. What videos are supported?
Any YouTube video with English subtitles is supported.

### Q2. Are other languages supported?
Currently, only English subtitles are supported.

### Q3. What about videos without subtitles?
You can use auto-generated subtitles if YouTube has created them.

### Q4. How long does it take?
Usually about 1 minute:
- Short videos (10 min): ~30 seconds
- Long videos (1 hour): ~1 minute

### Q5. What if an error occurs?
Check the following:
1. Internet connection status
2. Whether the YouTube URL is correct
3. Whether the video has subtitles

## 🎓 Real-World Use Cases

### Archiving Learning Materials
```bash
python main.py https://www.youtube.com/watch?v=LECTURE_VIDEO_URL
```
→ Save lecture content as text and search through it later.

### Organizing Interview Content
```bash
python main.py https://www.youtube.com/watch?v=INTERVIEW_VIDEO_URL
```
→ Read the full interview organized by topic.

### Using with AI Assistants
Send the generated TXT file to ChatGPT or Claude to:
- Summarize video content
- Explain specific sections
- Answer questions about the content

## 💡 Tips

### 1. Processing Multiple Videos
Save video URLs in a text file and run the script in a loop.

### 2. File Names Too Long?
File names are automatically truncated to 100 characters. Rename manually if needed.

### 3. Need Timestamp Information?
Open the CSV file to see exactly when each sentence was spoken.

## 🔧 Advanced Features (For Developers)

For technical details, see [tech.md](tech.md):
- System architecture
- Module descriptions
- Programming API
- Customization options

## 📞 Contact & Feedback

If you encounter issues or have suggestions:
- Open an issue on GitHub
- Or contact via email

## 📝 License

This program is free to use.

---

**Enjoy using it! 📚**

"""
llm_segmentation.py
──────────────────────────────────────────────
LLM-based semantic segmentation using Google Gemini.

This module uses Gemini 2.0 Flash (free) to:
- Segment transcript into meaningful topic-based paragraphs
- Generate topic titles for each segment
"""

import os
import pandas as pd
from typing import List, Tuple
import google.generativeai as genai
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()


def segment_with_gemini(df_merged: pd.DataFrame, api_key: str = None) -> Tuple[List[List[str]], List[str]]:
    """
    Segment transcript into semantic paragraphs using Gemini LLM.

    Args:
        df_merged: DataFrame with merged transcript segments
        api_key: Google AI API key (or use GEMINI_API_KEY from .env file)

    Returns:
        tuple: (paragraphs, topic_titles)
            - paragraphs: List of paragraphs (each is a list of sentences)
            - topic_titles: List of topic titles for each paragraph
    """
    # Get API key from parameter or environment variable
    if api_key is None:
        api_key = os.getenv('GEMINI_API_KEY')

    if not api_key:
        raise Exception("GEMINI_API_KEY not found. Please set it in .env file or pass it as parameter.")

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')

    # Prepare full transcript
    full_text = ' '.join(df_merged['text'].tolist())

    # Create prompt
    prompt = f"""You are a transcript segmentation expert. Analyze the following transcript and divide it into logical topic-based segments.

For each segment:
1. Group related sentences together that discuss the same topic
2. Create a concise, descriptive title (3-10 words) that summarizes what this segment is about
   - The title should capture the MAIN IDEA or KEY POINT being discussed
   - Use clear, informative language (NOT generic like "Topic 1", "Introduction", etc.)
   - Examples of GOOD titles:
     * "AI's Impact on Healthcare Diagnosis"
     * "Benefits of Remote Work for Employees"
     * "Climate Change Effects on Agriculture"
   - Examples of BAD titles:
     * "Topic 1"
     * "Introduction"
     * "Discussion"

Format your response as JSON:
{{
  "segments": [
    {{
      "title": "Specific descriptive title summarizing the main point",
      "text": "Full text of this segment..."
    }},
    ...
  ]
}}

Transcript:
{full_text}

Important:
- Keep the original text EXACTLY as is (don't modify, summarize, or translate)
- Create appropriately segments (depending on content length)
- Each segment should be a coherent topic
- Titles MUST be specific and descriptive, not generic labels
- The number of topic should be 8-15
"""

    try:
        # Call Gemini API
        print("   🤖 Calling Gemini API...")
        response = model.generate_content(prompt)
        result_text = response.text

        print(f"   📝 Gemini response length: {len(result_text)} characters")

        # Parse JSON response
        import json
        import re

        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            print("   ✅ Found JSON in markdown code block")
        else:
            json_str = result_text
            print("   ℹ️  Using raw response as JSON")

        result = json.loads(json_str)
        print(f"   ✅ Successfully parsed JSON")

        # Extract segments
        segments = result.get('segments', [])

        if not segments:
            raise Exception("No segments found in Gemini response")

        # Convert to expected format
        paragraphs = []
        topic_titles = []

        for segment in segments:
            title = segment.get('title', 'Untitled')
            text = segment.get('text', '')

            # Split text into sentences (simple split by '. ')
            sentences = [s.strip() + '.' for s in text.split('. ') if s.strip()]
            if sentences:
                # Remove trailing dot from last sentence if it has double dots
                if sentences[-1].endswith('..'):
                    sentences[-1] = sentences[-1][:-1]

            paragraphs.append(sentences)
            topic_titles.append(title)

        print(f"   ✅ Gemini segmentation: {len(paragraphs)} topics")
        return paragraphs, topic_titles

    except Exception as e:
        print(f"   ⚠️  Gemini segmentation failed: {e}")
        print(f"   ℹ️  Falling back to simple segmentation...")

        # Fallback: simple segmentation by length
        return simple_segmentation(df_merged)


def simple_segmentation(df_merged: pd.DataFrame) -> Tuple[List[List[str]], List[str]]:
    """
    Simple fallback segmentation by splitting into equal chunks.

    Args:
        df_merged: DataFrame with merged transcript segments

    Returns:
        tuple: (paragraphs, topic_titles)
    """
    sentences = df_merged['text'].tolist()

    # Split into ~10 segments
    num_segments = min(10, max(5, len(sentences) // 10))
    chunk_size = len(sentences) // num_segments

    paragraphs = []
    topic_titles = []

    for i in range(num_segments):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_segments - 1 else len(sentences)

        chunk = sentences[start_idx:end_idx]
        if chunk:
            paragraphs.append(chunk)
            topic_titles.append(f"Topic {i+1}")

    return paragraphs, topic_titles

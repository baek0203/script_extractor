"""
semantic_segmentation.py
──────────────────────────────────────────────
Semantic paragraph segmentation using sentence embeddings.

This module segments transcripts into meaningful paragraphs based on
semantic shifts between consecutive sentences.

Uses all-mpnet-base-v2 model for higher accuracy embeddings.
"""

import re
import numpy as np
from typing import List, Set, Tuple
import pandas as pd


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Args:
        text: Input text

    Returns:
        List of sentences
    """
    # Split by sentence endings
    sentences = re.split(r'([.!?]+)', text)

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

    return full_sentences


def compute_similarities(embeddings) -> List[float]:
    """
    Compute cosine similarity between adjacent sentence embeddings.

    Args:
        embeddings: Numpy array of sentence embeddings

    Returns:
        List of similarity scores
    """
    from sklearn.metrics.pairwise import cosine_similarity

    similarities = []
    for i in range(len(embeddings) - 1):
        sim = cosine_similarity(
            embeddings[i].reshape(1, -1),
            embeddings[i + 1].reshape(1, -1)
        )[0][0]
        similarities.append(sim)

    return similarities


def detect_boundaries(similarities: List[float], drop_ratio: float = 0.65, min_gap: int = 5) -> Set[int]:
    """
    Detect paragraph boundaries using relative drop strategy.

    Args:
        similarities: List of similarity scores between adjacent sentences
        drop_ratio: Threshold for detecting semantic shifts (default: 0.65)
        min_gap: Minimum sentences between boundaries to avoid over-segmentation

    Returns:
        Set of sentence indices where paragraph boundaries should occur
    """
    boundaries = set()

    if not similarities:
        return boundaries

    running_avg = similarities[0]
    last_boundary = -min_gap  # Allow first boundary immediately

    for i, sim in enumerate(similarities):
        # Detect sharp drop in similarity AND respect minimum gap
        if sim < running_avg * drop_ratio and (i + 1 - last_boundary) >= min_gap:
            boundaries.add(i + 1)
            last_boundary = i + 1

        # Update running average with exponential smoothing
        running_avg = 0.8 * running_avg + 0.2 * sim

    return boundaries


def detect_top_boundaries(similarities: List[float], 
                         target_paragraphs: int = 8,
                         min_gap: int = 10) -> Set[int]:
    """
    Detect exactly N-1 boundaries for N target paragraphs.
    
    Selects the top N-1 biggest similarity drops as boundaries,
    respecting minimum gap between boundaries.

    Args:
        similarities: List of similarity scores between adjacent sentences
        target_paragraphs: Target number of paragraphs (5-10 recommended)
        min_gap: Minimum sentences between boundaries

    Returns:
        Set of sentence indices where paragraph boundaries should occur
    """
    if not similarities or target_paragraphs < 2:
        return set()
    
    num_boundaries = target_paragraphs - 1
    
    # Calculate "drop score" for each position
    # Higher score = bigger topic shift
    drop_scores = []
    running_avg = similarities[0]
    
    for i, sim in enumerate(similarities):
        # Drop score = how much lower than running average
        drop = running_avg - sim
        drop_scores.append((i + 1, drop, sim))  # (index, drop_score, similarity)
        
        # Update running average
        running_avg = 0.9 * running_avg + 0.1 * sim
    
    # Sort by drop score (biggest drops first)
    drop_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Select top boundaries while respecting min_gap
    boundaries = set()
    
    for idx, drop, sim in drop_scores:
        if len(boundaries) >= num_boundaries:
            break
            
        # Check if this boundary respects min_gap from all existing boundaries
        valid = True
        for existing in boundaries:
            if abs(idx - existing) < min_gap:
                valid = False
                break
        
        if valid:
            boundaries.add(idx)
    
    return boundaries


def detect_elbow_boundaries(similarities: List[float], 
                           min_gap: int = 15,
                           min_paragraphs: int = 5,
                           max_paragraphs: int = 12) -> Set[int]:
    """
    Detect boundaries using elbow method - find where drops become insignificant.
    
    Automatically determines the number of paragraphs by finding the "elbow"
    point where similarity drops suddenly become much smaller.

    Args:
        similarities: List of similarity scores between adjacent sentences
        min_gap: Minimum sentences between boundaries
        min_paragraphs: Minimum number of paragraphs
        max_paragraphs: Maximum number of paragraphs

    Returns:
        Set of sentence indices where paragraph boundaries should occur
    """
    if not similarities:
        return set()
    
    # Calculate "drop score" for each position
    drop_scores = []
    running_avg = similarities[0]
    
    for i, sim in enumerate(similarities):
        drop = running_avg - sim
        drop_scores.append((i + 1, drop, sim))
        running_avg = 0.9 * running_avg + 0.1 * sim
    
    # Sort by drop score (biggest drops first)
    sorted_drops = sorted(drop_scores, key=lambda x: x[1], reverse=True)
    
    # Get just the drop values for analysis
    drop_values = [d[1] for d in sorted_drops]
    
    # Find the elbow: where the drop in drop-values is biggest
    # This indicates where "significant" drops end and "noise" begins
    if len(drop_values) < 3:
        return set()
    
    # Calculate differences between consecutive sorted drops
    diffs = []
    for i in range(len(drop_values) - 1):
        diff = drop_values[i] - drop_values[i + 1]
        diffs.append((i, diff))
    
    # Find the biggest "cliff" in drop values (elbow point)
    # Only look within min/max paragraph range
    best_elbow = min_paragraphs - 1
    best_diff = 0
    
    for i, diff in diffs:
        if min_paragraphs - 1 <= i < max_paragraphs - 1:
            if diff > best_diff:
                best_diff = diff
                best_elbow = i + 1  # Number of boundaries to use
    
    # Also consider if drops are all similar (no clear elbow) - use mean+std threshold
    mean_drop = np.mean(drop_values)
    std_drop = np.std(drop_values)
    threshold = mean_drop + 0.5 * std_drop
    
    # Count how many drops are above threshold
    significant_count = sum(1 for d in drop_values if d > threshold)
    
    # Use whichever gives a reasonable number in range
    num_boundaries = min(max(best_elbow, significant_count), max_paragraphs - 1)
    num_boundaries = max(num_boundaries, min_paragraphs - 1)
    
    print(f"   📊 Elbow analysis: {num_boundaries} significant topic shifts detected")
    
    # Select boundaries while respecting min_gap
    boundaries = set()
    
    for idx, drop, sim in sorted_drops:
        if len(boundaries) >= num_boundaries:
            break
            
        valid = True
        for existing in boundaries:
            if abs(idx - existing) < min_gap:
                valid = False
                break
        
        if valid:
            boundaries.add(idx)
    
    return boundaries


def group_into_paragraphs(sentences: List[str],
                         boundaries: Set[int],
                         min_paragraph_length: int = 2) -> List[List[str]]:
    """
    Group sentences into paragraphs based on detected boundaries.

    Args:
        sentences: List of sentences
        boundaries: Set of indices where paragraphs should start
        min_paragraph_length: Minimum number of sentences per paragraph

    Returns:
        List of paragraphs (each paragraph is a list of sentences)
    """
    paragraphs = []
    current = []

    for i, sent in enumerate(sentences):
        # Start new paragraph at boundary (if current has enough sentences)
        if i in boundaries and len(current) >= min_paragraph_length:
            paragraphs.append(current)
            current = []

        current.append(sent)

    # Add remaining sentences
    if current:
        # Merge with previous if too short
        if paragraphs and len(current) < min_paragraph_length:
            paragraphs[-1].extend(current)
        else:
            paragraphs.append(current)

    return paragraphs


def segment_by_semantics(df_merged: pd.DataFrame,
                        min_gap: int = 15,
                        min_paragraphs: int = 5,
                        max_paragraphs: int = 12,
                        use_gpu: bool = False,
                        extract_titles: bool = True,
                        **kwargs) -> Tuple[List[List[str]], List[str]]:
    """
    Segment transcript into semantic paragraphs based on topic shifts.

    Uses elbow method to automatically find significant topic boundaries.
    Only creates boundaries where similarity drops are meaningfully large.

    Args:
        df_merged: DataFrame with merged transcript segments
        min_gap: Minimum sentences between boundaries (default: 15)
        min_paragraphs: Minimum number of paragraphs (default: 5)
        max_paragraphs: Maximum number of paragraphs (default: 12)
        use_gpu: Whether to use GPU for embeddings
        extract_titles: Whether to extract topic titles for each paragraph

    Returns:
        Tuple of (paragraphs, titles):
            - paragraphs: List of paragraphs (each paragraph is a list of sentences)
            - titles: List of topic titles for each paragraph
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("⚠️  sentence-transformers not installed. Falling back to simple segmentation.")
        print("   Install with: pip install sentence-transformers")
        paragraphs = fallback_segmentation(df_merged)
        titles = [f"Topic {i+1}" for i in range(len(paragraphs))]
        return paragraphs, titles

    # Collect all text
    all_text = ' '.join(df_merged['text'].tolist())

    # Split into sentences
    sentences = split_into_sentences(all_text)

    if len(sentences) < 2:
        return [sentences], ["Topic 1"]

    print(f"   📝 Processing {len(sentences)} sentences...")

    # Load model (all-mpnet-base-v2: more accurate, larger model)
    device = 'cuda' if use_gpu else 'cpu'
    model = SentenceTransformer("all-mpnet-base-v2", device=device)

    # Generate embeddings
    print("   🧠 Generating semantic embeddings...")
    embeddings = model.encode(sentences, normalize_embeddings=True, show_progress_bar=False)

    # Compute similarities between consecutive sentences
    similarities = compute_similarities(embeddings)
    
    # Find boundaries using elbow method (automatic detection)
    print(f"   🎯 Finding significant topic boundaries (elbow method)...")
    boundaries = detect_elbow_boundaries(
        similarities, 
        min_gap=min_gap,
        min_paragraphs=min_paragraphs,
        max_paragraphs=max_paragraphs
    )
    paragraphs = group_into_paragraphs(sentences, boundaries, min_paragraph_length=5)
    
    print(f"   ✅ Created {len(paragraphs)} semantic paragraphs")

    # Extract topic titles
    titles = []
    if extract_titles:
        print("   🏷️  Extracting topic titles...")
        titles = extract_topic_titles(paragraphs, model=model)
        for i, title in enumerate(titles):
            print(f"      {i+1}. {title}")
    else:
        titles = [f"Topic {i+1}" for i in range(len(paragraphs))]

    return paragraphs, titles


def extract_topic_titles(paragraphs: List[List[str]], model=None) -> List[str]:
    """
    Extract topic titles for each paragraph using KeyBERT.
    
    Args:
        paragraphs: List of paragraphs (each paragraph is a list of sentences)
        model: Optional sentence-transformer model to reuse
        
    Returns:
        List of topic titles (noun phrases) for each paragraph
    """
    try:
        from keybert import KeyBERT
    except ImportError:
        print("   ⚠️  keybert not installed. Using fallback titles.")
        return [f"Topic {i+1}" for i in range(len(paragraphs))]
    
    # Initialize KeyBERT with the same model
    if model is not None:
        kw_model = KeyBERT(model=model)
    else:
        kw_model = KeyBERT(model="all-mpnet-base-v2")
    
    titles = []
    
    for i, paragraph in enumerate(paragraphs):
        # Combine sentences into one text
        text = ' '.join(paragraph)
        
        try:
            # Extract keyphrases (noun phrases preferred)
            keywords = kw_model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 3),  # 1-3 word phrases
                stop_words='english',
                top_n=3,
                use_mmr=True,  # Diversity
                diversity=0.5
            )
            
            if keywords:
                # Get the top keyphrase and capitalize
                title = keywords[0][0].title()
                titles.append(title)
            else:
                titles.append(f"Topic {i+1}")
                
        except Exception as e:
            titles.append(f"Topic {i+1}")
    
    return titles


def fallback_segmentation(df_merged: pd.DataFrame) -> List[List[str]]:
    """
    Fallback segmentation when sentence-transformers is not available.
    Uses simple sentence splitting without semantic analysis.

    Args:
        df_merged: DataFrame with merged transcript segments

    Returns:
        List of paragraphs (each paragraph is a list of sentences)
    """
    all_text = ' '.join(df_merged['text'].tolist())
    sentences = split_into_sentences(all_text)

    # Group every 3-5 sentences into a paragraph
    paragraphs = []
    current = []

    for i, sent in enumerate(sentences):
        current.append(sent)
        if len(current) >= 4 or i == len(sentences) - 1:
            paragraphs.append(current)
            current = []

    return paragraphs

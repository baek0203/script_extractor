"""
app.py
──────────────────────────────────────────────
Gradio web interface for YouTube Script Extractor.
"""

import os
import uuid
import shutil
import gradio as gr
from pathlib import Path

# Import the progressive processing function
from src.pipeline import process_video_progressive


def extract_transcript(youtube_url: str):
    """
    Extract transcript from YouTube video with progressive updates.

    Stage 1: Returns basic transcript immediately
    Stage 2: Returns semantic segmentation when ready

    Args:
        youtube_url: YouTube video URL

    Yields:
        tuple: (status, plain_content, semantic_content)
    """
    if not youtube_url or not youtube_url.strip():
        yield "⚠️ YouTube URL을 입력해주세요.", "", ""
        return

    # Validate URL format
    if not ("youtube.com" in youtube_url or "youtu.be" in youtube_url):
        yield "⚠️ 유효한 YouTube URL을 입력해주세요.", "", ""
        return

    # Create unique temporary directory for this request
    session_id = str(uuid.uuid4())[:8]
    temp_output_dir = os.path.join("data", f"session_{session_id}")

    try:
        # Process video progressively
        for stage, data in process_video_progressive(
            video_url=youtube_url,
            output_dir=temp_output_dir
        ):
            if stage == "basic":
                # Stage 1: Basic transcript ready (FAST)
                plain_content = data.get("content", "")
                yield (
                    "✅ 자막 다운로드 완료!\n\n⏳ Advanced processing is running...",
                    plain_content,
                    "처리 중..."
                )

            elif stage == "semantic":
                # Stage 2: Semantic segmentation ready (SLOW)
                semantic_content = data.get("content", "")
                yield (
                    "✅ 완료!",
                    plain_content,  # Keep the same plain content
                    semantic_content
                )

    except Exception as e:
        error_msg = str(e)

        # Provide user-friendly error messages
        if "No subtitles" in error_msg or "자막" in error_msg:
            yield "❌ 자막을 찾을 수 없습니다.", "", ""
        elif "Private video" in error_msg or "비공개" in error_msg:
            yield "❌ 비공개 또는 제한된 영상입니다.", "", ""
        elif "Video unavailable" in error_msg:
            yield "❌ 영상을 찾을 수 없습니다.", "", ""
        else:
            yield f"❌ 오류: {error_msg}", "", ""

    finally:
        # Cleanup temporary files
        try:
            if os.path.exists(temp_output_dir):
                shutil.rmtree(temp_output_dir)
        except Exception as e:
            print(f"Cleanup warning: {e}")


def cleanup_old_sessions():
    """Clean up old session directories to save disk space."""
    data_dir = Path("data")
    if not data_dir.exists():
        return

    try:
        for session_dir in data_dir.glob("session_*"):
            if session_dir.is_dir():
                shutil.rmtree(session_dir)
    except Exception as e:
        print(f"Cleanup warning: {e}")


# Create Gradio interface
with gr.Blocks(title="YouTube Script Extractor") as demo:

    gr.Markdown("# 📹 YouTube Script Extractor")

    with gr.Row():
        # Left side: Input
        with gr.Column(scale=1):
            url_input = gr.Textbox(
                label="YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                lines=2
            )

            extract_btn = gr.Button("Extract", variant="primary", size="lg")

            status_output = gr.Textbox(
                label="상태",
                lines=3,
                interactive=False
            )

        # Right side: Output
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📄 전문 자막"):
                    plain_output = gr.Textbox(
                        label="주제 구분 없는 전체 스크립트",
                        lines=25,
                        interactive=False,
                        placeholder="전문 자막이 여기에 표시됩니다..."
                    )

                with gr.Tab("📑 주제별 자막"):
                    semantic_output = gr.Textbox(
                        label="주제 단위로 구분된 스크립트",
                        lines=25,
                        interactive=False,
                        placeholder="주제별로 나뉜 자막이 여기에 표시됩니다..."
                    )

    # Event handler
    extract_btn.click(
        fn=extract_transcript,
        inputs=[url_input],
        outputs=[status_output, plain_output, semantic_output]
    )

    # Also trigger on Enter key
    url_input.submit(
        fn=extract_transcript,
        inputs=[url_input],
        outputs=[status_output, plain_output, semantic_output]
    )

    # Clean up old sessions on load
    demo.load(cleanup_old_sessions)


# Launch the app
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

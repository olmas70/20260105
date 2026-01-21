"""
SRT Formatter Module
Converts subtitle data to SRT format
"""

import logging
from typing import List, Dict, Any
from pathlib import Path


logger = logging.getLogger(__name__)


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (HH:MM:SS,mmm)

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string

    Example:
        >>> format_timestamp(65.5)
        '00:01:05,500'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def segments_to_srt(segments: List[Dict[str, Any]]) -> str:
    """
    Convert segments to SRT format

    Args:
        segments: List of subtitle segments with start, end, and text

    Returns:
        SRT formatted string

    Example segment:
        {
            "id": 1,
            "start": 0.0,
            "end": 3.5,
            "text": "안녕하세요"
        }
    """
    srt_lines = []

    for idx, segment in enumerate(segments, start=1):
        start_time = format_timestamp(segment["start"])
        end_time = format_timestamp(segment["end"])
        text = segment["text"].strip()

        # SRT format:
        # 1
        # 00:00:00,000 --> 00:00:03,500
        # 안녕하세요
        #
        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # Empty line between subtitles

    return "\n".join(srt_lines)


def save_srt(segments: List[Dict[str, Any]], output_path: str) -> str:
    """
    Save segments to SRT file

    Args:
        segments: List of subtitle segments
        output_path: Path to output SRT file

    Returns:
        Path to saved SRT file
    """
    output_path = Path(output_path)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert to SRT format
    srt_content = segments_to_srt(segments)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    logger.info(f"SRT file saved: {output_path} ({len(segments)} segments)")

    return str(output_path)


def parse_srt(srt_path: str) -> List[Dict[str, Any]]:
    """
    Parse SRT file to segments

    Args:
        srt_path: Path to SRT file

    Returns:
        List of segments

    Example:
        [
            {
                "id": 1,
                "start": 0.0,
                "end": 3.5,
                "text": "안녕하세요"
            },
            ...
        ]
    """
    segments = []

    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by double newline (subtitle blocks)
    blocks = content.strip().split("\n\n")

    for block in blocks:
        lines = block.strip().split("\n")

        if len(lines) < 3:
            continue

        # Parse subtitle block
        try:
            subtitle_id = int(lines[0])
            timestamp_line = lines[1]
            text = "\n".join(lines[2:])

            # Parse timestamps
            start_str, end_str = timestamp_line.split(" --> ")
            start = parse_timestamp(start_str)
            end = parse_timestamp(end_str)

            segments.append({
                "id": subtitle_id,
                "start": start,
                "end": end,
                "text": text
            })

        except Exception as e:
            logger.warning(f"Failed to parse subtitle block: {e}")
            continue

    logger.info(f"Parsed {len(segments)} segments from {srt_path}")

    return segments


def parse_timestamp(timestamp: str) -> float:
    """
    Parse SRT timestamp to seconds

    Args:
        timestamp: SRT timestamp string (HH:MM:SS,mmm)

    Returns:
        Time in seconds

    Example:
        >>> parse_timestamp("00:01:05,500")
        65.5
    """
    # Format: HH:MM:SS,mmm
    time_part, millis_part = timestamp.split(",")
    hours, minutes, seconds = map(int, time_part.split(":"))
    millis = int(millis_part)

    total_seconds = hours * 3600 + minutes * 60 + seconds + millis / 1000

    return total_seconds


def merge_short_segments(
    segments: List[Dict[str, Any]],
    min_duration: float = 1.0,
    max_chars: int = 100
) -> List[Dict[str, Any]]:
    """
    Merge short segments for better readability

    Args:
        segments: List of segments
        min_duration: Minimum duration for a segment (seconds)
        max_chars: Maximum characters per segment

    Returns:
        Merged segments
    """
    if not segments:
        return []

    merged = []
    current = segments[0].copy()

    for next_segment in segments[1:]:
        current_duration = current["end"] - current["start"]
        current_chars = len(current["text"])

        # Check if we should merge
        should_merge = (
            current_duration < min_duration and
            current_chars + len(next_segment["text"]) <= max_chars
        )

        if should_merge:
            # Merge segments
            current["end"] = next_segment["end"]
            current["text"] = current["text"] + " " + next_segment["text"]
        else:
            # Save current and start new
            merged.append(current)
            current = next_segment.copy()

    # Add last segment
    merged.append(current)

    logger.info(f"Merged {len(segments)} segments to {len(merged)} segments")

    return merged


if __name__ == "__main__":
    # Simple test
    test_segments = [
        {"id": 1, "start": 0.0, "end": 3.5, "text": "안녕하세요."},
        {"id": 2, "start": 3.5, "end": 7.2, "text": "오늘은 파이썬에 대해 알아보겠습니다."},
        {"id": 3, "start": 7.2, "end": 10.0, "text": "먼저 변수 선언 방법입니다."},
    ]

    # Test formatting
    srt_content = segments_to_srt(test_segments)
    print("SRT Format:")
    print(srt_content)
    print("\n" + "="*50 + "\n")

    # Test timestamp formatting
    print("Timestamp tests:")
    print(f"0.0s -> {format_timestamp(0.0)}")
    print(f"65.5s -> {format_timestamp(65.5)}")
    print(f"3661.123s -> {format_timestamp(3661.123)}")

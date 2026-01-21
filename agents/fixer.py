"""
Fixer Agent
Corrects subtitle errors using context metadata and generates final SRT file
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

from utils.api_client import ClaudeClient
from utils.srt_formatter import save_srt


logger = logging.getLogger(__name__)


class FixerAgent:
    """
    Fixer Agent - Third and final stage of subtitle pipeline

    Responsibilities:
    1. Read raw subtitle data and context metadata
    2. Correct each subtitle segment using Claude API
    3. Fix typos, spacing, punctuation based on context
    4. Distinguish homophones
    5. Generate final SRT file
    """

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        claude_model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 512,
        temperature: float = 0.1
    ):
        """
        Initialize Fixer Agent

        Args:
            claude_api_key: Anthropic API key for Claude
            claude_model: Claude model to use
            max_tokens: Maximum tokens per correction (lower for cost efficiency)
            temperature: Sampling temperature (lower = more deterministic)
        """
        self.claude_client = ClaudeClient(
            api_key=claude_api_key,
            model=claude_model,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def fix(
        self,
        raw_subtitle_path: str,
        context_metadata_path: str,
        output_srt_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fix subtitles and generate SRT file

        Args:
            raw_subtitle_path: Path to raw subtitle JSON from Generator
            context_metadata_path: Path to context metadata JSON from Analyzer
            output_srt_path: Path to output SRT file (optional)

        Returns:
            Dictionary with corrected subtitle data:
            {
                "source_file": str,
                "total_segments": int,
                "corrected_segments": int,
                "output_srt": str,
                "segments": [
                    {
                        "id": int,
                        "start": float,
                        "end": float,
                        "text": str,
                        "original_text": str,
                        "corrected": bool
                    }
                ]
            }
        """
        logger.info(f"Starting subtitle correction...")

        # Step 1: Load input data
        logger.info("Step 1/4: Loading input data...")
        raw_data = self._load_json(raw_subtitle_path)
        context_metadata = self._load_json(context_metadata_path)

        # Step 2: Correct each segment
        logger.info("Step 2/4: Correcting segments with Claude API...")
        corrected_segments = self._correct_segments(
            raw_data.get("segments", []),
            context_metadata
        )

        # Step 3: Generate SRT file
        logger.info("Step 3/4: Generating SRT file...")
        if output_srt_path is None:
            # Auto-generate output path
            video_path = Path(raw_data.get("video_path", "output"))
            output_srt_path = Path("data/output") / f"{video_path.stem}.srt"

        srt_path = save_srt(corrected_segments, str(output_srt_path))

        # Step 4: Format output
        logger.info("Step 4/4: Formatting output...")
        corrected_count = sum(1 for seg in corrected_segments if seg.get("corrected", False))

        result = {
            "source_file": raw_data.get("video_path", "unknown"),
            "total_segments": len(corrected_segments),
            "corrected_segments": corrected_count,
            "output_srt": str(srt_path),
            "segments": corrected_segments
        }

        logger.info(
            f"Correction complete: {corrected_count}/{len(corrected_segments)} segments corrected"
        )
        logger.info(f"SRT file saved: {srt_path}")

        return result

    def _load_json(self, path: str) -> Dict[str, Any]:
        """
        Load JSON file

        Args:
            path: Path to JSON file

        Returns:
            JSON data as dictionary
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data

    def _correct_segments(
        self,
        segments: List[Dict[str, Any]],
        context_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Correct all segments using Claude API

        Args:
            segments: List of raw subtitle segments
            context_metadata: Context metadata from Analyzer

        Returns:
            List of corrected segments
        """
        if not segments:
            logger.warning("No segments to correct")
            return []

        corrected_segments = []
        total = len(segments)

        # Extract compact context for prompts
        compact_context = self._extract_compact_context(context_metadata)

        for idx, segment in enumerate(segments, start=1):
            logger.info(f"Correcting segment {idx}/{total}...")

            try:
                # Correct segment
                corrected_text = self._correct_segment(segment, compact_context)

                # Check if text was actually corrected
                original_text = segment["text"].strip()
                was_corrected = corrected_text != original_text

                # Add to results
                corrected_segments.append({
                    "id": segment.get("id", idx),
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": corrected_text,
                    "original_text": original_text,
                    "corrected": was_corrected
                })

                if was_corrected:
                    logger.debug(f"  Original: {original_text}")
                    logger.debug(f"  Corrected: {corrected_text}")
                else:
                    logger.debug(f"  No changes needed")

            except Exception as e:
                logger.error(f"Failed to correct segment {idx}: {e}")
                # Keep original text on error
                corrected_segments.append({
                    "id": segment.get("id", idx),
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip(),
                    "original_text": segment["text"].strip(),
                    "corrected": False
                })

        return corrected_segments

    def _extract_compact_context(self, context_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract compact context for efficient prompting

        Args:
            context_metadata: Full context metadata

        Returns:
            Compact context dictionary
        """
        metadata = context_metadata.get("metadata", {})
        vocab = context_metadata.get("vocabulary", {})

        return {
            "topic": metadata.get("topic", "일반"),
            "domain": metadata.get("domain", "일반"),
            "technical_terms": vocab.get("technical_terms", [])[:15],  # Top 15
            "proper_nouns": vocab.get("proper_nouns", [])[:10],  # Top 10
            "error_patterns": context_metadata.get("error_patterns", [])[:5]  # Top 5
        }

    def _correct_segment(
        self,
        segment: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Correct a single segment using Claude API

        Args:
            segment: Subtitle segment
            context: Compact context metadata

        Returns:
            Corrected text
        """
        text = segment["text"].strip()

        # If text is very short or empty, return as-is
        if len(text) < 3:
            return text

        # Build system prompt
        system_prompt = """당신은 한국어 자막 교정 전문가입니다.
음성 인식으로 생성된 자막의 오류를 수정합니다.

교정 원칙:
1. 맞춤법과 띄어쓰기를 정확하게 수정
2. 문맥에 맞는 동음이의어 사용
3. 적절한 문장 부호 추가 (마침표, 쉼표 등)
4. 원문의 의미와 어조 유지
5. 과도한 수정 금지 (필요한 부분만 수정)

교정된 텍스트만 출력하세요. 설명이나 부가 정보는 제외하세요."""

        # Build user prompt
        technical_terms_str = ", ".join(context.get("technical_terms", [])[:10])
        proper_nouns_str = ", ".join(context.get("proper_nouns", [])[:8])

        user_prompt = f"""다음 자막을 교정하세요:

원본: {text}

문맥 정보:
- 주제: {context.get('topic', 'N/A')}
- 도메인: {context.get('domain', 'N/A')}
- 전문용어: {technical_terms_str if technical_terms_str else 'N/A'}
- 고유명사: {proper_nouns_str if proper_nouns_str else 'N/A'}

교정된 텍스트만 출력하세요."""

        try:
            corrected = self.claude_client.generate(
                user_prompt,
                system=system_prompt
            )

            # Clean up response
            corrected = corrected.strip()

            # Remove quotes if Claude added them
            if corrected.startswith('"') and corrected.endswith('"'):
                corrected = corrected[1:-1]
            elif corrected.startswith("'") and corrected.endswith("'"):
                corrected = corrected[1:-1]

            # If correction is suspiciously different (too long/short), keep original
            if len(corrected) > len(text) * 2 or len(corrected) < len(text) * 0.3:
                logger.warning(f"Suspicious correction length, keeping original: {text}")
                return text

            return corrected

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            # Return original on error
            return text

    def get_correction_summary(self, result: Dict[str, Any]) -> str:
        """
        Get human-readable summary of corrections

        Args:
            result: Correction result dictionary

        Returns:
            Formatted summary string
        """
        total = result.get("total_segments", 0)
        corrected = result.get("corrected_segments", 0)
        percentage = (corrected / total * 100) if total > 0 else 0

        summary = f"""
교정 요약:
---------
📝 총 자막 수: {total}개
✅ 교정된 자막: {corrected}개 ({percentage:.1f}%)
📄 출력 파일: {result.get('output_srt', 'N/A')}

변경 예시 (처음 3개):
"""

        # Show first 3 corrected segments
        segments = result.get("segments", [])
        corrected_examples = [
            seg for seg in segments
            if seg.get("corrected", False)
        ][:3]

        for seg in corrected_examples:
            summary += f"\n  원본: {seg.get('original_text', 'N/A')}\n"
            summary += f"  교정: {seg.get('text', 'N/A')}\n"

        return summary


def fix_subtitles(
    raw_subtitle_path: str,
    context_metadata_path: str,
    output_srt_path: Optional[str] = None,
    claude_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to fix subtitles

    Args:
        raw_subtitle_path: Path to raw subtitle JSON
        context_metadata_path: Path to context metadata JSON
        output_srt_path: Path to output SRT file
        claude_api_key: Anthropic API key

    Returns:
        Correction result dictionary
    """
    fixer = FixerAgent(claude_api_key=claude_api_key)
    return fixer.fix(raw_subtitle_path, context_metadata_path, output_srt_path)


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 3:
        print("Usage: python fixer.py <raw_subtitle_json> <context_metadata_json> [output_srt]")
        sys.exit(1)

    raw_subtitle_file = sys.argv[1]
    context_metadata_file = sys.argv[2]
    output_srt = sys.argv[3] if len(sys.argv) > 3 else None

    # Fix subtitles
    result = fix_subtitles(raw_subtitle_file, context_metadata_file, output_srt)

    # Print summary
    fixer = FixerAgent()
    print("\n" + "="*60)
    print(fixer.get_correction_summary(result))
    print("="*60)

    print(f"\n✅ Correction complete!")
    print(f"  - Total: {result['total_segments']} segments")
    print(f"  - Corrected: {result['corrected_segments']} segments")
    print(f"  - Output: {result['output_srt']}")

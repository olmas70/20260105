"""
Analyzer Agent
Analyzes subtitle context and extracts metadata for intelligent correction
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

from utils.api_client import ClaudeClient


logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """
    Analyzer Agent - Second stage of subtitle pipeline

    Responsibilities:
    1. Read raw subtitle data from Generator
    2. Analyze overall context and topic using Claude
    3. Extract technical terms and proper nouns
    4. Identify common error patterns
    5. Generate context metadata for Fixer
    """

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        claude_model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.3
    ):
        """
        Initialize Analyzer Agent

        Args:
            claude_api_key: Anthropic API key for Claude
            claude_model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
        """
        self.claude_client = ClaudeClient(
            api_key=claude_api_key,
            model=claude_model,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def analyze(
        self,
        raw_subtitle_path: str,
        output_json_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze subtitle context and generate metadata

        Args:
            raw_subtitle_path: Path to raw subtitle JSON from Generator
            output_json_path: Path to save context metadata JSON (optional)

        Returns:
            Dictionary with context metadata:
            {
                "source_file": str,
                "total_segments": int,
                "total_duration": float,
                "full_transcript": str,
                "metadata": {
                    "topic": str,
                    "domain": str,
                    "language_style": str,
                    "formality": str
                },
                "vocabulary": {
                    "technical_terms": list,
                    "proper_nouns": list,
                    "key_phrases": list
                },
                "error_patterns": [
                    {
                        "type": str,
                        "examples": list,
                        "correction_guide": str
                    }
                ]
            }
        """
        logger.info(f"Starting context analysis for: {raw_subtitle_path}")

        # Step 1: Load raw subtitle data
        logger.info("Step 1/4: Loading raw subtitle data...")
        raw_data = self._load_raw_subtitle(raw_subtitle_path)

        # Step 2: Extract full transcript
        logger.info("Step 2/4: Extracting full transcript...")
        full_transcript = self._extract_transcript(raw_data)

        # Step 3: Analyze context with Claude
        logger.info("Step 3/4: Analyzing context with Claude API...")
        analysis = self._analyze_with_claude(full_transcript)

        # Step 4: Format output
        logger.info("Step 4/4: Formatting output...")
        result = {
            "source_file": raw_data.get("video_path", "unknown"),
            "total_segments": len(raw_data.get("segments", [])),
            "total_duration": raw_data.get("duration", 0.0),
            "full_transcript": full_transcript,
            "metadata": analysis.get("metadata", {}),
            "vocabulary": analysis.get("vocabulary", {}),
            "error_patterns": analysis.get("error_patterns", [])
        }

        # Save to JSON if path provided
        if output_json_path:
            self._save_json(result, output_json_path)

        logger.info(
            f"Analysis complete: topic='{result['metadata'].get('topic', 'N/A')}', "
            f"domain='{result['metadata'].get('domain', 'N/A')}'"
        )

        return result

    def _load_raw_subtitle(self, path: str) -> Dict[str, Any]:
        """
        Load raw subtitle JSON file

        Args:
            path: Path to raw subtitle JSON

        Returns:
            Raw subtitle data dictionary
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Raw subtitle file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data.get('segments', []))} segments from {path}")

        return data

    def _extract_transcript(self, raw_data: Dict[str, Any]) -> str:
        """
        Extract full transcript from segments

        Args:
            raw_data: Raw subtitle data

        Returns:
            Full transcript as string
        """
        segments = raw_data.get("segments", [])

        if not segments:
            raise ValueError("No segments found in raw subtitle data")

        # Combine all segment texts
        transcript_parts = [seg["text"].strip() for seg in segments]
        full_transcript = " ".join(transcript_parts)

        logger.info(f"Extracted transcript: {len(full_transcript)} characters")

        return full_transcript

    def _analyze_with_claude(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript using Claude API

        Args:
            transcript: Full transcript text

        Returns:
            Analysis result dictionary
        """
        system_prompt = """당신은 한국어 텍스트 분석 전문가입니다.
주어진 대화/강의 스크립트를 분석하여 문맥, 주제, 전문용어 등을 파악하고,
음성 인식에서 발생할 수 있는 오류 패턴을 예측합니다.

분석 결과는 반드시 유효한 JSON 형식으로만 출력하세요.
다른 설명이나 마크다운 없이 순수 JSON만 반환하세요."""

        user_prompt = f"""다음 스크립트를 분석하세요:

{transcript[:5000]}  # 처음 5000자만 분석 (비용 절감)

다음 정보를 JSON 형식으로 추출하세요:

{{
  "metadata": {{
    "topic": "주제를 한 문장으로 요약 (예: 파이썬 프로그래밍 기초 강의)",
    "domain": "도메인/분야 (예: 기술/IT, 교육, 비즈니스, 일상, 엔터테인먼트 등)",
    "language_style": "언어 스타일 (예: 설명형, 대화형, 강의형, 발표형 등)",
    "formality": "격식 수준 (예: 격식, 보통, 비격식)"
  }},
  "vocabulary": {{
    "technical_terms": ["전문용어1", "전문용어2", ...],  # 최대 20개
    "proper_nouns": ["고유명사1", "고유명사2", ...],  # 인명, 지명, 브랜드명 등, 최대 15개
    "key_phrases": ["핵심구문1", "핵심구문2", ...]  # 자주 반복되는 중요 표현, 최대 10개
  }},
  "error_patterns": [
    {{
      "type": "spacing",
      "examples": ["변수선언 → 변수 선언", "데이터타입 → 데이터 타입"],
      "correction_guide": "합성어 띄어쓰기 규칙 적용"
    }},
    {{
      "type": "homophone",
      "examples": ["설명하겟습니다 → 설명하겠습니다"],
      "correction_guide": "'-겠-' 어미 교정"
    }}
  ]
}}

반드시 위 형식의 JSON만 출력하세요."""

        try:
            response = self.claude_client.generate(user_prompt, system=system_prompt)

            # Parse JSON response
            import re

            # Try to extract JSON from response
            # Claude sometimes adds markdown code blocks
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                analysis = json.loads(json_str)
            else:
                # Fallback: try parsing entire response
                analysis = json.loads(response)

            # Validate structure
            required_keys = ["metadata", "vocabulary", "error_patterns"]
            for key in required_keys:
                if key not in analysis:
                    logger.warning(f"Missing key '{key}' in Claude response, using defaults")
                    analysis[key] = {}

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Claude response: {e}")
            logger.debug(f"Claude response: {response[:500]}")

            # Return minimal valid structure
            return {
                "metadata": {
                    "topic": "분석 실패",
                    "domain": "unknown",
                    "language_style": "unknown",
                    "formality": "unknown"
                },
                "vocabulary": {
                    "technical_terms": [],
                    "proper_nouns": [],
                    "key_phrases": []
                },
                "error_patterns": []
            }

        except Exception as e:
            logger.error(f"Failed to analyze with Claude: {e}")
            raise

    def _save_json(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Save data to JSON file

        Args:
            data: Data to save
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved context metadata to: {output_path}")

    def get_summary(self, context_metadata: Dict[str, Any]) -> str:
        """
        Get human-readable summary of analysis

        Args:
            context_metadata: Context metadata dictionary

        Returns:
            Formatted summary string
        """
        metadata = context_metadata.get("metadata", {})
        vocab = context_metadata.get("vocabulary", {})

        summary = f"""
분석 요약:
---------
📌 주제: {metadata.get('topic', 'N/A')}
📂 도메인: {metadata.get('domain', 'N/A')}
✍️  언어 스타일: {metadata.get('language_style', 'N/A')}
🎯 격식: {metadata.get('formality', 'N/A')}

📚 어휘:
  - 전문용어: {len(vocab.get('technical_terms', []))}개
  - 고유명사: {len(vocab.get('proper_nouns', []))}개
  - 핵심구문: {len(vocab.get('key_phrases', []))}개

⚠️  예상 오류 패턴: {len(context_metadata.get('error_patterns', []))}개
"""
        return summary


def analyze_subtitles(
    raw_subtitle_path: str,
    output_json_path: Optional[str] = None,
    claude_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze subtitles

    Args:
        raw_subtitle_path: Path to raw subtitle JSON
        output_json_path: Path to save context metadata JSON
        claude_api_key: Anthropic API key

    Returns:
        Context metadata dictionary
    """
    analyzer = AnalyzerAgent(claude_api_key=claude_api_key)
    return analyzer.analyze(raw_subtitle_path, output_json_path)


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <raw_subtitle_json> [output_json]")
        sys.exit(1)

    raw_subtitle_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "data/temp/context_metadata.json"

    # Analyze subtitles
    result = analyze_subtitles(raw_subtitle_file, output_json)

    # Print summary
    analyzer = AnalyzerAgent()
    print("\n" + "="*60)
    print(analyzer.get_summary(result))
    print("="*60)

    print(f"\n✅ Analysis complete!")
    print(f"  - Output: {output_json}")

    # Show some vocabulary
    vocab = result.get("vocabulary", {})
    if vocab.get("technical_terms"):
        print(f"\n📚 전문용어 (처음 5개):")
        for term in vocab["technical_terms"][:5]:
            print(f"  - {term}")

    if vocab.get("proper_nouns"):
        print(f"\n🏷️  고유명사 (처음 5개):")
        for noun in vocab["proper_nouns"][:5]:
            print(f"  - {noun}")

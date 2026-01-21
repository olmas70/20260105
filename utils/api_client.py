"""
API Client Module
Handles API calls to OpenAI (Whisper) and Anthropic (Claude)
"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

from openai import OpenAI
from anthropic import Anthropic


logger = logging.getLogger(__name__)


class WhisperClient:
    """Client for OpenAI Whisper API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: Optional[str] = "ko",
        response_format: str = "verbose_json",
        temperature: float = 0.0
    ):
        """
        Initialize Whisper API client

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Whisper model to use
            language: Language code (e.g., 'ko' for Korean, None for auto-detect)
            response_format: Response format (json, text, srt, verbose_json, vtt)
            temperature: Sampling temperature (0-1, lower = more deterministic)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.language = language
        self.response_format = response_format
        self.temperature = temperature

    def transcribe(
        self,
        audio_path: str,
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Whisper API

        Args:
            audio_path: Path to audio file (max 25MB)
            prompt: Optional prompt to guide the model
            language: Language code (overrides default)
            response_format: Response format (overrides default)

        Returns:
            Transcription result as dictionary

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If API call fails
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Check file size (Whisper limit: 25MB)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(
                f"Audio file too large: {file_size_mb:.2f} MB "
                f"(max 25 MB). Please split the file."
            )

        logger.info(f"Transcribing audio: {audio_path} ({file_size_mb:.2f} MB)")

        try:
            with open(audio_path, "rb") as audio_file:
                kwargs = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": response_format or self.response_format,
                    "temperature": self.temperature,
                }

                # Add optional parameters
                if language or self.language:
                    kwargs["language"] = language or self.language

                if prompt:
                    kwargs["prompt"] = prompt

                # Call API
                response = self.client.audio.transcriptions.create(**kwargs)

                # Convert to dict if needed
                if hasattr(response, "model_dump"):
                    result = response.model_dump()
                else:
                    result = dict(response)

                logger.info(f"Transcription completed: {len(result.get('text', ''))} characters")

                return result

        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            raise RuntimeError(f"Failed to transcribe audio: {e}")

    def transcribe_with_timestamps(
        self,
        audio_path: str,
        prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio with detailed timestamps for each segment

        Args:
            audio_path: Path to audio file
            prompt: Optional prompt to guide the model

        Returns:
            List of segments with timestamps:
            [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 3.5,
                    "text": "안녕하세요"
                },
                ...
            ]
        """
        result = self.transcribe(
            audio_path,
            prompt=prompt,
            response_format="verbose_json"
        )

        segments = result.get("segments", [])

        logger.info(f"Found {len(segments)} segments")

        return segments


class ClaudeClient:
    """Client for Anthropic Claude API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
        temperature: float = 0.3
    ):
        """
        Initialize Claude API client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate text using Claude API

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens (overrides default)
            temperature: Temperature (overrides default)

        Returns:
            Generated text
        """
        logger.info(f"Calling Claude API with prompt length: {len(prompt)}")

        try:
            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)

            # Extract text from response
            text = response.content[0].text

            logger.info(f"Claude response length: {len(text)}")

            return text

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise RuntimeError(f"Failed to generate text: {e}")

    def analyze_context(self, transcript: str) -> Dict[str, Any]:
        """
        Analyze transcript context using Claude

        Args:
            transcript: Full transcript text

        Returns:
            Context analysis dictionary
        """
        system_prompt = """당신은 한국어 텍스트 분석 전문가입니다.
주어진 대화/강의 스크립트를 분석하여 문맥, 주제, 전문용어 등을 파악합니다.
JSON 형식으로 결과를 반환하세요."""

        user_prompt = f"""다음 스크립트를 분석하세요:

{transcript}

다음 정보를 JSON 형식으로 추출하세요:
1. topic: 주제 (한 줄 요약)
2. domain: 도메인/분야 (예: 기술, 교육, 일상, 비즈니스 등)
3. language_style: 언어 스타일 (예: 설명형, 대화형, 강의형 등)
4. technical_terms: 전문용어 리스트
5. proper_nouns: 고유명사 리스트 (인명, 지명, 브랜드명 등)

JSON만 출력하세요."""

        response = self.generate(user_prompt, system=system_prompt)

        # Parse JSON (Claude usually returns clean JSON)
        import json
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise ValueError("Failed to parse JSON from Claude response")

        return result

    def fix_subtitle(
        self,
        segment: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Fix subtitle segment using context

        Args:
            segment: Subtitle segment with text
            context: Context metadata from analyzer

        Returns:
            Corrected subtitle text
        """
        text = segment.get("text", "")

        system_prompt = """당신은 한국어 자막 교정 전문가입니다.
음성 인식으로 생성된 자막의 오타, 띄어쓰기, 문장 부호를 교정합니다.
문맥을 고려하여 정확한 한국어로 수정하세요."""

        user_prompt = f"""다음 자막을 교정하세요:

원본: {text}

문맥 정보:
- 주제: {context.get('topic', 'N/A')}
- 도메인: {context.get('domain', 'N/A')}
- 전문용어: {', '.join(context.get('technical_terms', [])[:10])}

교정 사항:
1. 오타 수정
2. 띌쓰기 교정
3. 문장 부호 추가/수정
4. 동음이의어 구분

교정된 텍스트만 출력하세요 (설명 없이)."""

        corrected = self.generate(user_prompt, system=system_prompt)

        return corrected.strip()


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    # Test Whisper client
    if len(sys.argv) >= 2:
        audio_file = sys.argv[1]
        client = WhisperClient()
        result = client.transcribe_with_timestamps(audio_file)
        print(f"Transcribed {len(result)} segments")
        for seg in result[:3]:
            print(f"  {seg['start']:.2f}s - {seg['end']:.2f}s: {seg['text']}")

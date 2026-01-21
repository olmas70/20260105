"""
Test Fixer Agent
"""

import pytest
import os
import json
from pathlib import Path
from agents.fixer import FixerAgent, fix_subtitles


# Mock raw subtitle data for testing
MOCK_RAW_SUBTITLE = {
    "video_path": "data/input/test_video.mp4",
    "audio_path": "data/temp/test_video.wav",
    "language": "ko",
    "duration": 120.5,
    "segments": [
        {
            "id": 1,
            "start": 0.0,
            "end": 3.5,
            "text": "안녕하세요 오늘은 파이썬프로그래밍에 대해 알아보겠습니다"
        },
        {
            "id": 2,
            "start": 3.5,
            "end": 7.2,
            "text": "먼저 변수선언 방법을 설명하겟습니다"
        },
        {
            "id": 3,
            "start": 7.2,
            "end": 12.0,
            "text": "파이썬에서는 변수타입을명시하지않아도됩니다"
        }
    ]
}

# Mock context metadata
MOCK_CONTEXT_METADATA = {
    "source_file": "data/input/test_video.mp4",
    "total_segments": 3,
    "total_duration": 120.5,
    "full_transcript": "안녕하세요 오늘은 파이썬프로그래밍에 대해...",
    "metadata": {
        "topic": "파이썬 프로그래밍 기초",
        "domain": "기술/IT",
        "language_style": "강의형",
        "formality": "보통"
    },
    "vocabulary": {
        "technical_terms": ["파이썬", "변수", "변수선언", "데이터타입"],
        "proper_nouns": ["Python"],
        "key_phrases": ["알아보겠습니다", "설명하겠습니다"]
    },
    "error_patterns": [
        {
            "type": "spacing",
            "examples": ["변수선언 → 변수 선언", "데이터타입 → 데이터 타입"],
            "correction_guide": "합성어 띄어쓰기 규칙 적용"
        },
        {
            "type": "homophone",
            "examples": ["설명하겟습니다 → 설명하겠습니다"],
            "correction_guide": "'-겠-' 어미 교정"
        }
    ]
}


@pytest.fixture
def mock_files(tmp_path):
    """Create mock input files"""
    # Create raw subtitle file
    raw_subtitle_file = tmp_path / "raw_subtitle.json"
    with open(raw_subtitle_file, "w", encoding="utf-8") as f:
        json.dump(MOCK_RAW_SUBTITLE, f, ensure_ascii=False, indent=2)

    # Create context metadata file
    context_metadata_file = tmp_path / "context_metadata.json"
    with open(context_metadata_file, "w", encoding="utf-8") as f:
        json.dump(MOCK_CONTEXT_METADATA, f, ensure_ascii=False, indent=2)

    return {
        "raw_subtitle": str(raw_subtitle_file),
        "context_metadata": str(context_metadata_file),
        "output_dir": tmp_path
    }


class TestFixerAgent:
    """Test cases for Fixer Agent"""

    def test_initialization(self):
        """Test agent initialization"""
        # Should work without API key (will use env var)
        agent = FixerAgent()
        assert agent.claude_client.model == "claude-3-5-sonnet-20241022"
        assert agent.claude_client.max_tokens == 512

    def test_initialization_with_custom_params(self):
        """Test agent with custom parameters"""
        agent = FixerAgent(
            claude_model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.2
        )
        assert agent.claude_client.max_tokens == 1024
        assert agent.claude_client.temperature == 0.2

    def test_load_json(self, mock_files):
        """Test JSON loading"""
        agent = FixerAgent()
        data = agent._load_json(mock_files["raw_subtitle"])

        assert "segments" in data
        assert len(data["segments"]) == 3
        assert data["language"] == "ko"

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        agent = FixerAgent()

        with pytest.raises(FileNotFoundError):
            agent._load_json("nonexistent.json")

    def test_extract_compact_context(self, mock_files):
        """Test compact context extraction"""
        agent = FixerAgent()
        context_metadata = agent._load_json(mock_files["context_metadata"])
        compact = agent._extract_compact_context(context_metadata)

        assert "topic" in compact
        assert "domain" in compact
        assert "technical_terms" in compact
        assert "proper_nouns" in compact
        assert compact["topic"] == "파이썬 프로그래밍 기초"
        assert len(compact["technical_terms"]) <= 15

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_correct_segment_with_real_api(self, mock_files):
        """Test segment correction with real Claude API (requires API key)"""
        agent = FixerAgent()
        context_metadata = agent._load_json(mock_files["context_metadata"])
        compact_context = agent._extract_compact_context(context_metadata)

        segment = {
            "id": 1,
            "start": 0.0,
            "end": 3.5,
            "text": "안녕하세요 오늘은 파이썬프로그래밍에 대해 알아보겠습니다"
        }

        corrected = agent._correct_segment(segment, compact_context)

        # Verify correction
        assert isinstance(corrected, str)
        assert len(corrected) > 0
        # Should have proper spacing
        assert "파이썬 프로그래밍" in corrected or "파이썬프로그래밍" in corrected

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_fix_with_real_api(self, mock_files):
        """Test full correction pipeline with real API (requires API key)"""
        agent = FixerAgent()

        output_srt = mock_files["output_dir"] / "output.srt"

        result = agent.fix(
            mock_files["raw_subtitle"],
            mock_files["context_metadata"],
            str(output_srt)
        )

        # Verify result structure
        assert "source_file" in result
        assert "total_segments" in result
        assert "corrected_segments" in result
        assert "output_srt" in result
        assert "segments" in result

        # Verify segments
        assert len(result["segments"]) == 3
        for seg in result["segments"]:
            assert "id" in seg
            assert "start" in seg
            assert "end" in seg
            assert "text" in seg
            assert "original_text" in seg
            assert "corrected" in seg

        # Verify SRT file was created
        assert Path(output_srt).exists()

        # Verify SRT file content
        with open(output_srt, "r", encoding="utf-8") as f:
            srt_content = f.read()
            assert "안녕하세요" in srt_content
            assert "-->" in srt_content

    def test_get_correction_summary(self):
        """Test summary generation"""
        agent = FixerAgent()

        mock_result = {
            "source_file": "test.mp4",
            "total_segments": 10,
            "corrected_segments": 5,
            "output_srt": "output.srt",
            "segments": [
                {
                    "id": 1,
                    "start": 0.0,
                    "end": 3.0,
                    "text": "안녕하세요.",
                    "original_text": "안녕하세요",
                    "corrected": True
                },
                {
                    "id": 2,
                    "start": 3.0,
                    "end": 6.0,
                    "text": "파이썬 프로그래밍",
                    "original_text": "파이썬프로그래밍",
                    "corrected": True
                }
            ]
        }

        summary = agent.get_correction_summary(mock_result)
        assert isinstance(summary, str)
        assert "10개" in summary
        assert "5개" in summary
        assert "50.0%" in summary
        assert "output.srt" in summary


class TestUtilityFunctions:
    """Test utility functions"""

    def test_fix_subtitles_function(self):
        """Test convenience function"""
        # This will fail without API key and valid files, but tests interface
        with pytest.raises(FileNotFoundError):
            fix_subtitles(
                "nonexistent1.json",
                "nonexistent2.json",
                claude_api_key="fake-key"
            )


class TestIntegration:
    """Integration tests"""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_full_correction_pipeline(self, mock_files):
        """Test full correction pipeline"""
        output_srt = mock_files["output_dir"] / "final.srt"

        # Run correction
        result = fix_subtitles(
            mock_files["raw_subtitle"],
            mock_files["context_metadata"],
            str(output_srt)
        )

        # Verify result
        assert result["total_segments"] == 3
        assert result["corrected_segments"] >= 0
        assert Path(output_srt).exists()

        # Verify SRT format
        with open(output_srt, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.strip().split("\n")

            # Should have proper SRT format
            assert lines[0] == "1"  # First subtitle number
            assert "-->" in lines[1]  # Timestamp line

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_end_to_end_pipeline(self, tmp_path):
        """Test complete pipeline: Generator → Analyzer → Fixer"""
        # This test requires all three agents and API keys
        # Skip if not in integration test mode
        pytest.skip("Full pipeline test - run manually with real video")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

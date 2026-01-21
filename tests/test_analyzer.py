"""
Test Analyzer Agent
"""

import pytest
import os
import json
from pathlib import Path
from agents.analyzer import AnalyzerAgent, analyze_subtitles


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
            "text": "안녕하세요 오늘은 파이썬 프로그래밍에 대해 알아보겠습니다"
        },
        {
            "id": 2,
            "start": 3.5,
            "end": 7.2,
            "text": "먼저 변수선언 방법을 설명하겠습니다"
        },
        {
            "id": 3,
            "start": 7.2,
            "end": 12.0,
            "text": "파이썬에서는 변수타입을 명시하지 않아도 됩니다"
        }
    ]
}


@pytest.fixture
def mock_raw_subtitle_file(tmp_path):
    """Create a mock raw subtitle JSON file"""
    file_path = tmp_path / "raw_subtitle.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(MOCK_RAW_SUBTITLE, f, ensure_ascii=False, indent=2)
    return str(file_path)


class TestAnalyzerAgent:
    """Test cases for Analyzer Agent"""

    def test_initialization(self):
        """Test agent initialization"""
        # Should work without API key (will use env var)
        agent = AnalyzerAgent()
        assert agent.claude_client.model == "claude-3-5-sonnet-20241022"
        assert agent.claude_client.max_tokens == 4096

    def test_initialization_with_custom_params(self):
        """Test agent with custom parameters"""
        agent = AnalyzerAgent(
            claude_model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            temperature=0.5
        )
        assert agent.claude_client.max_tokens == 2048
        assert agent.claude_client.temperature == 0.5

    def test_load_raw_subtitle(self, mock_raw_subtitle_file):
        """Test loading raw subtitle file"""
        agent = AnalyzerAgent()
        data = agent._load_raw_subtitle(mock_raw_subtitle_file)

        assert "segments" in data
        assert len(data["segments"]) == 3
        assert data["language"] == "ko"
        assert data["duration"] == 120.5

    def test_load_nonexistent_file(self):
        """Test loading nonexistent file"""
        agent = AnalyzerAgent()

        with pytest.raises(FileNotFoundError):
            agent._load_raw_subtitle("nonexistent.json")

    def test_extract_transcript(self, mock_raw_subtitle_file):
        """Test transcript extraction"""
        agent = AnalyzerAgent()
        data = agent._load_raw_subtitle(mock_raw_subtitle_file)
        transcript = agent._extract_transcript(data)

        assert isinstance(transcript, str)
        assert len(transcript) > 0
        assert "파이썬" in transcript
        assert "변수선언" in transcript

    def test_extract_transcript_empty_segments(self):
        """Test transcript extraction with empty segments"""
        agent = AnalyzerAgent()
        data = {"segments": []}

        with pytest.raises(ValueError):
            agent._extract_transcript(data)

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_analyze_with_real_api(self, mock_raw_subtitle_file):
        """Test analysis with real Claude API (requires API key)"""
        agent = AnalyzerAgent()
        result = agent.analyze(
            mock_raw_subtitle_file,
            output_json_path="data/temp/test_context_metadata.json"
        )

        # Verify result structure
        assert "source_file" in result
        assert "total_segments" in result
        assert "total_duration" in result
        assert "full_transcript" in result
        assert "metadata" in result
        assert "vocabulary" in result
        assert "error_patterns" in result

        # Verify metadata
        metadata = result["metadata"]
        assert "topic" in metadata
        assert "domain" in metadata
        assert "language_style" in metadata

        # Verify vocabulary
        vocab = result["vocabulary"]
        assert "technical_terms" in vocab
        assert "proper_nouns" in vocab
        assert "key_phrases" in vocab

    def test_get_summary(self, mock_raw_subtitle_file):
        """Test summary generation"""
        agent = AnalyzerAgent()

        # Create mock context metadata
        context_metadata = {
            "metadata": {
                "topic": "파이썬 프로그래밍",
                "domain": "기술/IT",
                "language_style": "강의형",
                "formality": "보통"
            },
            "vocabulary": {
                "technical_terms": ["파이썬", "변수", "데이터타입"],
                "proper_nouns": ["Python"],
                "key_phrases": ["알아보겠습니다"]
            },
            "error_patterns": [
                {
                    "type": "spacing",
                    "examples": ["변수선언 → 변수 선언"]
                }
            ]
        }

        summary = agent.get_summary(context_metadata)
        assert isinstance(summary, str)
        assert "파이썬 프로그래밍" in summary
        assert "기술/IT" in summary
        assert "3개" in summary  # technical terms count

    def test_save_json(self, tmp_path):
        """Test JSON saving"""
        agent = AnalyzerAgent()
        output_path = tmp_path / "output.json"

        test_data = {
            "test": "data",
            "number": 123,
            "korean": "한글"
        }

        agent._save_json(test_data, str(output_path))

        # Verify file was created
        assert output_path.exists()

        # Verify content
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded == test_data


class TestUtilityFunctions:
    """Test utility functions"""

    def test_analyze_subtitles_function(self):
        """Test convenience function"""
        # This will fail without API key and valid file, but tests interface
        with pytest.raises((ValueError, FileNotFoundError)):
            analyze_subtitles(
                "nonexistent.json",
                claude_api_key="fake-key"
            )


class TestIntegration:
    """Integration tests"""

    @pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set"
    )
    def test_full_analysis_pipeline(self, mock_raw_subtitle_file, tmp_path):
        """Test full analysis pipeline"""
        output_path = tmp_path / "context_metadata.json"

        # Run analysis
        result = analyze_subtitles(
            mock_raw_subtitle_file,
            str(output_path)
        )

        # Verify result
        assert result["total_segments"] == 3
        assert result["total_duration"] == 120.5
        assert len(result["full_transcript"]) > 0

        # Verify output file
        assert output_path.exists()

        # Verify can reload
        with open(output_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            assert loaded == result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

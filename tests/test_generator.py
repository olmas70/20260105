"""
Test Generator Agent
"""

import pytest
import os
from pathlib import Path
from agents.generator import GeneratorAgent, generate_subtitles


# Mock data for testing
MOCK_VIDEO_PATH = "data/input/test_video.mp4"


class TestGeneratorAgent:
    """Test cases for Generator Agent"""

    def test_initialization(self):
        """Test agent initialization"""
        # Should work without API key (will use env var)
        agent = GeneratorAgent(language="ko")
        assert agent.whisper_client.language == "ko"
        assert agent.whisper_client.model == "whisper-1"

    def test_initialization_with_custom_params(self):
        """Test agent with custom parameters"""
        agent = GeneratorAgent(
            whisper_model="whisper-1",
            language="en",
            temp_dir="data/temp/custom"
        )
        assert agent.whisper_client.language == "en"
        assert agent.temp_dir == Path("data/temp/custom")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set"
    )
    def test_generate_with_real_api(self):
        """Test generation with real API (requires video file and API key)"""
        if not Path(MOCK_VIDEO_PATH).exists():
            pytest.skip(f"Test video not found: {MOCK_VIDEO_PATH}")

        agent = GeneratorAgent(language="ko")
        result = agent.generate(
            MOCK_VIDEO_PATH,
            output_json_path="data/temp/test_output.json"
        )

        # Verify result structure
        assert "video_path" in result
        assert "audio_path" in result
        assert "language" in result
        assert "duration" in result
        assert "segments" in result

        # Verify segments
        assert isinstance(result["segments"], list)
        if len(result["segments"]) > 0:
            seg = result["segments"][0]
            assert "id" in seg
            assert "start" in seg
            assert "end" in seg
            assert "text" in seg

    def test_temp_dir_creation(self):
        """Test temporary directory creation"""
        temp_dir = "data/temp/test_temp"
        agent = GeneratorAgent(temp_dir=temp_dir)
        assert Path(temp_dir).exists()
        assert Path(temp_dir).is_dir()

    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files"""
        agent = GeneratorAgent(temp_dir="data/temp/test_cleanup")

        # Create a dummy file
        dummy_file = agent.temp_dir / "dummy.wav"
        dummy_file.touch()
        assert dummy_file.exists()

        # Cleanup
        agent.cleanup_temp_files(str(dummy_file))
        assert not dummy_file.exists()


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_subtitles_function(self):
        """Test convenience function"""
        # This will fail without API key and video file, but tests interface
        with pytest.raises((ValueError, FileNotFoundError)):
            generate_subtitles(
                "nonexistent_video.mp4",
                whisper_api_key="fake-key"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

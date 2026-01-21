"""
Generator Agent
Extracts audio from video and generates initial subtitles using Whisper API
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

from utils.audio_extractor import AudioExtractor
from utils.api_client import WhisperClient


logger = logging.getLogger(__name__)


class GeneratorAgent:
    """
    Generator Agent - First stage of subtitle pipeline

    Responsibilities:
    1. Extract audio from MP4 video
    2. Call Whisper API for speech-to-text
    3. Generate raw subtitle data with timestamps
    """

    def __init__(
        self,
        whisper_api_key: Optional[str] = None,
        whisper_model: str = "whisper-1",
        language: str = "ko",
        temp_dir: str = "data/temp"
    ):
        """
        Initialize Generator Agent

        Args:
            whisper_api_key: OpenAI API key for Whisper
            whisper_model: Whisper model to use
            language: Language code (e.g., 'ko' for Korean)
            temp_dir: Directory for temporary files
        """
        self.audio_extractor = AudioExtractor(
            output_format="wav",
            sample_rate=16000,
            channels=1
        )

        self.whisper_client = WhisperClient(
            api_key=whisper_api_key,
            model=whisper_model,
            language=language,
            response_format="verbose_json"
        )

        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        video_path: str,
        output_json_path: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate raw subtitles from video

        Args:
            video_path: Path to input video file
            output_json_path: Path to save raw subtitle JSON (optional)
            prompt: Optional prompt to guide Whisper

        Returns:
            Dictionary with raw subtitle data:
            {
                "video_path": str,
                "audio_path": str,
                "language": str,
                "duration": float,
                "segments": [
                    {
                        "id": int,
                        "start": float,
                        "end": float,
                        "text": str
                    },
                    ...
                ]
            }
        """
        logger.info(f"Starting subtitle generation for: {video_path}")

        # Step 1: Extract audio from video
        logger.info("Step 1/3: Extracting audio from video...")
        audio_path = self._extract_audio(video_path)

        # Step 2: Transcribe audio using Whisper
        logger.info("Step 2/3: Transcribing audio using Whisper API...")
        segments = self._transcribe_audio(audio_path, prompt)

        # Step 3: Format output
        logger.info("Step 3/3: Formatting output...")
        result = {
            "video_path": str(video_path),
            "audio_path": str(audio_path),
            "language": self.whisper_client.language,
            "duration": segments[-1]["end"] if segments else 0.0,
            "segments": segments
        }

        # Save to JSON if path provided
        if output_json_path:
            self._save_json(result, output_json_path)

        logger.info(
            f"Generation complete: {len(segments)} segments, "
            f"duration: {result['duration']:.2f}s"
        )

        return result

    def _extract_audio(self, video_path: str) -> str:
        """
        Extract audio from video file

        Args:
            video_path: Path to video file

        Returns:
            Path to extracted audio file
        """
        video_path = Path(video_path)

        # Generate audio path in temp directory
        audio_filename = video_path.stem + ".wav"
        audio_path = self.temp_dir / audio_filename

        # Extract audio
        try:
            self.audio_extractor.extract(str(video_path), str(audio_path))

            # Log audio info
            audio_info = self.audio_extractor.get_audio_info(str(audio_path))
            logger.info(
                f"Audio extracted: {audio_info['duration']:.2f}s, "
                f"{audio_info['size_mb']:.2f} MB"
            )

            return str(audio_path)

        except Exception as e:
            logger.error(f"Failed to extract audio: {e}")
            raise

    def _transcribe_audio(
        self,
        audio_path: str,
        prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio using Whisper API

        Args:
            audio_path: Path to audio file
            prompt: Optional prompt to guide transcription

        Returns:
            List of segments with timestamps
        """
        try:
            # Check file size
            audio_path_obj = Path(audio_path)
            file_size_mb = audio_path_obj.stat().st_size / (1024 * 1024)

            if file_size_mb > 25:
                logger.warning(
                    f"Audio file is large ({file_size_mb:.2f} MB). "
                    f"Consider splitting for better results."
                )
                # TODO: Implement chunking for large files
                raise ValueError(
                    f"Audio file too large: {file_size_mb:.2f} MB (max 25 MB)"
                )

            # Transcribe with Whisper
            segments = self.whisper_client.transcribe_with_timestamps(
                audio_path,
                prompt=prompt
            )

            # Format segments
            formatted_segments = []
            for seg in segments:
                formatted_segments.append({
                    "id": seg.get("id", len(formatted_segments) + 1),
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip()
                })

            return formatted_segments

        except Exception as e:
            logger.error(f"Failed to transcribe audio: {e}")
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

        logger.info(f"Saved raw subtitle data to: {output_path}")

    def cleanup_temp_files(self, audio_path: Optional[str] = None) -> None:
        """
        Clean up temporary files

        Args:
            audio_path: Specific audio file to delete (optional)
        """
        if audio_path:
            try:
                Path(audio_path).unlink()
                logger.info(f"Cleaned up temp file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {audio_path}: {e}")
        else:
            # Clean all temp audio files
            for audio_file in self.temp_dir.glob("*.wav"):
                try:
                    audio_file.unlink()
                    logger.info(f"Cleaned up temp file: {audio_file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {audio_file}: {e}")


def generate_subtitles(
    video_path: str,
    output_json_path: Optional[str] = None,
    whisper_api_key: Optional[str] = None,
    language: str = "ko",
    prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to generate subtitles from video

    Args:
        video_path: Path to input video file
        output_json_path: Path to save raw subtitle JSON
        whisper_api_key: OpenAI API key
        language: Language code
        prompt: Optional prompt for Whisper

    Returns:
        Raw subtitle data dictionary
    """
    generator = GeneratorAgent(
        whisper_api_key=whisper_api_key,
        language=language
    )

    return generator.generate(
        video_path,
        output_json_path,
        prompt
    )


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python generator.py <video_file> [output_json]")
        sys.exit(1)

    video_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "data/temp/raw_subtitle.json"

    # Generate subtitles
    result = generate_subtitles(video_file, output_json)

    print(f"\n✅ Generation complete!")
    print(f"  - Segments: {len(result['segments'])}")
    print(f"  - Duration: {result['duration']:.2f}s")
    print(f"  - Output: {output_json}")

    # Show first 3 segments
    print(f"\n📝 First 3 segments:")
    for seg in result['segments'][:3]:
        print(f"  [{seg['start']:.2f}s - {seg['end']:.2f}s] {seg['text']}")

"""
Audio Extractor Module
Extracts audio from video files using FFmpeg
"""

import os
import logging
from pathlib import Path
from typing import Optional
import ffmpeg


logger = logging.getLogger(__name__)


class AudioExtractor:
    """Extracts audio from video files using FFmpeg"""

    def __init__(
        self,
        output_format: str = "wav",
        sample_rate: int = 16000,
        channels: int = 1,
        codec: str = "pcm_s16le"
    ):
        """
        Initialize AudioExtractor

        Args:
            output_format: Output audio format (wav, mp3, etc.)
            sample_rate: Audio sample rate in Hz (Whisper recommends 16000)
            channels: Number of audio channels (1=mono, 2=stereo)
            codec: Audio codec to use
        """
        self.output_format = output_format
        self.sample_rate = sample_rate
        self.channels = channels
        self.codec = codec

        # Check if FFmpeg is installed
        self._check_ffmpeg()

    def _check_ffmpeg(self) -> None:
        """Check if FFmpeg is installed"""
        try:
            ffmpeg.probe("dummy")  # Will fail but checks if ffmpeg exists
        except ffmpeg.Error:
            pass  # Expected error, ffmpeg exists
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg is not installed. Please install FFmpeg:\n"
                "  Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                "  macOS: brew install ffmpeg\n"
                "  Windows: Download from https://ffmpeg.org/download.html"
            )

    def extract(
        self,
        video_path: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Extract audio from video file

        Args:
            video_path: Path to input video file
            output_path: Path to output audio file (optional)

        Returns:
            Path to extracted audio file

        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If FFmpeg fails
        """
        # Validate input
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Generate output path if not provided
        if output_path is None:
            output_path = video_path.with_suffix(f".{self.output_format}")
        else:
            output_path = Path(output_path)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting audio from {video_path} to {output_path}")

        try:
            # Get video info
            probe = ffmpeg.probe(str(video_path))

            # Check if video has audio stream
            audio_streams = [
                stream for stream in probe['streams']
                if stream['codec_type'] == 'audio'
            ]

            if not audio_streams:
                raise RuntimeError(f"No audio stream found in {video_path}")

            # Extract audio
            stream = ffmpeg.input(str(video_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec=self.codec,
                ar=self.sample_rate,
                ac=self.channels,
                format=self.output_format
            )

            # Run FFmpeg (overwrite output if exists)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            logger.info(f"Audio extracted successfully: {output_path}")

            # Get file size
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Output file size: {file_size_mb:.2f} MB")

            return str(output_path)

        except ffmpeg.Error as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            logger.error(f"FFmpeg error: {error_msg}")
            raise RuntimeError(f"Failed to extract audio: {error_msg}")

    def get_video_duration(self, video_path: str) -> float:
        """
        Get duration of video in seconds

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['format']['duration'])
            return duration
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            raise

    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get audio file information

        Args:
            audio_path: Path to audio file

        Returns:
            Dictionary with audio information
        """
        try:
            probe = ffmpeg.probe(audio_path)
            audio_stream = next(
                stream for stream in probe['streams']
                if stream['codec_type'] == 'audio'
            )

            return {
                'duration': float(probe['format']['duration']),
                'sample_rate': int(audio_stream['sample_rate']),
                'channels': int(audio_stream['channels']),
                'codec': audio_stream['codec_name'],
                'size_mb': float(probe['format']['size']) / (1024 * 1024)
            }
        except Exception as e:
            logger.error(f"Failed to get audio info: {e}")
            raise


def extract_audio_from_video(
    video_path: str,
    output_path: Optional[str] = None,
    **kwargs
) -> str:
    """
    Convenience function to extract audio from video

    Args:
        video_path: Path to input video file
        output_path: Path to output audio file (optional)
        **kwargs: Additional arguments for AudioExtractor

    Returns:
        Path to extracted audio file
    """
    extractor = AudioExtractor(**kwargs)
    return extractor.extract(video_path, output_path)


if __name__ == "__main__":
    # Simple test
    import sys

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python audio_extractor.py <video_file>")
        sys.exit(1)

    video_file = sys.argv[1]
    output_file = extract_audio_from_video(video_file)
    print(f"Audio extracted to: {output_file}")

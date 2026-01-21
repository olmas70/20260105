"""
Main Pipeline Script
Runs the complete subtitle generation and correction pipeline
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from agents.generator import generate_subtitles
from agents.analyzer import analyze_subtitles
from agents.fixer import fix_subtitles


# Setup logging
def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Suppress verbose logs from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)


def print_banner():
    """Print welcome banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🎬 YouTube Subtitle Generation & Correction System 🎬     ║
║                                                              ║
║   Generator → Analyzer → Fixer → Perfect Subtitles!         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_step(step_num: int, total_steps: int, title: str):
    """Print step header"""
    print(f"\n{'='*60}")
    print(f"  📌 Step {step_num}/{total_steps}: {title}")
    print(f"{'='*60}\n")


def check_api_keys():
    """Check if required API keys are set"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    missing = []
    if not openai_key:
        missing.append("OPENAI_API_KEY")
    if not anthropic_key:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        print("❌ Error: Missing required API keys!")
        print(f"   Please set the following environment variables:")
        for key in missing:
            print(f"   - {key}")
        print(f"\n   You can set them in a .env file or export them in your shell.")
        return False

    return True


def run_pipeline(
    input_video: str,
    output_srt: Optional[str] = None,
    language: str = "ko",
    keep_temp: bool = False,
    verbose: bool = False
) -> bool:
    """
    Run the complete subtitle generation pipeline

    Args:
        input_video: Path to input video file
        output_srt: Path to output SRT file (optional)
        language: Language code (default: "ko")
        keep_temp: Keep temporary files (default: False)
        verbose: Verbose logging (default: False)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Setup
        input_path = Path(input_video)
        if not input_path.exists():
            print(f"❌ Error: Input video file not found: {input_video}")
            return False

        # Generate temp file paths
        temp_dir = Path("data/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        video_stem = input_path.stem
        raw_subtitle_path = temp_dir / f"{video_stem}_raw.json"
        context_metadata_path = temp_dir / f"{video_stem}_context.json"

        # Generate output path if not provided
        if output_srt is None:
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_srt = str(output_dir / f"{video_stem}.srt")
        else:
            Path(output_srt).parent.mkdir(parents=True, exist_ok=True)

        # Print input info
        file_size_mb = input_path.stat().st_size / (1024 * 1024)
        print(f"📹 Input video: {input_path}")
        print(f"📏 File size: {file_size_mb:.2f} MB")
        print(f"🌐 Language: {language}")
        print(f"📄 Output SRT: {output_srt}")

        # ============================================================
        # STEP 1: Generator - Audio to Text
        # ============================================================
        print_step(1, 3, "Generator - Audio to Text (Whisper API)")

        print("🎙️  Extracting audio and transcribing...")
        raw_subtitle = generate_subtitles(
            video_path=str(input_path),
            output_json_path=str(raw_subtitle_path),
            language=language
        )

        segments_count = len(raw_subtitle['segments'])
        duration = raw_subtitle['duration']

        print(f"✅ Success!")
        print(f"   - Segments: {segments_count}")
        print(f"   - Duration: {duration:.2f}s ({duration/60:.1f} minutes)")
        print(f"   - Output: {raw_subtitle_path}")

        # ============================================================
        # STEP 2: Analyzer - Context Analysis
        # ============================================================
        print_step(2, 3, "Analyzer - Context Analysis (Claude API)")

        print("🔍 Analyzing context and vocabulary...")
        context = analyze_subtitles(
            raw_subtitle_path=str(raw_subtitle_path),
            output_json_path=str(context_metadata_path)
        )

        metadata = context.get('metadata', {})
        vocab = context.get('vocabulary', {})

        print(f"✅ Success!")
        print(f"   - Topic: {metadata.get('topic', 'N/A')}")
        print(f"   - Domain: {metadata.get('domain', 'N/A')}")
        print(f"   - Technical terms: {len(vocab.get('technical_terms', []))}")
        print(f"   - Proper nouns: {len(vocab.get('proper_nouns', []))}")
        print(f"   - Output: {context_metadata_path}")

        # ============================================================
        # STEP 3: Fixer - Error Correction
        # ============================================================
        print_step(3, 3, "Fixer - Error Correction (Claude API)")

        print("✏️  Correcting errors and generating SRT...")
        result = fix_subtitles(
            raw_subtitle_path=str(raw_subtitle_path),
            context_metadata_path=str(context_metadata_path),
            output_srt_path=output_srt
        )

        total = result['total_segments']
        corrected = result['corrected_segments']
        percentage = (corrected / total * 100) if total > 0 else 0

        print(f"✅ Success!")
        print(f"   - Total segments: {total}")
        print(f"   - Corrected: {corrected} ({percentage:.1f}%)")
        print(f"   - Output: {result['output_srt']}")

        # ============================================================
        # Cleanup
        # ============================================================
        if not keep_temp:
            print(f"\n🧹 Cleaning up temporary files...")
            try:
                raw_subtitle_path.unlink()
                context_metadata_path.unlink()
                print(f"   ✅ Temporary files deleted")
            except Exception as e:
                print(f"   ⚠️  Failed to delete temp files: {e}")
        else:
            print(f"\n📦 Temporary files kept:")
            print(f"   - {raw_subtitle_path}")
            print(f"   - {context_metadata_path}")

        # ============================================================
        # Final Summary
        # ============================================================
        print(f"\n{'='*60}")
        print(f"  🎉 Pipeline Complete!")
        print(f"{'='*60}\n")

        print(f"📊 Summary:")
        print(f"   Input:  {input_path}")
        print(f"   Output: {result['output_srt']}")
        print(f"   Segments: {total} ({corrected} corrected)")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Topic: {metadata.get('topic', 'N/A')}")

        print(f"\n📄 Next steps:")
        print(f"   1. Review the subtitle file: {result['output_srt']}")
        print(f"   2. Apply subtitles to your video")
        print(f"   3. Enjoy your perfectly subtitled video! 🎬")

        return True

    except Exception as e:
        logging.exception("Pipeline failed with error")
        print(f"\n❌ Pipeline failed: {e}")
        return False


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="YouTube Subtitle Generation and Correction System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (auto-detect output path)
  python main.py -i data/input/video.mp4

  # Specify output path
  python main.py -i video.mp4 -o subtitles/video.srt

  # English video with verbose logging
  python main.py -i video.mp4 -l en -v

  # Keep temporary files for debugging
  python main.py -i video.mp4 --keep-temp

For more information, see: https://github.com/your-repo/README.md
        """
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input video file (MP4, AVI, MOV, etc.)"
    )

    parser.add_argument(
        "-o", "--output",
        help="Output SRT file path (default: auto-generated in data/output/)"
    )

    parser.add_argument(
        "-l", "--language",
        default="ko",
        help="Language code (default: ko). Examples: en, ja, zh, es"
    )

    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files (raw subtitle and context metadata)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)

    # Print banner
    print_banner()

    # Check API keys
    if not check_api_keys():
        sys.exit(1)

    # Run pipeline
    success = run_pipeline(
        input_video=args.input,
        output_srt=args.output,
        language=args.language,
        keep_temp=args.keep_temp,
        verbose=args.verbose
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

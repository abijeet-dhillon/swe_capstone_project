"""
chronological_skills.py
---
Generates a chronological timeline of detected skills and media-based
metadata across all supported analyzers (code, text, video).

Integrates outputs from multiple analyzers, orders them by file
modification time, filters optionally by date, and exports results
to JSON, CSV, and plain text.

Usage (uncomment demo section at bottom):
    docker compose run --rm backend python3 -m src.analyze.chronological_skills
"""

import numpy as np
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Analyzer Imports
from src.analyze.code_analyzer import CodeAnalyzer
from src.analyze.text_analyzer import TextAnalyzer
from src.analyze.video_analyzer import VideoAnalyzer

# Optional image processor (requires zbar system library)
try:
    from src.image_processor import ImageProcessor
    IMAGE_PROCESSOR_AVAILABLE = True
except ImportError:
    ImageProcessor = None
    IMAGE_PROCESSOR_AVAILABLE = False

# Core Class
class ChronologicalSkillList:
    """Combines multiple analyzers to build a unified skill timeline."""

    def __init__(self):
        self.code_analyzer = CodeAnalyzer()
        self.text_analyzer = TextAnalyzer()
        self.video_analyzer = VideoAnalyzer()
        self.image_analyzer = ImageProcessor() if IMAGE_PROCESSOR_AVAILABLE else None

    def build_skill_timeline(
        self, directory_path: str, after_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Build a chronological list of discovered skills and media metadata.

        Args:
            directory_path: Root directory to analyze.
            after_date: Optional datetime filter. If provided, only include
                        files modified after this date.

        Returns:
            List of normalized event dictionaries.
        """
        timeline: List[Dict[str, Any]] = []

        # --- CODE ANALYSIS ---
        print("[+] Running Code Analyzer...")
        try:
            code_results = self.code_analyzer.analyze_directory(directory_path)
            for r in code_results:
                fp = Path(r.file_path)
                ts = datetime.fromtimestamp(fp.stat().st_mtime)
                if after_date and ts < after_date:
                    continue
                timeline.append({
                    "file": str(fp),
                    "timestamp": ts,
                    "category": "code",
                    "skills": sorted(r.skills),
                    "metadata": {
                        "language": r.language,
                        "frameworks": r.frameworks
                    }
                })
        except Exception as e:
            print(f"[warn] Code analysis failed: {e}")

        # --- TEXT ANALYSIS ---
        print("[+] Running Text Analyzer...")
        try:
            text_files = [
                f for f in Path(directory_path).rglob("*")
                if f.suffix.lower() in {".txt", ".pdf", ".docx"}
            ]
            for f in text_files:
                ts = datetime.fromtimestamp(f.stat().st_mtime)
                if after_date and ts < after_date:
                    continue
                try:
                    metrics = self.text_analyzer.analyze_file(str(f))
                    top_keywords = [k for k, _ in metrics.top_keywords[:10]]
                    timeline.append({
                        "file": str(f),
                        "timestamp": ts,
                        "category": "text",
                        "skills": ["writing"],
                        "metadata": {
                            "word_count": metrics.word_count,
                            "lexical_diversity": metrics.lexical_diversity,
                            "avg_word_length": metrics.avg_word_length,
                        }
                    })
                except Exception as inner_e:
                    print(f"[warn] Skipping text file {f}: {inner_e}")
        except Exception as e:
            print(f"[warn] Text analysis failed: {e}")

        # --- VIDEO ANALYSIS ---
        print("[+] Running Video Analyzer...")
        try:
            video_files = [
                f for f in Path(directory_path).rglob("*")
                if f.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".wmv"}
            ]
            for f in video_files:
                ts = datetime.fromtimestamp(f.stat().st_mtime)
                if after_date and ts < after_date:
                    continue
                try:
                    vres = self.video_analyzer.analyze_file(f)
                    if vres:
                        timeline.append({
                            "file": str(f),
                            "timestamp": ts,
                            "category": "video",
                            "skills": ["videography"],
                            "metadata": vres.to_dict(),
                        })
                except Exception as inner_e:
                    print(f"[warn] Skipping video {f}: {inner_e}")
        except Exception as e:
            print(f"[warn] Video analysis failed: {e}")

        # --- IMAGE ANALYSIS ---
        if self.image_analyzer:
            print("[+] Running Image Analyzer...")
            try:
                image_files = [
                    f for f in Path(directory_path).rglob("*")
                    if f.suffix.lower() in {".png", ".jpg", ".jpeg"}
                ]
                for f in image_files:
                    ts = datetime.fromtimestamp(f.stat().st_mtime)
                    if after_date and ts < after_date:
                        continue
                    try:
                        result = self.image_analyzer.analyze_image(str(f))
                        timeline.append({
                            "file": str(f),
                            "timestamp": ts,
                            "category": "image",
                            "skills": ["artistry"], 
                            "metadata": result,
                        })
                    except Exception as inner_e:
                        print(f"[warn] Skipping image {f}: {inner_e}")
            except Exception as e:
                print(f"[warn] Image analysis failed: {e}")
        else:
            print("[+] Image Analyzer skipped (zbar library not available)")

        timeline.sort(key=lambda e: e["timestamp"])
        return timeline

    def export_results(
        self, events: List[Dict[str, Any]], output_dir: str = "src/analyze/skills_output"
    ):
        """Export timeline data to JSON, CSV, and plain text formats."""
        Path(output_dir).mkdir(exist_ok=True)

        # JSON
        json_path = Path(output_dir) / "chronological_skills.json"
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump([
                {
                    **e,
                    "timestamp": e["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "metadata": make_json_serializable(e["metadata"])
                } for e in events
            ], jf, indent=2)
        print(f"[✓] JSON exported: {json_path}")

        # CSV
        csv_path = Path(output_dir) / "chronological_skills.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as cf:
            writer = csv.writer(cf)
            writer.writerow(["timestamp", "category", "file", "skills"])
            for e in events:
                writer.writerow([
                    e["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    e["category"],
                    e["file"],
                    ", ".join(e["skills"]),
                ])
        print(f"[✓] CSV exported: {csv_path}")

        # TXT summary
        txt_path = Path(output_dir) / "chronological_skills.txt"
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("=== Skill & Media Timeline ===\n\n")
            for e in events:
                tf.write(f"[{e['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] "
                         f"({e['category'].upper()}) {e['file']}\n")
                tf.write(f"  Skills: {', '.join(e['skills'])}\n\n")
        print(f"[✓] TXT exported: {txt_path}")

        return {
            "json": str(json_path),
            "csv": str(csv_path),
            "txt": str(txt_path)
        }
    
def make_json_serializable(obj):
    """Recursively convert NumPy types to Python native types."""
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj
    
# Command-Line Entrypoint
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description="Generate chronological timeline of skills from directory analysis"
    )
    parser.add_argument(
        "directory",
        help="Directory path to analyze"
    )
    parser.add_argument(
        "--output-dir",
        default="src/analyze/skills_output",
        help="Output directory for results (default: src/analyze/skills_output)"
    )
    parser.add_argument(
        "--after-date",
        help="Only include files modified after this date (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv", "txt", "all"],
        default="all",
        help="Output format (default: all)"
    )
    parser.add_argument(
        "--no-print",
        action="store_true",
        help="Don't print results to stdout (only export to files)"
    )
    
    args = parser.parse_args()
    
    # Parse after_date if provided
    after_date = None
    if args.after_date:
        try:
            after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format '{args.after_date}'. Use YYYY-MM-DD format.")
            sys.exit(1)
    
    # Check if directory exists
    directory_path = Path(args.directory)
    if not directory_path.exists():
        print(f"Error: Directory not found: {args.directory}")
        sys.exit(1)
    
    # Build timeline
    analyzer = ChronologicalSkillList()
    events = analyzer.build_skill_timeline(str(directory_path), after_date=after_date)
    
    if not events:
        print(f"\n⚠️  No events found in directory: {args.directory}")
        print("   Make sure the directory contains code, text, video, or image files.")
        sys.exit(0)
    
    print(f"\n[✓] Found {len(events)} event(s) in timeline")
    
    # Print to stdout by default (unless --no-print is used)
    if not args.no_print:
        print("\n" + "=" * 70)
        print("CHRONOLOGICAL SKILLS TIMELINE")
        print("=" * 70)
        for e in events:
            print(f"\n[{e['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}] ({e['category'].upper()})")
            print(f"  File: {e['file']}")
            print(f"  Skills: {', '.join(e['skills'])}")
            if e.get('metadata'):
                metadata = make_json_serializable(e['metadata'])
                # Format metadata nicely based on category
                if e['category'] == 'code':
                    print(f"  Language: {metadata.get('language', 'N/A')}")
                    if metadata.get('frameworks'):
                        print(f"  Frameworks: {', '.join(metadata['frameworks'])}")
                elif e['category'] == 'text':
                    print(f"  Word Count: {metadata.get('word_count', 'N/A')}")
                    print(f"  Lexical Diversity: {metadata.get('lexical_diversity', 'N/A'):.2f}")
                elif e['category'] == 'video':
                    print(f"  Duration: {metadata.get('duration_seconds', 'N/A')}s")
                    print(f"  Resolution: {metadata.get('resolution', 'N/A')}")
                    print(f"  Frame Rate: {metadata.get('frame_rate', 'N/A')} fps")
                    if metadata.get('has_audio'):
                        print(f"  Audio: Yes")
                elif e['category'] == 'image':
                    # Image metadata can vary, show key fields
                    for key, value in list(metadata.items())[:5]:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
                else:
                    # Fallback: show all metadata
                    for key, value in list(metadata.items())[:5]:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Export results
    if args.format in ["all", "json", "csv", "txt"]:
        export_paths = analyzer.export_results(events, output_dir=args.output_dir)
        
        if args.format != "all":
            # Only show the requested format
            format_map = {"json": "json", "csv": "csv", "txt": "txt"}
            print(f"\n[✓] Exported {args.format.upper()}: {export_paths[format_map[args.format]]}")
        else:
            print(f"\n[✓] Exported all formats to: {args.output_dir}")
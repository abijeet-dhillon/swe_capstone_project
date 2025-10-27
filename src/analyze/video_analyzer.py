import os
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from moviepy.editor import VideoFileClip


# ---------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------
@dataclass
class VideoAnalysisResult:
    """Represents metadata and analysis result for a single video file."""
    file_path: str
    duration_seconds: float
    resolution: str
    frame_rate: float
    total_frames: int
    has_audio: bool
    file_type: str
    format: str

    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON export."""
        return {
            "file_path": self.file_path,
            "duration_seconds": self.duration_seconds,
            "resolution": self.resolution,
            "frame_rate": self.frame_rate,
            "total_frames": self.total_frames,
            "has_audio": self.has_audio,
            "file_type": self.file_type,
            "format": self.format
        }


@dataclass
class VideoCollectionMetrics:
    """Aggregated metrics across multiple video files."""
    total_videos: int
    total_duration: float
    average_fps: float
    resolutions: List[str]
    formats: List[str]
    audio_videos: int
    video_only_files: int

    def to_dict(self) -> Dict:
        """Convert metrics summary to dictionary."""
        return {
            "total_videos": self.total_videos,
            "total_duration": self.total_duration,
            "average_fps": self.average_fps,
            "resolutions": self.resolutions,
            "formats": self.formats,
            "audio_videos": self.audio_videos,
            "video_only_files": self.video_only_files
        }


# ---------------------------------------------------------------------
# Video Analyzer
# ---------------------------------------------------------------------
class VideoAnalyzer:
    """Analyze video files and compute collection-level metrics."""

    SUPPORTED_FORMATS = {'.mp4', '.mov', '.avi', '.mkv', '.wmv'}

    def __init__(self):
        """Initialize analyzer with default config."""
        self.skip_dirs = {'.git', '__pycache__', 'temp', 'build', 'dist', 'node_modules'}

    # -----------------------------------------------------------------
    # Core: Analyze Single File
    # -----------------------------------------------------------------
    def analyze_file(self, file_path: Union[str, Path]) -> Optional[VideoAnalysisResult]:
        """Analyze a single video file and return metadata."""
        file_path = Path(file_path)

        # Skip invalid files
        if not file_path.exists() or file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            return None

        try:
            with VideoFileClip(str(file_path)) as clip:
                duration = clip.duration or 0.0
                fps = clip.fps or 0.0
                width, height = getattr(clip, "w", 0), getattr(clip, "h", 0)
                has_audio = clip.audio is not None

                total_frames = int(duration * fps) if duration and fps else 0
                resolution = f"{width}x{height}" if width and height else "unknown"

                file_type = "video-with-audio" if has_audio else "video-only"

                return VideoAnalysisResult(
                    file_path=str(file_path.absolute()),
                    duration_seconds=duration,
                    resolution=resolution,
                    frame_rate=fps,
                    total_frames=total_frames,
                    has_audio=has_audio,
                    file_type=file_type,
                    format=file_path.suffix.lstrip('.').lower()
                )

        except Exception as e:
            print(f"[WARN] Skipping file {file_path}: {e}")
            return None

    # -----------------------------------------------------------------
    # Core: Analyze Directory
    # -----------------------------------------------------------------
    def analyze_directory(self, directory_path: Union[str, Path]) -> List[VideoAnalysisResult]:
        """Recursively analyze all supported videos in a directory."""
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        results = []

        for file_path in directory_path.rglob('*'):
            if self._should_skip_file(file_path):
                continue

            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                result = self.analyze_file(file_path)
                if result:
                    results.append(result)

        return results

    # -----------------------------------------------------------------
    # Metrics Aggregation
    # -----------------------------------------------------------------
    def calculate_collection_metrics(self, results: List[VideoAnalysisResult]) -> VideoCollectionMetrics:
        """Aggregate statistics from a collection of analyzed videos."""
        if not results:
            return VideoCollectionMetrics(0, 0.0, 0.0, [], [], 0, 0)

        total_videos = len(results)
        total_duration = sum(r.duration_seconds for r in results)
        avg_fps = sum(r.frame_rate for r in results) / total_videos if total_videos else 0.0
        resolutions = list({r.resolution for r in results})
        formats = list({r.format for r in results})
        audio_videos = sum(1 for r in results if r.has_audio)
        video_only_files = sum(1 for r in results if not r.has_audio)

        return VideoCollectionMetrics(
            total_videos=total_videos,
            total_duration=round(total_duration, 2),
            average_fps=round(avg_fps, 2),
            resolutions=sorted(resolutions),
            formats=sorted(formats),
            audio_videos=audio_videos,
            video_only_files=video_only_files
        )

    # -----------------------------------------------------------------
    # Helper: Skip logic
    # -----------------------------------------------------------------
    def _should_skip_file(self, file_path: Path) -> bool:
        """Return True if a file should be skipped based on directory name."""
        return any(skip in file_path.parts for skip in self.skip_dirs)

    # -----------------------------------------------------------------
    # Helper: Export results
    # -----------------------------------------------------------------
    def save_to_json(self, results: List[VideoAnalysisResult], output_path: Union[str, Path]) -> None:
        """Save list of video results to a JSON file."""
        data = [r.to_dict() for r in results]
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"[INFO] Saved analysis results to {output_path}")

    # -----------------------------------------------------------------
    # Example CLI 
    # -----------------------------------------------------------------
    def run_example(self):  # pragma: no cover
        """Example method to demonstrate analyzer usage."""
        example_dir = Path(__file__).parent / "example_videos"
        results = self.analyze_directory(example_dir)
        metrics = self.calculate_collection_metrics(results)
        print(metrics.to_dict())

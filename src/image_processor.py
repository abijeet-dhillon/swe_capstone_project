"""
Image processor for analyzing PNG/JPEG files and extracting metrics.

This module provides functionality to analyze image files and extract various
metrics including resolution, aspect ratio, file format, file size, timestamps,
color analysis, EXIF metadata, and edit frequency.
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from collections import Counter

import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


class ImageProcessor:
    """Processes and analyzes image files to extract comprehensive metrics."""

    def __init__(self):
        """Initialize the image processor."""
        self.logger = logging.getLogger(__name__)
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}

    def is_supported_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            True if format is supported, False otherwise
        """
        return Path(file_path).suffix in self.supported_formats

    def get_resolution(self, image: Image.Image) -> Dict[str, int]:
        """
        Get image resolution (width × height).
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with width and height
        """
        width, height = image.size
        return {
            "width": width,
            "height": height,
            "total_pixels": width * height
        }

    def get_aspect_ratio(self, width: int, height: int) -> Dict[str, Any]:
        """
        Calculate aspect ratio.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Dictionary with aspect ratio information
        """
        if height == 0:
            return {"ratio": 0, "ratio_string": "0:0", "decimal": 0}
        
        ratio = width / height
        
        # Calculate GCD for simplified ratio
        from math import gcd
        divisor = gcd(width, height)
        simplified_width = width // divisor
        simplified_height = height // divisor
        
        return {
            "ratio": ratio,
            "ratio_string": f"{simplified_width}:{simplified_height}",
            "decimal": round(ratio, 2)
        }

    def get_file_format(self, image: Image.Image, file_path: str) -> Dict[str, str]:
        """
        Get file format information.
        
        Args:
            image: PIL Image object
            file_path: Path to the image file
            
        Returns:
            Dictionary with format information
        """
        return {
            "format": image.format or "UNKNOWN",
            "mode": image.mode,
            "extension": Path(file_path).suffix.lower()
        }

    def get_file_stats(self, file_path: str) -> Dict[str, Any]:
        """
        Get file size and timestamp information.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with file statistics
        """
        stats = os.stat(file_path)
        
        return {
            "size_bytes": stats.st_size,
            "size_kb": round(stats.st_size / 1024, 2),
            "size_mb": round(stats.st_size / (1024 * 1024), 2),
            "created_timestamp": stats.st_ctime,
            "created_datetime": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "modified_timestamp": stats.st_mtime,
            "modified_datetime": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "accessed_timestamp": stats.st_atime,
            "accessed_datetime": datetime.fromtimestamp(stats.st_atime).isoformat()
        }

    def get_average_brightness(self, image: Image.Image) -> Dict[str, float]:
        """
        Calculate average brightness of the image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with brightness information
        """
        # Convert to grayscale
        grayscale = image.convert('L')
        pixels = np.array(grayscale)
        
        avg_brightness = np.mean(pixels)
        
        return {
            "average_brightness": round(float(avg_brightness), 2),
            "brightness_percentage": round(float(avg_brightness) / 255 * 100, 2),
            "min_brightness": int(np.min(pixels)),
            "max_brightness": int(np.max(pixels))
        }

    def get_average_color(self, image: Image.Image) -> Dict[str, Any]:
        """
        Calculate average color values.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with average color information
        """
        # Convert to RGB if not already
        rgb_image = image.convert('RGB')
        pixels = np.array(rgb_image)
        
        # Calculate average for each channel
        avg_r = np.mean(pixels[:, :, 0])
        avg_g = np.mean(pixels[:, :, 1])
        avg_b = np.mean(pixels[:, :, 2])
        
        return {
            "average_rgb": {
                "r": round(float(avg_r), 2),
                "g": round(float(avg_g), 2),
                "b": round(float(avg_b), 2)
            },
            "average_hex": f"#{int(avg_r):02x}{int(avg_g):02x}{int(avg_b):02x}"
        }

    def get_dominant_color(self, image: Image.Image, num_colors: int = 5) -> Dict[str, Any]:
        """
        Find dominant colors in the image.
        
        Args:
            image: PIL Image object
            num_colors: Number of dominant colors to return
            
        Returns:
            Dictionary with dominant color information
        """
        # Resize image for faster processing
        small_image = image.convert('RGB').resize((150, 150))
        pixels = np.array(small_image)
        
        # Reshape to list of RGB values
        pixels_list = pixels.reshape(-1, 3)
        
        # Convert to tuples for counting
        pixel_tuples = [tuple(pixel) for pixel in pixels_list]
        
        # Count occurrences
        color_counts = Counter(pixel_tuples)
        most_common = color_counts.most_common(num_colors)
        
        dominant_colors = []
        for color, count in most_common:
            dominant_colors.append({
                "rgb": {"r": color[0], "g": color[1], "b": color[2]},
                "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
                "frequency": count,
                "percentage": round(count / len(pixel_tuples) * 100, 2)
            })
        
        return {
            "dominant_colors": dominant_colors,
            "most_dominant": dominant_colors[0] if dominant_colors else None
        }

    def get_exif_metadata(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract EXIF metadata from the image.
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with EXIF metadata
        """
        exif_data = {}
        
        try:
            exif = image._getexif()
            
            if exif is None:
                return {"has_exif": False, "data": {}}
            
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                
                # Handle GPS data separately
                if tag == "GPSInfo":
                    gps_data = {}
                    for gps_tag_id in value:
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_data[gps_tag] = value[gps_tag_id]
                    exif_data["GPSInfo"] = gps_data
                else:
                    # Convert bytes to string for readability
                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except:
                            value = str(value)
                    exif_data[tag] = value
            
            return {
                "has_exif": True,
                "data": exif_data,
                "camera_make": exif_data.get("Make", "Unknown"),
                "camera_model": exif_data.get("Model", "Unknown"),
                "datetime_original": exif_data.get("DateTimeOriginal", "Unknown"),
                "has_gps": "GPSInfo" in exif_data
            }
            
        except AttributeError:
            return {"has_exif": False, "data": {}}
        except Exception as e:
            self.logger.warning(f"Error extracting EXIF data: {e}")
            return {"has_exif": False, "error": str(e), "data": {}}

    def calculate_edit_frequency(self, file_path: str) -> Dict[str, Any]:
        """
        Calculate frequency of edits based on timestamps.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary with edit frequency information
        """
        stats = os.stat(file_path)
        
        created = datetime.fromtimestamp(stats.st_ctime)
        modified = datetime.fromtimestamp(stats.st_mtime)
        
        time_diff = modified - created
        days_since_creation = time_diff.total_seconds() / 86400
        
        # Check if file has been modified since creation
        was_edited = abs(stats.st_mtime - stats.st_ctime) > 1  # 1 second tolerance
        
        return {
            "was_edited": was_edited,
            "created": created.isoformat(),
            "last_modified": modified.isoformat(),
            "days_since_creation": round(days_since_creation, 2),
            "time_between_create_modify_seconds": round(time_diff.total_seconds(), 2)
        }

    def analyze_image(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of an image file.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            Dictionary containing all metrics
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        if not self.is_supported_format(file_path):
            raise ValueError(f"Unsupported file format: {Path(file_path).suffix}")
        
        try:
            # Open image
            with Image.open(file_path) as image:
                # Get resolution
                resolution = self.get_resolution(image)
                
                # Get aspect ratio
                aspect_ratio = self.get_aspect_ratio(resolution["width"], resolution["height"])
                
                # Get file format
                file_format = self.get_file_format(image, file_path)
                
                # Get file stats
                file_stats = self.get_file_stats(file_path)
                
                # Get brightness
                brightness = self.get_average_brightness(image)
                
                # Get average color
                avg_color = self.get_average_color(image)
                
                # Get dominant color
                dominant_color = self.get_dominant_color(image)
                
                # Get EXIF metadata
                exif = self.get_exif_metadata(image)
                
                # Calculate edit frequency
                edit_frequency = self.calculate_edit_frequency(file_path)
                
                return {
                    "file_path": str(Path(file_path).resolve()),
                    "file_name": Path(file_path).name,
                    "resolution": resolution,
                    "aspect_ratio": aspect_ratio,
                    "format": file_format,
                    "file_stats": file_stats,
                    "brightness": brightness,
                    "average_color": avg_color,
                    "dominant_color": dominant_color,
                    "exif_metadata": exif,
                    "edit_frequency": edit_frequency,
                    "analysis_timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error analyzing image {file_path}: {e}")
            raise

    def batch_analyze(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Analyze multiple images at once.
        
        Args:
            file_paths: List of paths to image files
            
        Returns:
            List of analysis results
        """
        results = []
        
        for file_path in file_paths:
            try:
                result = self.analyze_image(file_path)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to analyze {file_path}: {e}")
                results.append({
                    "file_path": file_path,
                    "error": str(e),
                    "analysis_timestamp": datetime.now().isoformat()
                })
        
        return results

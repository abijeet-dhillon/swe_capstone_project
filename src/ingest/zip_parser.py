"""
Zip file parsing functionality.
"""

import zipfile
import hashlib
from pathlib import Path
from typing import Union

from .models import ZipIndex, ZipEntry


class ZipParseError(Exception):
    """Raised when zip file parsing fails."""
    pass


def parse_zip(zip_path: Union[str, Path]) -> ZipIndex:
    """Parse a zip file and return structured metadata."""
    zip_path = Path(zip_path)
    
    # Validate file exists
    if not zip_path.exists():
        raise ZipParseError(f"File not found: {zip_path}")
    
    # Validate file is readable
    if not zip_path.is_file():
        raise ZipParseError(f"Path is not a file: {zip_path}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Validate zip file integrity
            if zf.testzip() is not None:
                raise ZipParseError(f"Corrupt zip file: {zip_path}")
            
            files = []
            total_uncompressed = 0
            total_compressed = 0
            
            for info in zf.infolist():
                # Skip directories
                if info.is_dir():
                    continue
                
                # Basic path normalization
                rel_path = info.filename.replace('\\', '/')
                if rel_path.startswith('/'):
                    rel_path = rel_path[1:]
                
                # Calculate depth
                depth = len(Path(rel_path).parts) - 1
                
                # Extract file extension
                ext = Path(rel_path).suffix.lower()
                if ext.startswith('.'):
                    ext = ext[1:]
                
                # Read file content for hash
                with zf.open(info) as file_obj:
                    content = file_obj.read()
                
                # Compute SHA256 hash
                sha256_hash = hashlib.sha256(content).hexdigest()
                
                # Simple text detection
                is_text = _is_text_content(content)
                
                # Determine if compressed
                is_compressed = info.compress_type != zipfile.ZIP_STORED
                
                # Create file entry
                entry = ZipEntry(
                    rel_path=rel_path,
                    size=info.file_size,
                    compressed_size=info.compress_size,
                    is_compressed=is_compressed,
                    sha256=sha256_hash,
                    depth=depth,
                    ext=ext,
                    is_text_guess=is_text
                )
                
                files.append(entry)
                total_uncompressed += info.file_size
                total_compressed += info.compress_size
            
            return ZipIndex(
                root_name=zip_path.name,
                file_count=len(files),
                total_uncompressed_bytes=total_uncompressed,
                total_compressed_bytes=total_compressed,
                files=files
            )
            
    except zipfile.BadZipFile:
        raise ZipParseError(f"Not a valid zip file: {zip_path}")
    except Exception as e:
        raise ZipParseError(f"Unexpected error parsing zip file {zip_path}: {e}")


def _is_text_content(content: bytes) -> bool:
    """Simple text detection heuristic."""
    if not content:
        return True
    
    try:
        content.decode('utf-8', errors='ignore')
        return True
    except Exception:
        return False
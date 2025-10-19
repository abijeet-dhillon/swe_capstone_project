import pytest
import zipfile
from pathlib import Path

from src.ingest.zip_parser import parse_zip, ZipParseError
from src.ingest.models import ZipIndex, ZipEntry


class TestZipParser:
    def test_parses_simple_zip(self, tmp_path):
        """Test parsing a zip with a single text file."""
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "Hello World")
        
        result = parse_zip(zip_path)
        
        assert isinstance(result, ZipIndex)
        assert result.root_name == "test.zip"
        assert result.file_count == 1
        assert len(result.files) == 1
        
        file_entry = result.files[0]
        assert file_entry.rel_path == "readme.txt"
        assert file_entry.ext == "txt"
        assert file_entry.depth == 0
        assert len(file_entry.sha256) == 64

    def test_handles_empty_zip(self, tmp_path):
        """Test parsing an empty zip file."""
        zip_path = tmp_path / "empty.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            pass  # Create empty zip
        
        result = parse_zip(zip_path)
        
        assert result.file_count == 0
        assert result.files == []

    def test_raises_error_for_invalid_zip(self, tmp_path):
        """Test that invalid files raise ZipParseError."""
        zip_path = tmp_path / "not_a_zip.txt"
        zip_path.write_text("This is not a zip file")
        
        with pytest.raises(ZipParseError):
            parse_zip(zip_path)

    def test_raises_error_for_missing_file(self, tmp_path):
        """Test that missing files raise ZipParseError."""
        zip_path = tmp_path / "nonexistent.zip"
        
        with pytest.raises(ZipParseError):
            parse_zip(zip_path)

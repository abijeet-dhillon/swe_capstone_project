"""
Document Parser Module
Extracts text content from various document formats (docx, pptx).
"""
from pathlib import Path
from typing import Dict, Any
from docx import Document
from pptx import Presentation


class DocumentParser:
    """Parser for extracting text from various document formats."""
    
    @staticmethod
    def parse_docx(file_path: str) -> Dict[str, Any]:
        """
        Extract text content from a Word document (.docx).
        
        Args:
            file_path: Path to the .docx file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.docx':
            raise ValueError(f"Expected .docx file, got {file_path.suffix}")
        
        try:
            doc = Document(file_path)
            
            # Extract all text from paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            full_text = "\n\n".join(paragraphs)
            
            # Extract text from tables
            table_text = []
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        table_text.append(row_text)
            
            if table_text:
                full_text += "\n\nTables:\n" + "\n".join(table_text)
            
            return {
                "file_name": file_path.name,
                "file_type": "docx",
                "text": full_text,
                "paragraph_count": len(paragraphs),
                "table_count": len(doc.tables),
                "word_count": len(full_text.split())
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX file: {str(e)}")
    
    @staticmethod
    def parse_pptx(file_path: str) -> Dict[str, Any]:
        """
        Extract text content from a PowerPoint presentation (.pptx).
        
        Args:
            file_path: Path to the .pptx file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pptx':
            raise ValueError(f"Expected .pptx file, got {file_path.suffix}")
        
        try:
            prs = Presentation(file_path)
            
            slides_text = []
            
            for slide_num, slide in enumerate(prs.slides, start=1):
                slide_content = []
                
                # Extract text from all shapes
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_content.append(shape.text.strip())
                
                if slide_content:
                    slide_text = f"Slide {slide_num}:\n" + "\n".join(slide_content)
                    slides_text.append(slide_text)
            
            full_text = "\n\n".join(slides_text)
            
            return {
                "file_name": file_path.name,
                "file_type": "pptx",
                "text": full_text,
                "slide_count": len(prs.slides),
                "word_count": len(full_text.split())
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse PPTX file: {str(e)}")
    
    @staticmethod
    def parse_file(file_path: str) -> Dict[str, Any]:
        """
        Parse a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        
        if suffix == '.docx':
            return DocumentParser.parse_docx(str(file_path))
        elif suffix == '.pptx':
            return DocumentParser.parse_pptx(str(file_path))
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported formats: .docx, .pptx")


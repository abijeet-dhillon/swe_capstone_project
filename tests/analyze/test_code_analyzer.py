"""
Unit tests for Code Analyzer module
Tests local analysis of code files for language detection, framework identification,
contribution metrics, and skill extraction.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from analyze.code_analyzer import CodeAnalyzer, AnalysisResult, ContributionMetrics


class TestCodeAnalyzer:
    """Test suite for CodeAnalyzer class"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return CodeAnalyzer()
    
    @pytest.fixture
    def sample_python_code(self):
        """Sample Python code for testing"""
        return '''
import fastapi
from sqlalchemy import Column, Integer, String
import pytest

class User:
    def __init__(self, name):
        self.name = name
    
    def get_profile(self):
        return {"name": self.name}

def test_user_creation():
    user = User("test")
    assert user.name == "test"
'''
    
    @pytest.fixture
    def sample_js_code(self):
        """Sample JavaScript code for testing"""
        return '''
import React from 'react';
import { useState, useEffect } from 'react';

function App() {
    const [count, setCount] = useState(0);
    
    useEffect(() => {
        document.title = `Count: ${count}`;
    }, [count]);
    
    return (
        <div>
            <button onClick={() => setCount(count + 1)}>
                Count: {count}
            </button>
        </div>
    );
}

export default App;
'''
    
    def test_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer is not None
        assert hasattr(analyzer, 'analyze_file')
        assert hasattr(analyzer, 'analyze_directory')
    
    def test_detect_language_python(self, analyzer, sample_python_code):
        """Test Python language detection"""
        result = analyzer.detect_language(sample_python_code, "app.py")
        assert result == "python"
    
    def test_detect_language_javascript(self, analyzer, sample_js_code):
        """Test JavaScript language detection"""
        result = analyzer.detect_language(sample_js_code, "App.jsx")
        assert result == "javascript"
    
    def test_detect_frameworks_python(self, analyzer, sample_python_code):
        """Test Python framework detection"""
        frameworks = analyzer.detect_frameworks(sample_python_code, "python")
        assert "fastapi" in frameworks
        assert "sqlalchemy" in frameworks
        assert "pytest" in frameworks
    
    def test_detect_frameworks_javascript(self, analyzer, sample_js_code):
        """Test JavaScript framework detection"""
        frameworks = analyzer.detect_frameworks(sample_js_code, "javascript")
        assert "react" in frameworks
    
    def test_extract_skills_python(self, analyzer, sample_python_code):
        """Test skill extraction from Python code"""
        skills = analyzer.extract_skills(sample_python_code, "python")
        expected_skills = ["python", "fastapi", "sqlalchemy", "pytest", "object-oriented-programming"]
        
        for skill in expected_skills:
            assert skill in skills
    
    def test_extract_skills_javascript(self, analyzer, sample_js_code):
        """Test skill extraction from JavaScript code"""
        skills = analyzer.extract_skills(sample_js_code, "javascript")
        expected_skills = ["javascript", "react", "hooks", "frontend-development"]
        
        for skill in expected_skills:
            assert skill in skills
    
    def test_analyze_file_success(self, analyzer, sample_python_code):
        """Test successful file analysis"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_python_code)
            temp_path = f.name
        
        try:
            result = analyzer.analyze_file(temp_path)
            
            assert isinstance(result, AnalysisResult)
            assert result.language == "python"
            assert "fastapi" in result.frameworks
            assert "python" in result.skills
            assert result.file_path == temp_path
            assert result.lines_of_code > 0
        finally:
            os.unlink(temp_path)
    
    def test_analyze_file_nonexistent(self, analyzer):
        """Test analysis of non-existent file"""
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file("/nonexistent/file.py")
    
    def test_analyze_file_empty(self, analyzer):
        """Test analysis of empty file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            temp_path = f.name
        
        try:
            result = analyzer.analyze_file(temp_path)
            # Empty .py file should still be detected as Python by extension
            assert result.language == "python"
            assert len(result.frameworks) == 0
            # Language is added as a skill even for empty files
            assert result.skills == ["python"]
        finally:
            os.unlink(temp_path)
    
    def test_analyze_directory_success(self, analyzer):
        """Test directory analysis"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            python_file = Path(temp_dir) / "app.py"
            js_file = Path(temp_dir) / "component.jsx"
            
            python_file.write_text("import fastapi\nprint('hello')")
            js_file.write_text("import React from 'react'")
            
            results = analyzer.analyze_directory(temp_dir)
            
            assert len(results) == 2
            assert any(r.language == "python" for r in results)
            assert any(r.language == "javascript" for r in results)
    
    def test_analyze_directory_empty(self, analyzer):
        """Test analysis of empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            results = analyzer.analyze_directory(temp_dir)
            assert len(results) == 0
    
    def test_contribution_metrics_calculation(self, analyzer):
        """Test contribution metrics calculation"""
        results = [
            AnalysisResult(
                file_path="app.py",
                language="python",
                frameworks=["fastapi"],
                skills=["python", "fastapi"],
                lines_of_code=100,
                file_type="code"
            ),
            AnalysisResult(
                file_path="test_app.py",
                language="python", 
                frameworks=["pytest"],
                skills=["python", "testing"],
                lines_of_code=50,
                file_type="test"
            ),
            AnalysisResult(
                file_path="README.md",
                language="markdown",
                frameworks=[],
                skills=["documentation"],
                lines_of_code=20,
                file_type="documentation"
            )
        ]
        
        metrics = analyzer.calculate_contribution_metrics(results)
        
        assert isinstance(metrics, ContributionMetrics)
        assert metrics.total_files == 3
        assert metrics.total_lines == 170
        assert set(metrics.languages) == {"python", "markdown"}
        assert metrics.code_files == 1
        assert metrics.test_files == 1
        assert metrics.documentation_files == 1
        assert "fastapi" in metrics.frameworks
        assert "python" in metrics.skills
    
    def test_skill_categorization(self, analyzer):
        """Test skill categorization"""
        skills = ["python", "fastapi", "react", "sqlalchemy", "pytest", "javascript"]
        categorized = analyzer.categorize_skills(skills)
        
        assert "programming-languages" in categorized
        assert "web-frameworks" in categorized
        assert "testing" in categorized
        assert "databases" in categorized
    
    def test_file_type_detection(self, analyzer):
        """Test file type detection based on content and path"""
        # Test file
        test_code = "def test_something():\n    assert True"
        file_type = analyzer.detect_file_type(test_code, "test_app.py")
        assert file_type == "test"
        
        # Documentation file
        doc_code = "# This is documentation\n## API Reference"
        file_type = analyzer.detect_file_type(doc_code, "README.md")
        assert file_type == "documentation"
        
        # Regular code file
        code = "def main():\n    print('hello')"
        file_type = analyzer.detect_file_type(code, "app.py")
        assert file_type == "code"
    
    def test_error_handling_invalid_file(self, analyzer):
        """Test error handling for invalid files"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("invalid python syntax {")
            temp_path = f.name
        
        try:
            # Should not raise exception, but handle gracefully
            result = analyzer.analyze_file(temp_path)
            assert result.language == "python"  # Should still detect as Python
            assert len(result.skills) >= 0  # Should not crash
        finally:
            os.unlink(temp_path)


class TestAnalysisResult:
    """Test suite for AnalysisResult data class"""
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult object creation"""
        result = AnalysisResult(
            file_path="/test/app.py",
            language="python",
            frameworks=["fastapi"],
            skills=["python", "web-development"],
            lines_of_code=100,
            file_type="code"
        )
        
        assert result.file_path == "/test/app.py"
        assert result.language == "python"
        assert result.frameworks == ["fastapi"]
        assert result.skills == ["python", "web-development"]
        assert result.lines_of_code == 100
        assert result.file_type == "code"
    
    def test_analysis_result_to_dict(self):
        """Test converting AnalysisResult to dictionary"""
        result = AnalysisResult(
            file_path="/test/app.py",
            language="python",
            frameworks=["fastapi"],
            skills=["python"],
            lines_of_code=100,
            file_type="code"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict["file_path"] == "/test/app.py"
        assert result_dict["language"] == "python"
        assert result_dict["frameworks"] == ["fastapi"]
        assert result_dict["skills"] == ["python"]
        assert result_dict["lines_of_code"] == 100
        assert result_dict["file_type"] == "code"


class TestContributionMetrics:
    """Test suite for ContributionMetrics data class"""
    
    def test_contribution_metrics_creation(self):
        """Test ContributionMetrics object creation"""
        metrics = ContributionMetrics(
            total_files=5,
            total_lines=500,
            languages=["python", "javascript"],
            frameworks=["fastapi", "react"],
            skills=["python", "javascript", "web-development"],
            code_files=3,
            test_files=1,
            documentation_files=1,
            project_duration_days=30
        )
        
        assert metrics.total_files == 5
        assert metrics.total_lines == 500
        assert metrics.languages == ["python", "javascript"]
        assert metrics.frameworks == ["fastapi", "react"]
        assert metrics.skills == ["python", "javascript", "web-development"]
        assert metrics.code_files == 3
        assert metrics.test_files == 1
        assert metrics.documentation_files == 1
        assert metrics.project_duration_days == 30
    
    def test_contribution_metrics_to_dict(self):
        """Test converting ContributionMetrics to dictionary"""
        metrics = ContributionMetrics(
            total_files=3,
            total_lines=300,
            languages=["python"],
            frameworks=["fastapi"],
            skills=["python"],
            code_files=2,
            test_files=1,
            documentation_files=0,
            project_duration_days=15
        )
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert metrics_dict["total_files"] == 3
        assert metrics_dict["total_lines"] == 300
        assert metrics_dict["languages"] == ["python"]
        assert metrics_dict["frameworks"] == ["fastapi"]
        assert metrics_dict["skills"] == ["python"]
        assert metrics_dict["code_files"] == 2
        assert metrics_dict["test_files"] == 1
        assert metrics_dict["documentation_files"] == 0
        assert metrics_dict["project_duration_days"] == 15


class TestCodeAnalyzerIntegration:
    """Integration tests for CodeAnalyzer"""
    
    def test_full_analysis_workflow(self):
        """Test complete analysis workflow"""
        analyzer = CodeAnalyzer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a small project structure
            app_file = Path(temp_dir) / "app.py"
            test_file = Path(temp_dir) / "test_app.py"
            readme_file = Path(temp_dir) / "README.md"
            
            app_file.write_text("""
import fastapi
from sqlalchemy import Column, Integer, String

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
""")
            
            test_file.write_text("""
import pytest
from app import app

def test_read_root():
    response = app.get("/")
    assert response.status_code == 200
""")
            
            readme_file.write_text("""
# My FastAPI Project

This is a simple FastAPI application.
""")
            
            # Analyze the directory
            results = analyzer.analyze_directory(temp_dir)
            
            # Should find Python files (README.md is not a code file)
            assert len(results) == 2
            
            # Check that we can calculate metrics
            metrics = analyzer.calculate_contribution_metrics(results)
            
            assert metrics.total_files == 2
            assert metrics.total_lines > 0
            assert "python" in metrics.languages
            assert "fastapi" in metrics.frameworks
            assert metrics.code_files >= 1
            assert metrics.test_files >= 1
            # README.md is not analyzed as it's not a code file

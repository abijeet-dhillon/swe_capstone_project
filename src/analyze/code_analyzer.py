import re
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    file_path: str
    language: str
    frameworks: List[str]
    skills: List[str]
    lines_of_code: int
    file_type: str
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'language': self.language,
            'frameworks': self.frameworks,
            'skills': self.skills,
            'lines_of_code': self.lines_of_code,
            'file_type': self.file_type
        }


@dataclass
class ContributionMetrics:
    total_files: int
    total_lines: int
    languages: List[str]
    frameworks: List[str]
    skills: List[str]
    code_files: int
    test_files: int
    
    def to_dict(self) -> Dict:
        return {
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'languages': self.languages,
            'frameworks': self.frameworks,
            'skills': self.skills,
            'code_files': self.code_files,
            'test_files': self.test_files
        }


class CodeAnalyzer:
    
    def __init__(self):
        self.frameworks = {
            'python': ['fastapi', 'django', 'flask', 'sqlalchemy', 'pytest', 'pandas', 'numpy'],
            'javascript': ['react', 'vue', 'angular', 'express', 'jest', 'node'],
            'java': ['spring', 'hibernate', 'junit', 'maven'],
            'cpp': ['boost', 'qt', 'opencv']
        }
    
    def detect_language(self, content: str, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        
        if ext == '.py':
            return 'python'
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            return 'javascript'
        elif ext == '.java':
            return 'java'
        elif ext in ['.cpp', '.cc', '.c', '.h', '.hpp']:
            return 'cpp'
        
        content_lower = content.lower()
        if 'import ' in content_lower and 'def ' in content_lower:
            return 'python'
        elif 'function' in content_lower and ('const ' in content_lower or 'let ' in content_lower):
            return 'javascript'
        elif 'public class' in content_lower and 'import ' in content_lower:
            return 'java'
        
        return 'unknown'
    
    def detect_frameworks(self, content: str, language: str) -> List[str]:
        if language not in self.frameworks:
            return []
        
        found = []
        content_lower = content.lower()
        
        for framework in self.frameworks[language]:
            if framework in content_lower:
                found.append(framework)
        
        return found
    
    def extract_skills(self, content: str, language: str) -> List[str]:
        skills = [language] if language != 'unknown' else []
        
        frameworks = self.detect_frameworks(content, language)
        skills.extend(frameworks)
        
        content_lower = content.lower()
        if language == 'python':
            if 'class ' in content:
                skills.append('object-oriented-programming')
            if 'async def' in content:
                skills.append('asynchronous-programming')
        elif language == 'javascript':
            if '=>' in content:
                skills.append('arrow-functions')
            if 'useState' in content or 'useEffect' in content:
                skills.append('react-hooks')
        
        return list(set(skills))  
    
    def detect_file_type(self, content: str, filename: str) -> str:
        filename_lower = filename.lower()
        
        if (filename_lower.startswith('test_') or 
            filename_lower.endswith('_test.py') or
            'test' in filename_lower and 'def test_' in content.lower()):
            return 'test'
        
        if (filename_lower.endswith('.md') or 
            filename_lower.endswith('.txt') or
            filename_lower in ['readme', 'changelog']):
            return 'documentation'
        
        return 'code'
    
    def analyze_file(self, file_path: Union[str, Path]) -> AnalysisResult:
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')
        
        language = self.detect_language(content, file_path.name)
        frameworks = self.detect_frameworks(content, language)
        skills = self.extract_skills(content, language)
        file_type = self.detect_file_type(content, file_path.name)
        
        lines = [line for line in content.split('\n') 
                if line.strip() and not line.strip().startswith('#')]
        lines_of_code = len(lines)
        
        return AnalysisResult(
            file_path=str(file_path),
            language=language,
            frameworks=frameworks,
            skills=skills,
            lines_of_code=lines_of_code,
            file_type=file_type
        )
    
    def analyze_directory(self, directory_path: Union[str, Path]) -> List[AnalysisResult]:
        directory_path = Path(directory_path)
        
        if not directory_path.exists() or not directory_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")
        
        results = []
        code_extensions = {'.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.cc', '.c', '.h'}
        
        for file_path in directory_path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in code_extensions and
                not self._should_skip_file(file_path)):
                
                try:
                    result = self.analyze_file(file_path)
                    results.append(result)
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
        
        return results
    
    def _should_skip_file(self, file_path: Path) -> bool:
        skip_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'build', 'dist'}
        return any(part in skip_dirs for part in file_path.parts)
    
    def calculate_contribution_metrics(self, results: List[AnalysisResult]) -> ContributionMetrics:
        if not results:
            return ContributionMetrics(0, 0, [], [], [], 0, 0)
        
        total_files = len(results)
        total_lines = sum(r.lines_of_code for r in results)
        
        languages = list(set(r.language for r in results if r.language != 'unknown'))
        frameworks = list(set(fw for r in results for fw in r.frameworks))
        skills = list(set(skill for r in results for skill in r.skills))
        
        code_files = sum(1 for r in results if r.file_type == 'code')
        test_files = sum(1 for r in results if r.file_type == 'test')
        
        return ContributionMetrics(
            total_files=total_files,
            total_lines=total_lines,
            languages=sorted(languages),
            frameworks=sorted(frameworks),
            skills=sorted(skills),
            code_files=code_files,
            test_files=test_files
        )
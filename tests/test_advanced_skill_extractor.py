"""Tests for Advanced Skill Extractor"""

import pytest
from pathlib import Path
from src.analyze.advanced_skill_extractor import (
    AdvancedSkillExtractor,
    DeepSkillAnalysis,
    SkillEvidence
)


@pytest.fixture
def extractor():
    return AdvancedSkillExtractor()


@pytest.fixture
def sample_code_with_caching():
    return '''
def get_data(self):
    if self._cache is None:
        self._cache = expensive_operation()
    return self._cache
'''


@pytest.fixture
def sample_code_with_set_optimization():
    return '''
def remove_duplicates(items):
    return list(set(items))
'''


@pytest.fixture
def sample_code_with_type_hints():
    return '''
def process(data: List[str], count: int) -> Dict[str, int]:
    return {"result": count}

def analyze(items: Optional[List[str]]) -> bool:
    return True
'''


@pytest.fixture
def sample_code_with_exception():
    return '''
class CustomError(Exception):
    pass

class ValidationError(Exception):
    pass
'''


def test_extractor_initialization(extractor):
    assert extractor is not None
    assert extractor.skill_patterns is not None


def test_detect_lazy_initialization(extractor, sample_code_with_caching, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_code_with_caching)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'lazy-initialization' in analysis.advanced_skills
    assert any(e.skill == 'lazy-initialization' for e in analysis.evidence)


def test_detect_set_optimization(extractor, sample_code_with_set_optimization, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_code_with_set_optimization)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'algorithmic-optimization' in analysis.advanced_skills
    assert analysis.complexity_insights.get('set_deduplication', 0) > 0


def test_detect_type_hints(extractor, sample_code_with_type_hints, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_code_with_type_hints)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'static-type-checking' in analysis.advanced_skills


def test_detect_custom_exceptions(extractor, sample_code_with_exception, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_code_with_exception)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'custom-exception-hierarchy' in analysis.design_patterns


def test_syntax_error_handling(extractor, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("def broken(:\n    pass")
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'syntax-error-detected' in analysis.basic_skills


def test_analyze_directory(extractor, tmp_path):
    (tmp_path / "file1.py").write_text("def test(): pass")
    (tmp_path / "file2.py").write_text("x = list(set([1,2,3]))")
    
    results = extractor.analyze_directory(tmp_path)
    
    assert len(results) == 2


def test_aggregate_skills(extractor, tmp_path):
    (tmp_path / "file1.py").write_text("x = list(set([1,2,3]))")
    (tmp_path / "file2.py").write_text("x = list(set([4,5,6]))")
    
    results = extractor.analyze_directory(tmp_path)
    aggregated = extractor.aggregate_skills(results)
    
    assert 'algorithmic-optimization' in aggregated['advanced_skills']
    assert aggregated['total_files_analyzed'] == 2


def test_evidence_structure(extractor, sample_code_with_caching, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text(sample_code_with_caching)
    
    analysis = extractor.analyze_file(test_file)
    
    if analysis.evidence:
        evidence = analysis.evidence[0]
        assert hasattr(evidence, 'skill')
        assert hasattr(evidence, 'evidence_type')
        assert hasattr(evidence, 'location')
        assert hasattr(evidence, 'reasoning')
        assert hasattr(evidence, 'confidence')
        assert 0.0 <= evidence.confidence <= 1.0


def test_dataclass_detection(extractor, tmp_path):
    code = '''
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int
'''
    test_file = tmp_path / "test.py"
    test_file.write_text(code)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'modern-python-features' in analysis.advanced_skills


def test_context_manager_detection(extractor, tmp_path):
    code = '''
with open('file.txt') as f:
    data = f.read()

with connection() as conn:
    conn.execute()
'''
    test_file = tmp_path / "test.py"
    test_file.write_text(code)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'resource-management' in analysis.advanced_skills


def test_comprehension_detection(extractor, tmp_path):
    code = '''
squares = [x**2 for x in range(10)]
evens = [x for x in range(10) if x % 2 == 0]
names = {p.name for p in people}
mapping = {k: v for k, v in items}
'''
    test_file = tmp_path / "test.py"
    test_file.write_text(code)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'pythonic-idioms' in analysis.advanced_skills


def test_graceful_degradation_detection(extractor, tmp_path):
    code = '''
try:
    result = risky_operation()
except Exception:
    result = fallback_value()
'''
    test_file = tmp_path / "test.py"
    test_file.write_text(code)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'graceful-degradation' in analysis.advanced_skills


def test_cryptographic_hashing_detection(extractor, tmp_path):
    code = '''
import hashlib

def hash_file(content):
    return hashlib.sha256(content).hexdigest()
'''
    test_file = tmp_path / "test.py"
    test_file.write_text(code)
    
    analysis = extractor.analyze_file(test_file)
    
    assert 'cryptographic-hashing' in analysis.advanced_skills

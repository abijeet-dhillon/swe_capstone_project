"""Advanced Skill Extractor - Local AST-based analysis"""

import ast
import re
from pathlib import Path
from typing import List, Dict, Set, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class SkillEvidence:
    skill: str
    evidence_type: str
    location: str
    reasoning: str
    confidence: float


@dataclass
class DeepSkillAnalysis:
    file_path: str
    basic_skills: List[str] = field(default_factory=list)
    advanced_skills: List[str] = field(default_factory=list)
    design_patterns: List[str] = field(default_factory=list)
    complexity_insights: Dict[str, Any] = field(default_factory=dict)
    evidence: List[SkillEvidence] = field(default_factory=list)


class AdvancedSkillExtractor:
    
    def __init__(self):
        self.skill_patterns = self._initialize_patterns()
        self.language_extensions = {
            '.py': 'python',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }
    
    def _detect_language(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        return self.language_extensions.get(ext, 'unknown')
    
    def _initialize_patterns(self) -> Dict[str, Any]:
        return {
            'caching': {
                'keywords': ['cache', 'memoize', 'cached', '_cached'],
                'patterns': [r'if.*is None:', r'@lru_cache', r'@cache']
            },
            'lazy_evaluation': {
                'keywords': ['lazy', '_lazy', 'deferred'],
                'patterns': [r'if.*is None:.*=', r'property.*return']
            },
            'set_optimization': {
                'keywords': ['set(', 'frozenset('],
                'patterns': [r'list\(set\(', r'set\([^\)]+\)']
            },
            'dependency_injection': {
                'keywords': ['inject', 'Optional[', 'Union['],
                'patterns': [r'def __init__\(self.*:.*\)']
            },
            'type_hints': {
                'keywords': ['List[', 'Dict[', 'Optional[', 'Union[', 'Set['],
                'patterns': [r'def.*\(.*:.*\)\s*->', r':\s*List\[', r':\s*Dict\[']
            },
            'context_managers': {
                'keywords': ['with ', '__enter__', '__exit__'],
                'patterns': [r'with\s+\w+.*as\s+\w+:']
            },
            'custom_exceptions': {
                'keywords': ['Exception)', 'Error)'],
                'patterns': [r'class\s+\w+Error\(', r'class\s+\w+Exception\(']
            },
            'dataclasses': {
                'keywords': ['@dataclass', 'from dataclasses'],
                'patterns': [r'@dataclass']
            },
            'async_programming': {
                'keywords': ['async def', 'await ', 'asyncio'],
                'patterns': [r'async\s+def\s+', r'await\s+']
            },
            'comprehensions': {
                'keywords': ['for ', ' in '],
                'patterns': [r'\[.+for\s+\w+\s+in\s+', r'\{.+for\s+\w+\s+in\s+']
            }
        }
    
    def analyze_file(self, file_path: Path) -> DeepSkillAnalysis:
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = file_path.read_text(encoding='latin-1')
        
        language = self._detect_language(file_path)
        analysis = DeepSkillAnalysis(file_path=str(file_path))
        analysis.basic_skills.append(language)
        
        if language == 'python':
            try:
                tree = ast.parse(content)
                self._detect_caching_patterns(tree, content, analysis)
                self._detect_design_patterns(tree, content, analysis)
                self._detect_complexity_awareness(tree, content, analysis)
                self._detect_error_handling(tree, content, analysis)
                self._detect_type_safety(tree, content, analysis)
                self._detect_data_structures(tree, content, analysis)
            except SyntaxError:
                pass
        else:
            self._analyze_generic(content, language, analysis)
        
        return analysis
    
    def _detect_caching_patterns(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.If):
                        test_str = ast.unparse(stmt.test) if hasattr(ast, 'unparse') else ''
                        if 'is None' in test_str or '== None' in test_str:
                            analysis.advanced_skills.append('lazy-initialization')
                            analysis.evidence.append(SkillEvidence(
                                skill='lazy-initialization',
                                evidence_type='pattern',
                                location=f'Function: {node.name}',
                                reasoning='Detected lazy initialization pattern with None check',
                                confidence=0.9
                            ))
                            break
        if '@lru_cache' in content or '@cache' in content:
            analysis.advanced_skills.append('memoization')
            analysis.evidence.append(SkillEvidence(
                skill='memoization',
                evidence_type='decorator',
                location='File-level',
                reasoning='Uses functools caching decorators for performance',
                confidence=1.0
            ))
    
    def _detect_design_patterns(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        has_enum = 'Enum' in content or 'from enum import' in content
        has_dict_dispatch = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Dict):
                    if len(node.value.keys) > 2:
                        has_dict_dispatch = True
        
        if has_enum and has_dict_dispatch:
            analysis.design_patterns.append('strategy-pattern')
            analysis.evidence.append(SkillEvidence(
                skill='strategy-pattern',
                evidence_type='pattern',
                location='Class-level',
                reasoning='Enum + dictionary dispatch indicates Strategy pattern',
                confidence=0.8
            ))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                for arg in node.args.args[1:]:
                    if arg.annotation:
                        annotation_str = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else ''
                        if 'Optional' in annotation_str or 'Union' in annotation_str:
                            analysis.design_patterns.append('dependency-injection')
                            analysis.evidence.append(SkillEvidence(
                                skill='dependency-injection',
                                evidence_type='pattern',
                                location=f'__init__ method',
                                reasoning='Optional dependencies injected via constructor',
                                confidence=0.85
                            ))
                            break
        custom_exceptions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = ast.unparse(base) if hasattr(ast, 'unparse') else ''
                    if 'Exception' in base_name or 'Error' in base_name:
                        custom_exceptions.append(node.name)
        
        if custom_exceptions:
            analysis.design_patterns.append('custom-exception-hierarchy')
            analysis.evidence.append(SkillEvidence(
                skill='custom-exception-hierarchy',
                evidence_type='pattern',
                location=f'Classes: {", ".join(custom_exceptions)}',
                reasoning='Defines domain-specific exceptions for fine-grained error handling',
                confidence=1.0
            ))
    
    def _detect_complexity_awareness(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        set_usage_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ''
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                if func_name == 'list' and len(node.args) > 0:
                    if isinstance(node.args[0], ast.Call):
                        if isinstance(node.args[0].func, ast.Name):
                            if node.args[0].func.id == 'set':
                                set_usage_count += 1
        
        if set_usage_count > 0:
            analysis.advanced_skills.append('algorithmic-optimization')
            analysis.complexity_insights['set_deduplication'] = set_usage_count
            analysis.evidence.append(SkillEvidence(
                skill='algorithmic-optimization',
                evidence_type='data-structure',
                location=f'{set_usage_count} occurrences',
                reasoning='Uses set for O(n) deduplication instead of O(n²) list iteration',
                confidence=0.95
            ))
        if 'hashlib' in content or 'sha256' in content or 'md5' in content:
            analysis.advanced_skills.append('cryptographic-hashing')
            analysis.evidence.append(SkillEvidence(
                skill='cryptographic-hashing',
                evidence_type='library',
                location='Import-level',
                reasoning='Uses cryptographic hashing for O(1) lookups and integrity',
                confidence=0.9
            ))
    
    def _detect_error_handling(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        try_except_count = 0
        graceful_degradation = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                try_except_count += 1
                if len(node.handlers) > 0:
                    for handler in node.handlers:
                        if len(handler.body) > 1 or (
                            len(handler.body) == 1 and 
                            not isinstance(handler.body[0], (ast.Pass, ast.Raise))
                        ):
                            graceful_degradation = True
        
        if try_except_count > 0:
            analysis.basic_skills.append('exception-handling')
        
        if graceful_degradation:
            analysis.advanced_skills.append('graceful-degradation')
            analysis.evidence.append(SkillEvidence(
                skill='graceful-degradation',
                evidence_type='pattern',
                location=f'{try_except_count} try-except blocks',
                reasoning='Implements fallback mechanisms instead of failing completely',
                confidence=0.85
            ))
    
    def _detect_type_safety(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        type_hint_count = 0
        return_type_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.annotation:
                        type_hint_count += 1
                if node.returns:
                    return_type_count += 1
        
        if type_hint_count + return_type_count >= 5:
            analysis.advanced_skills.append('static-type-checking')
            analysis.evidence.append(SkillEvidence(
                skill='static-type-checking',
                evidence_type='annotation',
                location=f'{type_hint_count} parameters, {return_type_count} returns',
                reasoning='Comprehensive type hints enable static analysis and IDE support',
                confidence=0.9
            ))
        if '@dataclass' in content:
            analysis.advanced_skills.append('modern-python-features')
            analysis.evidence.append(SkillEvidence(
                skill='modern-python-features',
                evidence_type='decorator',
                location='Class definitions',
                reasoning='Uses dataclasses for structured data with automatic methods',
                confidence=1.0
            ))
    
    def _detect_data_structures(self, tree: ast.AST, content: str, analysis: DeepSkillAnalysis):
        
        comprehension_count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                comprehension_count += 1
        
        if comprehension_count > 3:
            analysis.advanced_skills.append('pythonic-idioms')
            analysis.evidence.append(SkillEvidence(
                skill='pythonic-idioms',
                evidence_type='syntax',
                location=f'{comprehension_count} comprehensions',
                reasoning='Uses comprehensions for concise, efficient iteration',
                confidence=0.8
            ))
        with_count = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                with_count += 1
        
        if with_count > 0:
            analysis.advanced_skills.append('resource-management')
            analysis.evidence.append(SkillEvidence(
                skill='resource-management',
                evidence_type='pattern',
                location=f'{with_count} with statements',
                reasoning='Uses context managers for automatic resource cleanup',
                confidence=0.9
            ))
    
    def _analyze_generic(self, content: str, language: str, analysis: DeepSkillAnalysis):
        patterns = {
            'java': {
                'generics': r'<[A-Z][a-zA-Z0-9,\s<>]*>',
                'interface': r'interface\s+\w+',
                'abstract': r'abstract\s+class',
                'stream': r'\.stream\(\)',
                'lambda': r'->',
                'annotation': r'@\w+',
                'exception': r'class\s+\w+Exception\s+extends'
            },
            'cpp': {
                'template': r'template\s*<',
                'smart_ptr': r'(unique_ptr|shared_ptr|weak_ptr)',
                'raii': r'(std::lock_guard|std::unique_lock)',
                'move': r'std::move',
                'constexpr': r'constexpr',
                'namespace': r'namespace\s+\w+'
            },
            'c': {
                'pointer': r'\*\w+',
                'malloc': r'(malloc|calloc|realloc|free)',
                'struct': r'struct\s+\w+',
                'typedef': r'typedef\s+'
            },
            'javascript': {
                'arrow': r'=>',
                'async': r'async\s+',
                'promise': r'Promise',
                'destructure': r'(const|let)\s*\{[^}]+\}\s*=',
                'spread': r'\.\.\.\w+'
            },
            'typescript': {
                'interface': r'interface\s+\w+',
                'type_alias': r'type\s+\w+\s*=',
                'generic': r'<[A-Z][a-zA-Z0-9,\s]*>',
                'readonly': r'readonly\s+'
            }
        }
        
        lang_patterns = patterns.get(language, {})
        for skill, pattern in lang_patterns.items():
            if re.search(pattern, content):
                analysis.advanced_skills.append(f'{language}-{skill}')
        
        if re.search(r'(HashMap|HashSet|unordered_map|unordered_set|dict|Map|Set)', content):
            analysis.advanced_skills.append('hash-based-structures')
            analysis.evidence.append(SkillEvidence(
                skill='hash-based-structures',
                evidence_type='data-structure',
                location='File-level',
                reasoning='Uses hash-based data structures for O(1) operations',
                confidence=0.85
            ))
        
        if re.search(r'(try|catch|except|throw|throws)', content, re.IGNORECASE):
            analysis.basic_skills.append('exception-handling')
    
    def analyze_directory(self, directory: Path) -> Dict[str, DeepSkillAnalysis]:
        results = {}
        extensions = tuple(self.language_extensions.keys())
        
        for code_file in directory.rglob('*'):
            if code_file.suffix.lower() not in self.language_extensions:
                continue
            if any(skip in code_file.parts for skip in ['__pycache__', '.venv', 'venv', 'node_modules', 'build', 'dist']):
                continue
            
            try:
                analysis = self.analyze_file(code_file)
                results[str(code_file)] = analysis
            except Exception as e:
                print(f"Error analyzing {code_file}: {e}")
        
        return results
    
    def aggregate_skills(self, analyses: Dict[str, DeepSkillAnalysis]) -> Dict[str, Any]:
        all_basic = set()
        all_advanced = set()
        all_patterns = set()
        evidence_by_skill = defaultdict(list)
        
        for analysis in analyses.values():
            all_basic.update(analysis.basic_skills)
            all_advanced.update(analysis.advanced_skills)
            all_patterns.update(analysis.design_patterns)
            
            for evidence in analysis.evidence:
                evidence_by_skill[evidence.skill].append(evidence)
        
        return {
            'basic_skills': sorted(list(all_basic)),
            'advanced_skills': sorted(list(all_advanced)),
            'design_patterns': sorted(list(all_patterns)),
            'evidence_count': sum(len(v) for v in evidence_by_skill.values()),
            'evidence_by_skill': dict(evidence_by_skill),
            'total_files_analyzed': len(analyses)
        }

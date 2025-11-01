import re
import json
import logging
from pathlib import Path
from typing import List, Set, Optional

# Set up logging
logger = logging.getLogger(__name__)


# Language mappings by file extension
EXTENSION_TO_LANGUAGE = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.hpp': 'cpp',
    '.cs': 'csharp',
    '.go': 'go',
    '.rb': 'ruby',
    '.php': 'php',
    '.kt': 'kotlin',
    '.swift': 'swift',
}

# Shebang patterns for language detection
SHEBANG_PATTERNS = {
    'python': r'#!.*python[0-9]*',
    'javascript': r'#!.*node',
    'ruby': r'#!.*ruby',
    'shell': r'#!.*(bash|sh)',
}

# Framework detection patterns per language
FRAMEWORK_PATTERNS = {
    'python': {
        'fastapi': r'(?:from\s+fastapi\s+import|import\s+fastapi)',
        'django': r'(?:from\s+django|import\s+django)',
        'flask': r'(?:from\s+flask\s+import|import\s+flask)',
        'sqlalchemy': r'(?:from\s+sqlalchemy|import\s+sqlalchemy)',
        'pytest': r'(?:import\s+pytest|@pytest\.|def\s+test_)',
        'pandas': r'(?:import\s+pandas|from\s+pandas)',
        'numpy': r'(?:import\s+numpy|from\s+numpy)',
    },
    'javascript': {
        'react': r'(?:import\s+.*\s+from\s+[\'"]react[\'"]|require\([\'"]react[\'"])',
        'vue': r'(?:import\s+.*\s+from\s+[\'"]vue[\'"]|require\([\'"]vue[\'"])',
        'angular': r'(?:import\s+.*\s+from\s+[\'"]@angular|@angular/)',
        'express': r'(?:require\([\'"]express[\'"]|import\s+.*\s+from\s+[\'"]express[\'"])',
        'jest': r'(?:describe\(|test\(|it\(|expect\()',
        'node': r'(?:require\(|module\.exports)',
    },
    'typescript': {
        'react': r'(?:import\s+.*\s+from\s+[\'"]react[\'"])',
        'vue': r'(?:import\s+.*\s+from\s+[\'"]vue[\'"])',
        'angular': r'(?:import\s+.*\s+from\s+[\'"]@angular|@angular/)',
        'express': r'(?:import\s+.*\s+from\s+[\'"]express[\'"])',
        'jest': r'(?:describe\(|test\(|it\(|expect\()',
    },
    'java': {
        'spring': r'(?:import\s+org\.springframework|@SpringBootApplication|@RestController)',
        'hibernate': r'(?:import\s+org\.hibernate|@Entity)',
        'junit': r'(?:import\s+org\.junit|@Test)',
        'maven': r'(?:import\s+org\.apache\.maven)',
    },
    'cpp': {
        'boost': r'#include\s+<boost/',
        'qt': r'#include\s+<Q[A-Z]',
        'opencv': r'#include\s+<opencv2?/',
    },
    'c': {
        'boost': r'#include\s+<boost/',
        'opencv': r'#include\s+<opencv2?/',
    },
}


def detect_language_by_ext_and_shebang(filename: str, content: str) -> str:
    """
    Detect programming language based on file extension and shebang line.
    
    Args:
        filename: Name of the file (including extension)
        content: Content of the file
    
    Returns:
        Detected language name (lowercase), or 'unknown' if not detected
    """
    # Try extension first (highest priority)
    ext = Path(filename).suffix.lower()
    if ext in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[ext]
    
    # Try shebang as fallback
    if content and content.startswith('#!'):
        first_line = content.split('\n', 1)[0]
        for language, pattern in SHEBANG_PATTERNS.items():
            if re.search(pattern, first_line, re.IGNORECASE):
                return language
    
    return 'unknown'


def detect_frameworks_from_source(language: str, content: str) -> List[str]:
    """
    Detect frameworks from source code based on imports and patterns.
    
    Args:
        language: Programming language of the source code
        content: Source code content
    
    Returns:
        List of detected framework names (lowercase)
    """
    if language not in FRAMEWORK_PATTERNS:
        return []
    
    detected = []
    patterns = FRAMEWORK_PATTERNS[language]
    
    for framework, pattern in patterns.items():
        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            detected.append(framework)
    
    return detected


def detect_frameworks_from_manifests(project_root: Path) -> Set[str]:
    """
    Detect frameworks by parsing project manifest files.
    
    Supported manifest files:
    - package.json (JavaScript/TypeScript)
    - requirements.txt, pyproject.toml (Python)
    - pom.xml, build.gradle, build.gradle.kts (Java/Kotlin)
    - CMakeLists.txt (C/C++)
    
    Args:
        project_root: Path to the project root directory
    
    Returns:
        Set of detected framework names (lowercase)
    """
    frameworks = set()
    
    # Parse package.json for JavaScript/TypeScript frameworks
    package_json = project_root / "package.json"
    if package_json.exists():
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                dependencies = data.get('dependencies', {})
                dev_dependencies = data.get('devDependencies', {})
                all_deps = {**dependencies, **dev_dependencies}
                
                # Check for known frameworks
                js_frameworks = ['react', 'vue', 'angular', 'express', 'jest', 'webpack', 'next', 'svelte']
                for fw in js_frameworks:
                    if any(fw in dep.lower() for dep in all_deps.keys()):
                        frameworks.add(fw)
        except (json.JSONDecodeError, IOError):
            pass  # Silently handle parse errors
    
    # Parse requirements.txt for Python frameworks
    requirements_txt = project_root / "requirements.txt"
    if requirements_txt.exists():
        try:
            content = requirements_txt.read_text(encoding='utf-8').lower()
            python_frameworks = ['django', 'flask', 'fastapi', 'sqlalchemy', 'pytest', 'pandas', 'numpy']
            for fw in python_frameworks:
                if fw in content:
                    frameworks.add(fw)
        except IOError:
            pass
    
    # Parse pyproject.toml for Python frameworks
    pyproject_toml = project_root / "pyproject.toml"
    if pyproject_toml.exists():
        try:
            content = pyproject_toml.read_text(encoding='utf-8').lower()
            python_frameworks = ['django', 'flask', 'fastapi', 'sqlalchemy', 'pytest', 'pandas', 'numpy']
            for fw in python_frameworks:
                if fw in content:
                    frameworks.add(fw)
        except IOError:
            pass
    
    # Parse pom.xml for Java frameworks
    pom_xml = project_root / "pom.xml"
    if pom_xml.exists():
        try:
            content = pom_xml.read_text(encoding='utf-8').lower()
            if 'springframework' in content or 'spring-boot' in content:
                frameworks.add('spring')
            if 'hibernate' in content:
                frameworks.add('hibernate')
            if 'junit' in content:
                frameworks.add('junit')
            if 'maven' in content:
                frameworks.add('maven')
        except IOError:
            pass
    
    # Parse build.gradle or build.gradle.kts for Java/Kotlin frameworks
    for gradle_file in ['build.gradle', 'build.gradle.kts']:
        gradle = project_root / gradle_file
        if gradle.exists():
            try:
                content = gradle.read_text(encoding='utf-8').lower()
                if 'springframework' in content or 'spring-boot' in content:
                    frameworks.add('spring')
                if 'hibernate' in content:
                    frameworks.add('hibernate')
                if 'junit' in content:
                    frameworks.add('junit')
            except IOError:
                pass
    
    # Parse CMakeLists.txt for C/C++ frameworks
    cmake = project_root / "CMakeLists.txt"
    if cmake.exists():
        try:
            content = cmake.read_text(encoding='utf-8')
            # Look for find_package calls
            if re.search(r'find_package\s*\(\s*Qt[0-9]*', content, re.IGNORECASE):
                frameworks.add('qt')
            if re.search(r'find_package\s*\(\s*Boost', content, re.IGNORECASE):
                frameworks.add('boost')
            if re.search(r'find_package\s*\(\s*OpenCV', content, re.IGNORECASE):
                frameworks.add('opencv')
        except IOError:
            pass
    
    return frameworks


def merge_file_and_project_frameworks(file_fw: List[str], project_fw: Set[str]) -> List[str]:
    """
    Merge frameworks detected from file-level analysis with project-level frameworks.
    
    File-level frameworks are listed first, followed by additional project frameworks.
    Duplicates are removed.
    
    Args:
        file_fw: List of frameworks detected from source code analysis
        project_fw: Set of frameworks detected from manifest files
    
    Returns:
        Merged list of unique framework names
    """
    # Start with file frameworks to preserve order
    result = list(file_fw)
    
    # Add project frameworks that aren't already in the list
    for fw in sorted(project_fw):  # Sort for deterministic order
        if fw not in result:
            result.append(fw)
    
    return result


def get_supported_languages() -> List[str]:
    """Get list of all supported programming languages."""
    return sorted(set(EXTENSION_TO_LANGUAGE.values()))


def get_supported_extensions() -> List[str]:
    """Get list of all supported file extensions."""
    return sorted(EXTENSION_TO_LANGUAGE.keys())


"""
Shared Git utility functions with guarded imports for PyDriller and GitPython.
Provides commit iteration, intent classification, and ISO week calculations.
"""
from datetime import datetime, date, timedelta
from typing import Iterator, Dict, List
import re

# Guarded imports: prefer PyDriller, fall back to GitPython
try:
    from pydriller import Repository
    PYDRILLER_AVAILABLE = True
except ImportError:
    Repository = None
    PYDRILLER_AVAILABLE = False

try:
    from git import Repo as GitRepo
    GITPYTHON_AVAILABLE = True
except ImportError:
    GitRepo = None
    GITPYTHON_AVAILABLE = False


def iter_commits(repo_path) -> Iterator[Dict]:
    """
    Iterate over commits in a repository, yielding normalized commit data.
    
    Works with either PyDriller or GitPython depending on availability.
    Gracefully handles empty repositories (no commits yet).
    
    Args:
        repo_path: Path to the Git repository
    
    Yields:
        Dict with keys:
            - author_name: str
            - author_email: str
            - msg: str (commit message)
            - date: datetime
            - insertions: int
            - deletions: int
            - files: List[str] (file paths touched)
    """
    repo_path_str = str(repo_path)
    
    if PYDRILLER_AVAILABLE:
        # Use PyDriller
        try:
            repo = Repository(repo_path_str)
            for commit in repo.traverse_commits():
                files = []
                for mf in commit.modified_files:
                    # Use new_path if available, otherwise old_path
                    file_path = mf.new_path if mf.new_path else mf.old_path
                    if file_path:
                        files.append(file_path)
                
                yield {
                    "author_name": commit.author.name,
                    "author_email": commit.author.email,
                    "msg": commit.msg,
                    "date": commit.author_date,
                    "insertions": commit.insertions,
                    "deletions": commit.deletions,
                    "files": files,
                }
        except Exception as e:
            # Empty repository or invalid Git repo - return empty iterator
            # Common errors: "bad revision 'HEAD'", "does not have any commits yet"
            return
    
    elif GITPYTHON_AVAILABLE:
        # Fallback to GitPython
        try:
            repo = GitRepo(repo_path_str)
            for commit in repo.iter_commits():
                # Extract stats
                stats = commit.stats.total
                insertions = stats.get("insertions", 0)
                deletions = stats.get("deletions", 0)
                files = list(commit.stats.files.keys())
                
                yield {
                    "author_name": commit.author.name,
                    "author_email": commit.author.email,
                    "msg": commit.message,
                    "date": commit.committed_datetime,
                    "insertions": insertions,
                    "deletions": deletions,
                    "files": files,
                }
        except Exception as e:
            # Empty repository or invalid Git repo - return empty iterator
            # Common errors: "bad revision 'HEAD'", "does not have any commits yet"
            return
    
    else:
        raise ImportError("Neither PyDriller nor GitPython is available. Install one of them.")


def classify_intent(msg: str) -> str:
    """
    Classify commit intent based on message content.
    
    Rules:
    1. Check for conventional commit prefixes (case-insensitive)
    2. Check for keywords in the message
    3. Default to "other"
    
    Args:
        msg: Commit message
    
    Returns:
        One of: "feature", "bugfix", "refactor", "docs", "test", "other"
    """
    msg_lower = msg.lower().strip()
    
    # Check for conventional commit prefixes
    if msg_lower.startswith("feat:") or msg_lower.startswith("feature:"):
        return "feature"
    if msg_lower.startswith("fix:"):
        return "bugfix"
    if msg_lower.startswith("refactor:"):
        return "refactor"
    if msg_lower.startswith("docs:") or msg_lower.startswith("doc:"):
        return "docs"
    if msg_lower.startswith("test:") or msg_lower.startswith("tests:"):
        return "test"
    
    # Keyword-based classification
    # Feature indicators
    if any(keyword in msg_lower for keyword in ["add", "implement", "create"]):
        # But check if it's test-related first
        if any(test_kw in msg_lower for test_kw in ["test", "assert", "spec"]):
            return "test"
        return "feature"
    
    # Bug fix indicators
    if any(keyword in msg_lower for keyword in ["bug", "issue", "fix", "patch"]):
        return "bugfix"
    
    # Refactor indicators
    if any(keyword in msg_lower for keyword in ["cleanup", "refactor", "restructure", "reorganize"]):
        return "refactor"
    
    # Documentation indicators
    if any(keyword in msg_lower for keyword in ["readme", "doc", "documentation", "comment"]):
        return "docs"
    
    # Test indicators
    if any(keyword in msg_lower for keyword in ["test", "assert", "spec"]):
        return "test"
    
    return "other"


def iso_week_start(dt: datetime) -> date:
    """
    Get the ISO week start date (Monday) for a given datetime.
    
    Args:
        dt: datetime to get week start for
    
    Returns:
        date object representing the Monday of that ISO week
    """
    # Get ISO calendar (year, week, weekday)
    # weekday: 1=Monday, 7=Sunday
    iso_year, iso_week, iso_weekday = dt.isocalendar()
    
    # Calculate the Monday of this ISO week
    # Start from the date and subtract (weekday - 1) days to get to Monday
    days_since_monday = iso_weekday - 1
    monday = dt.date() - timedelta(days=days_since_monday)
    
    return monday

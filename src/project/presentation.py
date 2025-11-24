"""
Portfolio and Resume Item Generation

This module generates structured, human-facing summaries for projects analyzed
by the artifact pipeline. It is pure (no I/O, no LLM, no DB) and template-based.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List


@dataclass
class PortfolioItem:
    """
    Structured portfolio item suitable for a personal portfolio site
    """
    project_name: str
    tagline: str
    description: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    is_collaborative: bool = False
    total_commits: int = 0
    total_lines: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dictionary"""
        return asdict(self)


@dataclass
class ResumeItem:
    """
    Structured resume item containing bullet points for a CV
    """
    project_name: str
    bullets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to plain dictionary"""
        return asdict(self)


@dataclass
class ProjectMetrics:
    """
    Extracted metrics from a project analysis dict
    """
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    total_files: int = 0
    total_lines: int = 0
    total_commits: int = 0
    total_contributors: int = 0
    is_collaborative: bool = False


def extract_project_metrics(project_dict: Dict[str, Any]) -> ProjectMetrics:
    """
    Extract basic metrics from a project result dict produced by _process_project()
    
    Args:
        project_dict: Project result dictionary from ArtifactPipeline._process_project()
        
    Returns:
        ProjectMetrics with safely extracted values (defaults to empty/zero on missing data)
    """
    metrics = ProjectMetrics()
    
    # Extract from analysis_results -> code -> metrics
    try:
        analysis_results = project_dict.get('analysis_results', {})
        if isinstance(analysis_results, dict):
            code_analysis = analysis_results.get('code')
            if isinstance(code_analysis, dict) and 'error' not in code_analysis:
                code_metrics = code_analysis.get('metrics', {})
                if isinstance(code_metrics, dict):
                    metrics.languages = code_metrics.get('languages', [])
                    metrics.frameworks = code_metrics.get('frameworks', [])
                    metrics.skills = code_metrics.get('skills', [])
                    metrics.total_files = code_metrics.get('total_files', 0)
                    metrics.total_lines = code_metrics.get('total_lines', 0)
    except (AttributeError, TypeError, KeyError):
        # If any access fails, keep defaults
        pass
    
    # Extract from git_analysis
    try:
        git_analysis = project_dict.get('git_analysis')
        if isinstance(git_analysis, dict) and 'error' not in git_analysis:
            metrics.total_commits = git_analysis.get('total_commits', 0)
            metrics.total_contributors = git_analysis.get('total_contributors', 0)
            # is_collaborative if more than 1 contributor
            metrics.is_collaborative = metrics.total_contributors > 1
    except (AttributeError, TypeError, KeyError):
        # If any access fails, keep defaults
        pass
    
    return metrics


def generate_portfolio_item(project_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a portfolio item from a project analysis dict
    
    Args:
        project_dict: Project result dictionary from ArtifactPipeline._process_project()
        
    Returns:
        Dictionary representation of a PortfolioItem
    """
    # Extract project name safely
    project_name = project_dict.get('project_name', 'Unnamed Project')
    
    # Extract metrics
    metrics = extract_project_metrics(project_dict)
    
    # Build tagline
    tagline = _build_tagline(metrics)
    
    # Build description
    description = _build_description(metrics)
    
    # Create portfolio item
    portfolio = PortfolioItem(
        project_name=project_name,
        tagline=tagline,
        description=description,
        languages=metrics.languages[:10],  # Limit to top 10
        frameworks=metrics.frameworks[:10],  # Limit to top 10
        skills=metrics.skills[:15],  # Limit to top 15
        is_collaborative=metrics.is_collaborative,
        total_commits=metrics.total_commits,
        total_lines=metrics.total_lines
    )
    
    return portfolio.to_dict()


def generate_resume_item(project_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a resume item with 2-3 bullet points from a project analysis dict
    
    Args:
        project_dict: Project result dictionary from ArtifactPipeline._process_project()
        
    Returns:
        Dictionary representation of a ResumeItem
    """
    # Extract project name safely
    project_name = project_dict.get('project_name', 'Unnamed Project')
    
    # Extract metrics
    metrics = extract_project_metrics(project_dict)
    
    # Build bullets
    bullets = _build_resume_bullets(metrics)
    
    # Create resume item
    resume = ResumeItem(
        project_name=project_name,
        bullets=bullets
    )
    
    return resume.to_dict()


def _build_tagline(metrics: ProjectMetrics) -> str:
    """
    Build a one-line tagline for a project
    
    Args:
        metrics: Extracted project metrics
        
    Returns:
        Short tagline string
    """
    # Determine collaboration type
    collab_type = "Collaborative" if metrics.is_collaborative else "Individual"
    
    # Get primary language(s) - up to 2
    lang_phrase = ""
    if metrics.languages:
        if len(metrics.languages) == 1:
            lang_phrase = metrics.languages[0]
        elif len(metrics.languages) == 2:
            lang_phrase = f"{metrics.languages[0]} and {metrics.languages[1]}"
        else:
            lang_phrase = f"multi-language ({metrics.languages[0]}, {metrics.languages[1]})"
    else:
        lang_phrase = "software"
    
    # Get framework mention - up to 2
    framework_phrase = ""
    if metrics.frameworks:
        if len(metrics.frameworks) == 1:
            framework_phrase = f" using {metrics.frameworks[0]}"
        elif len(metrics.frameworks) >= 2:
            framework_phrase = f" using {metrics.frameworks[0]} and {metrics.frameworks[1]}"
    
    return f"{collab_type} {lang_phrase} project{framework_phrase}"


def _build_description(metrics: ProjectMetrics) -> str:
    """
    Build a 1-2 sentence description for a project
    
    Args:
        metrics: Extracted project metrics
        
    Returns:
        Description string
    """
    if metrics.total_files > 0 or metrics.total_lines > 0 or metrics.total_commits > 0:
        # Build description with available metrics
        parts = []
        
        if metrics.total_files > 0:
            parts.append(f"{metrics.total_files} source files")
        
        if metrics.total_lines > 0:
            parts.append(f"approximately {metrics.total_lines:,} lines of code")
        
        if metrics.total_commits > 0:
            parts.append(f"{metrics.total_commits} Git commits")
        
        if parts:
            metrics_str = ", ".join(parts)
            return f"Analyzed {metrics_str}."
        
    # Fallback for minimal metrics
    return "Project analyzed through automated artifact pipeline processing."


def _build_resume_bullets(metrics: ProjectMetrics) -> List[str]:
    """
    Build 2-3 resume bullet points from project metrics
    
    Args:
        metrics: Extracted project metrics
        
    Returns:
        List of 2-3 bullet strings
    """
    bullets = []
    
    # Bullet 1: What/How/Scale
    bullet1_parts = []
    
    if metrics.is_collaborative:
        bullet1_parts.append("Contributed to collaborative")
    else:
        bullet1_parts.append("Developed")
    
    # Mention languages
    if metrics.languages:
        if len(metrics.languages) == 1:
            bullet1_parts.append(f"{metrics.languages[0]} project")
        elif len(metrics.languages) == 2:
            bullet1_parts.append(f"{metrics.languages[0]} and {metrics.languages[1]} project")
        else:
            bullet1_parts.append(f"multi-language project ({', '.join(metrics.languages[:3])})")
    else:
        bullet1_parts.append("software project")
    
    # Add frameworks if available
    if metrics.frameworks:
        if len(metrics.frameworks) == 1:
            bullet1_parts.append(f"using {metrics.frameworks[0]}")
        elif len(metrics.frameworks) >= 2:
            bullet1_parts.append(f"using {metrics.frameworks[0]}, {metrics.frameworks[1]}")
    
    # Add scale information
    if metrics.total_files > 0 and metrics.total_lines > 0:
        bullet1_parts.append(f"totaling {metrics.total_lines:,} lines across {metrics.total_files} files")
    elif metrics.total_lines > 0:
        bullet1_parts.append(f"totaling approximately {metrics.total_lines:,} lines of code")
    elif metrics.total_files > 0:
        bullet1_parts.append(f"comprising {metrics.total_files} source files")
    
    bullets.append(" ".join(bullet1_parts) + ".")
    
    # Bullet 2: Version Control / Collaboration
    if metrics.is_collaborative and metrics.total_commits > 0:
        # Collaborative project with Git
        bullets.append(
            f"Collaborated with {metrics.total_contributors} contributors "
            f"through {metrics.total_commits} commits, demonstrating teamwork "
            f"and iterative development practices."
        )
    elif metrics.total_commits > 0:
        # Individual project with Git
        bullets.append(
            f"Maintained disciplined version control with {metrics.total_commits} "
            f"Git commits, demonstrating systematic development and code management."
        )
    else:
        # No Git data available - generic collaboration/development statement
        if metrics.is_collaborative:
            bullets.append(
                "Engaged in team-based development with focus on collaboration "
                "and coordinated workflow practices."
            )
        else:
            bullets.append(
                "Demonstrated independent project ownership and systematic "
                "approach to software development."
            )
    
    # Bullet 3: Skills
    if metrics.skills and len(metrics.skills) > 0:
        # Mention specific skills (limit to top 5 for brevity)
        skill_list = metrics.skills[:5]
        if len(skill_list) <= 2:
            skill_str = " and ".join(skill_list)
        else:
            skill_str = ", ".join(skill_list[:-1]) + f", and {skill_list[-1]}"
        
        bullets.append(
            f"Applied technical skills including {skill_str}, "
            f"showcasing proficiency in modern development practices."
        )
    else:
        # Generic skills statement
        bullets.append(
            "Demonstrated proficiency in software engineering principles, "
            "including code organization, documentation, and best practices."
        )
    
    return bullets


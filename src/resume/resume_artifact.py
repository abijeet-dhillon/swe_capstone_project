from __future__ import annotations

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader

SKILL_LEVELS = ("Advanced", "Proficient", "Working Knowledge", "Familiar")

_LATEX_REPLACEMENTS = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "_": r"\_",
    "%": r"\%",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(value: str) -> str:
    """Escape special LaTeX characters in plain text."""
    return "".join(_LATEX_REPLACEMENTS.get(char, char) for char in value)


def escape_latex_data(value: Any) -> Any:
    """Recursively escape LaTeX-sensitive strings."""
    if isinstance(value, str):
        return escape_latex(value)
    if isinstance(value, list):
        return [escape_latex_data(item) for item in value]
    if isinstance(value, dict):
        return {key: escape_latex_data(item) for key, item in value.items()}
    return value


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _format_date(value: Any) -> str:
    raw = _clean_text(value)
    if not raw:
        return ""
    iso_candidate = raw.split("T", 1)[0]
    try:
        return datetime.fromisoformat(iso_candidate).strftime("%b %Y")
    except ValueError:
        return raw


def _iter_projects(report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    projects = report.get("projects") or {}
    if not isinstance(projects, dict):
        return {}
    return {
        name: payload
        for name, payload in projects.items()
        if name != "_misc_files" and isinstance(payload, dict)
    }


def _select_identity(projects: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    best_name = ""
    best_email = ""
    best_commits = -1
    for payload in projects.values():
        git = _as_dict(payload.get("git_analysis"))
        for contributor in _as_list(git.get("contributors")):
            contrib = _as_dict(contributor)
            author = _as_dict(contrib.get("author"))
            commits = _to_int(contrib.get("commits"))
            name = _clean_text(author.get("name") or contrib.get("name"))
            email = _clean_text(author.get("email") or contrib.get("email"))
            if commits > best_commits and (name or email):
                best_commits = commits
                best_name = name
                best_email = email
    return {"name": best_name, "email": best_email}


def _collect_skills(projects: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    counts: Counter[str] = Counter()
    original_by_key: Dict[str, str] = {}
    for payload in projects.values():
        metrics = _as_dict(payload.get("project_metrics"))
        seen_in_project = set()
        for field in ("skills", "frameworks", "languages"):
            for raw_skill in _as_list(metrics.get(field)):
                skill = _clean_text(raw_skill)
                if not skill:
                    continue
                lowered = skill.casefold()
                if lowered in seen_in_project:
                    continue
                seen_in_project.add(lowered)
                counts[lowered] += 1
                original_by_key.setdefault(lowered, skill)

    buckets: Dict[str, List[str]] = {level: [] for level in SKILL_LEVELS}
    for lowered, count in sorted(
        counts.items(),
        key=lambda item: (-item[1], original_by_key[item[0]].casefold()),
    ):
        skill = original_by_key[lowered]
        # Frequency across projects is a simple and deterministic proficiency proxy.
        if count >= 4:
            buckets["Advanced"].append(skill)
        elif count == 3:
            buckets["Proficient"].append(skill)
        elif count == 2:
            buckets["Working Knowledge"].append(skill)
        else:
            buckets["Familiar"].append(skill)
    return buckets


def _ranked_project_names(report: Dict[str, Any], projects: Dict[str, Dict[str, Any]]) -> List[str]:
    names: List[str] = []
    ranking = _as_dict(report.get("project_ranking"))
    for summary in _as_list(ranking.get("top_summaries")):
        name = _clean_text(_as_dict(summary).get("name"))
        if name and name in projects and name not in names:
            names.append(name)
    for name in sorted(projects, key=str.casefold):
        if name not in names:
            names.append(name)
    return names


def _fallback_bullets(metrics: Dict[str, Any], git: Dict[str, Any]) -> List[str]:
    bullets: List[str] = []
    total_lines = _to_int(metrics.get("total_lines"))
    total_commits = _to_int(git.get("total_commits", metrics.get("total_commits")))
    total_contributors = _to_int(git.get("total_contributors", metrics.get("total_contributors")))
    if total_lines > 0:
        bullets.append(f"Delivered {total_lines:,} lines of implementation across project scope.")
    if total_commits > 0:
        if total_contributors > 1:
            bullets.append(
                f"Contributed {total_commits} commits in a {total_contributors}-contributor repository."
            )
        else:
            bullets.append(f"Contributed {total_commits} commits.")
    skills = [_clean_text(skill) for skill in _as_list(metrics.get("skills")) if _clean_text(skill)]
    if skills:
        bullets.append(f"Applied {', '.join(skills[:3])}.")
    return bullets[:3]


def _build_projects(report: Dict[str, Any], projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rendered_projects: List[Dict[str, Any]] = []
    for project_name in _ranked_project_names(report, projects):
        payload = projects[project_name]
        metrics = _as_dict(payload.get("project_metrics"))
        git = _as_dict(payload.get("git_analysis"))
        resume_item = _as_dict(payload.get("resume_item"))

        bullets = [
            _clean_text(bullet)
            for bullet in _as_list(resume_item.get("bullets"))
            if _clean_text(bullet)
        ]
        if not bullets:
            bullets = _fallback_bullets(metrics, git)

        tech_stack_items: List[str] = []
        for field in ("languages", "frameworks", "skills"):
            for value in _as_list(metrics.get(field)):
                text = _clean_text(value)
                if text and text not in tech_stack_items:
                    tech_stack_items.append(text)

        rendered_projects.append(
            {
                "name": _clean_text(resume_item.get("project_name") or payload.get("project_name") or project_name),
                "start_date": _format_date(git.get("first_commit_at") or metrics.get("duration_start")),
                "end_date": _format_date(git.get("last_commit_at") or metrics.get("duration_end")),
                "tech_stack": ", ".join(tech_stack_items[:10]),
                "github_url": "",
                "github_label": "",
                "bullets": bullets[:4],
            }
        )
    return rendered_projects


def build_resume_context(report: Dict[str, Any]) -> Dict[str, Any]:
    """Build template-ready context using existing analysis/report output."""
    projects = _iter_projects(report)
    identity = _select_identity(projects)
    context = {
        "name": identity["name"],
        "phone": "",
        "email": identity["email"],
        "linkedin_url": "",
        "linkedin_label": "",
        "github_url": "",
        "github_label": "",
        "education": [],
        "skills": _collect_skills(projects),
        "projects": _build_projects(report, projects),
        "awards": [],
    }
    return escape_latex_data(context)


def render_resume_template(
    context: Dict[str, Any],
    *,
    template_path: Path | None = None,
) -> str:
    path = template_path or Path(__file__).resolve().with_name("resume_template.tex")
    env = Environment(loader=FileSystemLoader(str(path.parent)), autoescape=False)
    template = env.get_template(path.name)
    return template.render(**context)


def write_rendered_resume(rendered_tex: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_tex, encoding="utf-8")
    return output_path


def generate_resume_tex_artifact(
    report: Dict[str, Any],
    output_path: Path,
    *,
    template_path: Path | None = None,
) -> Path:
    context = build_resume_context(report)
    rendered = render_resume_template(context, template_path=template_path)
    return write_rendered_resume(rendered, output_path)

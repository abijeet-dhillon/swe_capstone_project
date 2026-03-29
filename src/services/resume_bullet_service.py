"""
AI-powered resume bullet point generation.

Uses OpenAI to generate meaningful, project-specific resume bullets from
pipeline-extracted metadata and LLM document summaries.
"""
import json
import re
from typing import Any, Dict, List

from src.llm.openai_client import DEFAULT_MODEL, OpenAIClient


def generate_resume_bullets_with_llm(
    project_name: str,
    project_data: Dict[str, Any],
    doc_summaries: List[Dict[str, Any]],
    model: str = DEFAULT_MODEL,
) -> List[str]:
    """
    Generate 3 resume bullet points for a project using OpenAI.

    Args:
        project_name: Name of the project.
        project_data: Project result dict from the pipeline (contains
            analysis_results, git_analysis, project_metrics, etc.)
        doc_summaries: List of document summary dicts produced by
            SummarizationService (may be empty if no docs were found).
        model: OpenAI model to use.

    Returns:
        List of up to 3 resume bullet strings.
        Returns an empty list if generation fails — callers should fall back
        to template bullets in that case.
    """
    client = OpenAIClient()
    prompt = _build_prompt(project_name, project_data, doc_summaries)

    response = client.client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional resume writer specialising in software engineering roles. "
                    "Given structured information about a software project, generate exactly 3 concise, "
                    "impactful resume bullet points. Each bullet must start with a strong past-tense "
                    "action verb, include specific technical details from the project, and be suitable "
                    "for a CV. Return ONLY a JSON array of exactly 3 strings — no markdown, no extra text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=400,
        temperature=0.5,
    )

    raw = response.choices[0].message.content.strip()
    return _parse_bullets(raw)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_prompt(
    project_name: str,
    project_data: Dict[str, Any],
    doc_summaries: List[Dict[str, Any]],
) -> str:
    parts = [f"Project name: {project_name}"]

    # --- Metrics ---
    metrics = project_data.get("project_metrics") or {}
    languages = metrics.get("languages") or []
    frameworks = metrics.get("frameworks") or []
    skills = metrics.get("skills") or []
    total_lines = metrics.get("total_lines", 0)
    total_files = metrics.get("total_files", 0)
    has_tests = metrics.get("has_tests", False)
    has_docs = metrics.get("has_documentation", False)

    if languages:
        parts.append(f"Languages: {', '.join(languages[:6])}")
    if frameworks:
        parts.append(f"Frameworks / libraries: {', '.join(frameworks[:6])}")
    if skills:
        parts.append(f"Skills demonstrated: {', '.join(skills[:8])}")
    if total_lines:
        parts.append(f"Scale: {total_lines:,} lines of code across {total_files} files")
    if has_tests:
        parts.append("Includes automated test coverage")
    if has_docs:
        parts.append("Includes project documentation")

    # --- Git analysis ---
    git = project_data.get("git_analysis") or {}
    total_commits = git.get("total_commits", 0)
    total_contributors = git.get("total_contributors", 0)
    if total_commits:
        collab = f"{total_contributors} contributor(s)" if total_contributors > 1 else "solo"
        parts.append(f"Version control: {total_commits} commits ({collab})")

    # Activity mix across all contributors (feature / bugfix / refactor %)
    contributors = git.get("contributors") or []
    if contributors:
        agg: Dict[str, float] = {}
        total_c = sum(c.get("commits", 0) for c in contributors)
        if total_c > 0:
            for c in contributors:
                weight = c.get("commits", 0)
                for activity, val in (c.get("activity_mix") or {}).items():
                    agg[activity] = agg.get(activity, 0.0) + val * weight
            top = sorted(agg.items(), key=lambda x: -x[1])[:3]
            activity_str = ", ".join(
                f"{a} ({int(v / total_c * 100)}%)" for a, v in top if v > 0
            )
            if activity_str:
                parts.append(f"Commit activity: {activity_str}")

    # --- Document summaries (the most valuable context) ---
    summary_texts = []
    for entry in doc_summaries[:3]:
        if not isinstance(entry, dict):
            continue
        summary = entry.get("summary")
        if summary and isinstance(summary, str) and len(summary.strip()) > 20:
            summary_texts.append(summary.strip()[:600])

    if summary_texts:
        parts.append("\nWhat the project does (from its documentation):")
        for text in summary_texts:
            parts.append(f"  {text}")

    parts.append(
        "\nUsing all of the above, write 3 resume bullet points as a JSON array of strings."
    )
    return "\n".join(parts)


def _parse_bullets(raw: str) -> List[str]:
    """Parse bullet strings out of an OpenAI response.

    Primary path: response is a JSON array.
    Fallback: extract numbered/bulleted lines.
    """
    # --- JSON array (expected path) ---
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            cleaned = [str(b).strip() for b in parsed if str(b).strip()]
            if cleaned:
                return cleaned[:3]
    except (json.JSONDecodeError, ValueError):
        pass

    # --- Markdown code block wrapper ---
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if code_block:
        try:
            parsed = json.loads(code_block.group(1).strip())
            if isinstance(parsed, list):
                cleaned = [str(b).strip() for b in parsed if str(b).strip()]
                if cleaned:
                    return cleaned[:3]
        except (json.JSONDecodeError, ValueError):
            pass

    # --- Line-by-line fallback ---
    bullets: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # Strip leading list markers
        line = re.sub(r"^[\-\*\•]\s+", "", line)
        line = re.sub(r"^\d+[\.\)]\s*", "", line)
        if len(line) > 15:
            bullets.append(line)

    return bullets[:3]

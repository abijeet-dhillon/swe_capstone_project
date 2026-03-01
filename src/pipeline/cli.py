"""Unified CLI for artifact pipeline operations."""

import sys
import os
import json
import getpass
import argparse
import sqlite3
import shutil
from typing import Optional, List, Dict, Any


# ── Interactive helpers ────────────────────────────────────────────────────

BANNER = "Digital Work Artifact Miner — Interactive CLI\n" + "=" * 50

MAIN_MENU = """
  1. Analyze a new ZIP file
  2. Incremental update (merge new ZIP into existing portfolio)
  3. List all projects
  4. View project details
  5. View portfolio showcase
  6. View resume item
  7. Generate / regenerate portfolio & resume items
  8. Customize portfolio showcase (edit & save)
  9. Customize resume item (edit & save)
 10. Manage skills for a project
 11. Set your role in a project
 12. Add evidence of success for a project
 13. Associate a thumbnail image for a project
 14. Representation view (ranking / chronology / skills / showcase)
 15. View chronological skills timeline
 16. Delete data
 17. Start FastAPI server
  0. Exit
"""


def _inp(msg: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        v = input(f"  {msg}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return v or default


def _inp_int(msg: str) -> Optional[int]:
    raw = _inp(msg)
    try:
        return int(raw) if raw else None
    except ValueError:
        print("  Invalid number.")
        return None


def _inp_yn(msg: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = _inp(f"{msg} ({hint})", "")
    return (raw.lower() in ("y", "yes")) if raw else default


def _get_store():
    from src.insights.storage import ProjectInsightsStore
    return ProjectInsightsStore()


def _get_pipeline(store=None):
    from src.pipeline.presentation_pipeline import PresentationPipeline
    return PresentationPipeline(insights_store=store or _get_store())


def _pick_project(store=None) -> Optional[int]:
    """Print project table and prompt for a project ID. Returns ID or None."""
    store = store or _get_store()
    args = argparse.Namespace(
        db_path=None, encryption_key_env=None,
        language=None, framework=None, zip_path=None, zip_hash=None
    )
    # Reuse existing handle_list output
    handle_list(args)
    return _inp_int("Enter project ID")


# ── Interactive action implementations ────────────────────────────────────

def _iact_analyze():
    zip_path = _inp("Path to ZIP file")
    if not zip_path or not os.path.isfile(zip_path):
        print("  File not found." if zip_path else "  Cancelled.")
        return
    args = argparse.Namespace(zip_path=zip_path, user_id=None)
    handle_analyze(args)


def _iact_incremental():
    """Incrementally update an existing ZIP analysis with a new ZIP file."""
    print("  Incremental update merges a new ZIP into an existing portfolio.")
    print("  • Projects only in the old ZIP are kept (reassigned to the new hash).")
    print("  • Projects only in the new ZIP are added.")
    print("  • Projects present in both are replaced by the new ZIP's version.\n")

    # --- pick existing ZIP hash -------------------------------------------
    store = _get_store()
    runs = store.list_recent_zipfiles(limit=20)
    if not runs:
        print("  No existing analyses found. Run option 1 first.")
        return

    print("  Existing ZIP analyses:")
    print(f"  {'#':<4}  {'ZIP Hash':<16}  {'Source':<40}  {'Projects'}")
    print(f"  {'-'*4}  {'-'*16}  {'-'*40}  {'-'*8}")
    for i, run in enumerate(runs, 1):
        zh = (run.get("zip_hash") or "")[:16]
        src = (run.get("zip_path") or run.get("source_name") or "N/A")[-40:]
        proj_names = [p for p in store.list_projects_for_zip(run.get("zip_hash") or "") if p != "_misc_files"]
        print(f"  {i:<4}  {zh:<16}  {src:<40}  {len(proj_names)}")

    idx = _inp_int("Select existing analysis number to update")
    if idx is None or not (1 <= idx <= len(runs)):
        print("  Invalid selection. Cancelled.")
        return
    old_zip_hash = runs[idx - 1]["zip_hash"]

    # --- pick new ZIP file -----------------------------------------------
    new_zip_path = _inp("Path to new ZIP file")
    if not new_zip_path or not os.path.isfile(new_zip_path):
        print("  File not found." if new_zip_path else "  Cancelled.")
        return

    args = argparse.Namespace(
        new_zip_path=new_zip_path,
        old_zip_hash=old_zip_hash,
        user_id=None,
    )
    handle_incremental(args)


def _iact_list():
    args = argparse.Namespace(
        db_path=None, encryption_key_env=None,
        language=None, framework=None, zip_path=None, zip_hash=None
    )
    handle_list(args)


def _iact_view_project():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    payload = store.load_project_insight_by_id(pid)
    if payload is None:
        print(f"  Project {pid} not found.")
        return
    from src.insights.user_role_store import ProjectRoleStore
    meta = _get_pipeline(store)._get_project_metadata(pid)
    role = ProjectRoleStore().get_user_role(meta["zip_hash"], meta["project_name"]) if meta else None
    print(f"\n{'='*60}")
    print(f"  PROJECT {pid}: {payload.get('project_name', 'N/A')}")
    if role:
        print(f"  Your Role:   {role}")
    m = payload.get("project_metrics") or {}
    for label, key in [("Languages", "languages"), ("Frameworks", "frameworks"), ("Skills", "skills")]:
        val = ", ".join(m.get(key, []))
        if val:
            print(f"  {label}: {val}")
    print(f"  Files: {m.get('total_files', 0)}  |  Lines: {m.get('total_lines', 0):,}")
    print(f"  Git Repo: {'Yes' if payload.get('is_git_repo') else 'No'}")
    git = payload.get("git_analysis") or {}
    if git:
        print(f"  Commits: {git.get('total_commits', 0)}  |  Contributors: {git.get('total_contributors', 0)}")
    success = payload.get("success_metrics") or {}
    if success and "error" not in success:
        print("  Success Metrics:")
        for k, v in success.items():
            if isinstance(v, (str, int, float)):
                print(f"    {k}: {v}")
    print(f"{'='*60}\n")


def _iact_view_portfolio():
    pid = _pick_project()
    if pid is None:
        return
    args = argparse.Namespace(
        project_id=pid, zip_hash=None, project_name=None,
        db_path=None, encryption_key_env=None
    )
    handle_show_portfolio(args)


def _iact_view_resume():
    pid = _pick_project()
    if pid is None:
        return
    args = argparse.Namespace(
        project_id=pid, zip_hash=None, project_name=None,
        db_path=None, encryption_key_env=None
    )
    handle_show_resume(args)


def _iact_generate():
    print("  a) Single project   b) All projects")
    choice = _inp("Choice", "a").lower()
    if choice == "a":
        pid = _pick_project()
        if pid is None:
            return
        args = argparse.Namespace(
            project_id=pid, zip_hash=None, project_name=None,
            all_in_zip=False, all=False, db_path=None,
            encryption_key_env=None, limit=None
        )
    else:
        args = argparse.Namespace(
            project_id=None, zip_hash=None, project_name=None,
            all_in_zip=False, all=True, db_path=None,
            encryption_key_env=None, limit=None
        )
    handle_present(args)


def _iact_edit_portfolio():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    payload = store.load_project_insight_by_id(pid)
    if payload is None:
        print(f"  Project {pid} not found.")
        return
    p = payload.get("portfolio_item") or {}
    print(f"\n  Current — Tagline: {p.get('tagline','')}  |  Type: {p.get('project_type','')}  |  Complexity: {p.get('complexity','')}")
    print(f"  Description: {p.get('description','')}")
    print("  Leave blank to keep current value.")
    fields: Dict[str, Any] = {}
    for prompt, key in [("New tagline", "tagline"), ("New description", "description"),
                        ("New project type", "project_type"), ("New complexity", "complexity"),
                        ("New summary", "summary")]:
        v = _inp(prompt)
        if v:
            fields[key] = v
    v = _inp("New key features (comma-separated)")
    if v:
        fields["key_features"] = [x.strip() for x in v.split(",") if x.strip()]
    if not fields:
        print("  No changes made.")
        return
    store.update_portfolio_insights_fields(pid, fields)
    print("  Portfolio saved successfully.")


def _iact_edit_resume():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    payload = store.load_project_insight_by_id(pid)
    if payload is None:
        print(f"  Project {pid} not found.")
        return
    bullets = list((payload.get("resume_item") or {}).get("bullets", []))
    print(f"\n  Current bullets:")
    for i, b in enumerate(bullets, 1):
        print(f"    {i}. {b}")
    print("  a) Replace all  b) Edit one  c) Add  d) Remove")
    choice = _inp("Choice", "a").lower()
    if choice == "a":
        new_bullets, idx = [], 1
        while True:
            line = _inp(f"Bullet {idx} (blank to finish)")
            if not line:
                break
            new_bullets.append(line)
            idx += 1
        if new_bullets:
            store.replace_resume_bullets(pid, new_bullets)
            print(f"  Saved {len(new_bullets)} bullet(s).")
    elif choice == "b":
        i = _inp_int(f"Which bullet (1-{len(bullets)})")
        if i and 1 <= i <= len(bullets):
            t = _inp(f"New text for bullet {i}")
            if t:
                bullets[i - 1] = t
                store.replace_resume_bullets(pid, bullets)
                print("  Updated.")
    elif choice == "c":
        t = _inp("New bullet text")
        if t:
            bullets.append(t)
            store.replace_resume_bullets(pid, bullets)
            print("  Added.")
    elif choice == "d":
        i = _inp_int(f"Which bullet to remove (1-{len(bullets)})")
        if i and 1 <= i <= len(bullets):
            store.replace_resume_bullets(pid, bullets[:i-1] + bullets[i:])
            print(f"  Removed bullet {i}.")


def _iact_skills():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    payload = store.load_project_insight_by_id(pid)
    if payload is None:
        print(f"  Project {pid} not found.")
        return
    skills = list((payload.get("project_metrics") or {}).get("skills", []))
    print(f"\n  Current skills: {', '.join(skills) or '(none)'}")
    print("  a) Replace all  b) Add  c) Remove  d) Rename")
    choice = _inp("Choice", "a").lower()
    if choice == "a":
        v = _inp("New skills (comma-separated)")
        if v:
            store.update_project_skills(pid, [s.strip() for s in v.split(",") if s.strip()])
            print("  Saved.")
    elif choice == "b":
        v = _inp("Skills to add (comma-separated)")
        if v:
            to_add = [s.strip().lower() for s in v.split(",") if s.strip()]
            low = {s.lower() for s in skills}
            store.update_project_skills(pid, skills + [s for s in to_add if s not in low])
            print("  Added.")
    elif choice == "c":
        v = _inp("Skills to remove (comma-separated)")
        if v:
            rm = {s.strip().lower() for s in v.split(",") if s.strip()}
            store.update_project_skills(pid, [s for s in skills if s.lower() not in rm])
            print("  Removed.")
    elif choice == "d":
        old = _inp("Skill to rename")
        new = _inp("New name")
        if old and new:
            store.update_project_skills(pid, [new if s.lower() == old.lower() else s for s in skills])
            print(f"  Renamed '{old}' → '{new}'.")


def _iact_set_role():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    meta = _get_pipeline(store)._get_project_metadata(pid)
    if meta is None:
        print(f"  Project {pid} not found.")
        return
    from src.insights.user_role_store import ProjectRoleStore
    rs = ProjectRoleStore()
    current = rs.get_user_role(meta["zip_hash"], meta["project_name"])
    if current:
        print(f"  Current role: {current}")
    role = _inp("Your role in this project (e.g. Lead Developer)")
    if role and rs.set_user_role(meta["zip_hash"], meta["project_name"], role):
        print(f"  Role set to: {role}")
    else:
        print("  Cancelled or failed.")


def _iact_evidence():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    payload = store.load_project_insight_by_id(pid)
    if payload is None:
        print(f"  Project {pid} not found.")
        return
    current = dict(payload.get("success_metrics") or {})
    if current and "error" not in current:
        print("  Existing metrics:")
        for k, v in current.items():
            print(f"    {k}: {v}")
    print("  Enter metric key-value pairs. Leave key blank to finish.")
    while True:
        k = _inp("Metric name")
        if not k:
            break
        v = _inp(f"Value for '{k}'")
        if v:
            current[k] = v
    if current:
        store.update_portfolio_insights_fields(pid, {"summary": json.dumps(current)})
        print("  Evidence of success saved.")
    else:
        print("  No changes.")


def _iact_thumbnail():
    pid = _pick_project()
    if pid is None:
        return
    store = _get_store()
    meta = _get_pipeline(store)._get_project_metadata(pid)
    if meta is None:
        print(f"  Project {pid} not found.")
        return
    img = _inp("Path to image file (PNG, JPEG, WebP)")
    if not img or not os.path.isfile(img):
        print("  File not found." if img else "  Cancelled.")
        return
    if not img.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        print("  Invalid format. Use PNG, JPEG, or WebP.")
        return
    if os.path.getsize(img) > 5 * 1024 * 1024:
        print("  File too large (max 5 MB).")
        return
    dest_dir = os.path.join("data", "thumbnails")
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"project_{pid}{os.path.splitext(img)[1]}")
    shutil.copy2(img, dest)
    print(f"  Thumbnail saved to {dest} for '{meta['project_name']}'.")


def _iact_rerank():
    """Sub-action: manually order projects by ID (used within representation menu)."""
    store = _get_store()
    pipeline = _get_pipeline(store)
    projects = pipeline.list_available_projects()
    if not projects:
        print("  No projects found.")
        return
    print("\n  Current projects:")
    for i, p in enumerate(projects, 1):
        print(f"    {i}. [{p['project_id']}] {p.get('project_name', '?')}")
    raw = _inp("New order as comma-separated IDs (e.g. 3,1,2)")
    if not raw:
        print("  Cancelled.")
        return
    try:
        order = [int(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError:
        print("  Invalid input.")
        return
    print("  New ranking:")
    for rank, pid in enumerate(order, 1):
        name = next((p.get("project_name", "?") for p in projects if p["project_id"] == pid), "?")
        print(f"    {rank}. [{pid}] {name}")
    if _inp_yn("Save this ranking?"):
        print("  Ranking saved.")
    else:
        print("  Cancelled.")


def _iact_representation():
    """Configure and preview a representation view (ranking, chronology, skills, showcase)."""
    store = _get_store()
    runs = store.list_recent_zipfiles(limit=1)
    if not runs:
        print("  No analyses found. Run option 1 first.")
        return
    zip_hash = runs[0]["zip_hash"]
    report = store.load_zip_report(zip_hash)
    if not report:
        print("  Could not load report for the most recent analysis.")
        return

    print(f"\n  Representation builder for ZIP: {zip_hash[:16]}...")
    print("  Configure each section (press Enter to keep defaults).\n")

    # --- Ranking ----------------------------------------------------------
    print("  [RANKING]")
    print("  Criteria: score (default), commits, loc, recency, impact, user_contrib")
    criteria = _inp("  Ranking criteria", "score").strip() or "score"
    valid_criteria = {"score", "commits", "loc", "recency", "impact", "user_contrib"}
    if criteria not in valid_criteria:
        print(f"  Unknown criteria '{criteria}', using 'score'.")
        criteria = "score"
    n_raw = _inp("  Limit to top N projects (blank = all)")
    n_limit: Optional[int] = None
    if n_raw:
        try:
            n_limit = int(n_raw)
        except ValueError:
            print("  Invalid number, showing all.")

    manual_raw = _inp("  Manual order: comma-separated project names (blank = auto)")
    manual_order = [s.strip() for s in manual_raw.split(",") if s.strip()] if manual_raw else []

    # --- Chronology -------------------------------------------------------
    print("\n  [CHRONOLOGY]")
    show_chron = _inp_yn("  Include chronological skills timeline?", default=True)

    # --- Skills -----------------------------------------------------------
    print("\n  [SKILLS]")
    show_skills = _inp_yn("  Include aggregated skills list?", default=True)
    highlight: List[str] = []
    suppress: List[str] = []
    if show_skills:
        h_raw = _inp("  Skills to highlight (comma-separated, blank = none)")
        highlight = [s.strip() for s in h_raw.split(",") if s.strip()] if h_raw else []
        s_raw = _inp("  Skills to suppress (comma-separated, blank = none)")
        suppress = [s.strip() for s in s_raw.split(",") if s.strip()] if s_raw else []

    # --- Showcase ---------------------------------------------------------
    print("\n  [SHOWCASE]")
    show_showcase = _inp_yn("  Include portfolio showcase?", default=True)
    selected_projects: List[str] = []
    if show_showcase:
        sp_raw = _inp("  Selected projects (comma-separated names, blank = all)")
        selected_projects = [s.strip() for s in sp_raw.split(",") if s.strip()] if sp_raw else []

    # --- Build and display ------------------------------------------------
    from src.api.routers.projects import (
        _build_ranking_output,
        _build_skills_output,
        _build_showcase_output,
    )

    print(f"\n{'='*70}")
    print("  REPRESENTATION PREVIEW")
    print(f"{'='*70}\n")

    # Ranking
    ranking_cfg = {"enabled": True, "criteria": criteria, "n": n_limit, "manual_order": manual_order}
    ranking_out = _build_ranking_output(report, ranking_cfg)
    items = ranking_out.get("items", [])
    print(f"  RANKING  (criteria: {criteria}, total: {ranking_out.get('total_projects_ranked', 0)})")
    for entry in items:
        score = entry.get("score", 0)
        m = entry.get("metrics", {})
        print(
            f"    #{entry.get('rank', '?'):<3} {entry.get('name', 'N/A'):<30}"
            f"  score={score:.4f}  commits={m.get('commits', 0)}  loc={m.get('loc', 0):,}"
        )
    if not items:
        print("    (no projects to rank)")

    # Chronology
    if show_chron:
        global_insights = report.get("global_insights") or {}
        chron = global_insights.get("chronological_skills") or {}
        timeline = chron.get("timeline", [])
        print(f"\n  CHRONOLOGY  ({len(timeline)} events)")
        for event in timeline[:10]:
            ts = (event.get("timestamp") or "N/A")[:19]
            print(f"    [{ts}]  {event.get('category', '?'):<12}  {', '.join(event.get('skills', []))}")
        if len(timeline) > 10:
            print(f"    ... and {len(timeline) - 10} more events")
        if not timeline:
            print("    (no chronological data)")

    # Skills
    if show_skills:
        skills_cfg = {"enabled": True, "highlight": highlight, "suppress": suppress}
        skills_out = _build_skills_output(report, skills_cfg)
        all_skills = skills_out.get("skills", [])
        highlighted = skills_out.get("highlighted", [])
        print(f"\n  SKILLS  ({len(all_skills)} total, {len(highlighted)} highlighted)")
        if all_skills:
            print(f"    {', '.join(all_skills[:20])}" + (" ..." if len(all_skills) > 20 else ""))
        else:
            print("    (no skills found)")

    # Showcase
    if show_showcase:
        showcase_cfg = {"enabled": True, "selected_projects": selected_projects}
        showcase_out = _build_showcase_output(report, showcase_cfg)
        sc_projects = showcase_out.get("projects", [])
        print(f"\n  SHOWCASE  ({len(sc_projects)} project(s))")
        for sc in sc_projects:
            pf = sc.get("portfolio_item") or {}
            print(f"    • {sc.get('project_name', 'N/A')}: {pf.get('tagline', '(no tagline)')}")

    print(f"\n{'='*70}\n")


def _iact_chronological():
    store = _get_store()
    global_insights = store.load_latest_global_insights() or {}
    chron = global_insights.get("chronological_skills") or {}
    timeline = chron.get("timeline", [])
    if not timeline:
        print("  No chronological skills data. Run an analysis first.")
        return
    print(f"\n  CHRONOLOGICAL SKILLS TIMELINE")
    print(f"  Total events: {chron.get('total_events', len(timeline))}  |  Categories: {', '.join(chron.get('categories', []))}\n")
    for event in timeline[:30]:
        ts = (event.get("timestamp") or "N/A")[:19]
        print(f"  [{ts}]  {event.get('category','?'):<12}  {', '.join(event.get('skills', []))}")
    if len(timeline) > 30:
        print(f"\n  ... and {len(timeline) - 30} more events (showing first 30)")


def _iact_delete():
    args_ns = argparse.Namespace(db_path=None)
    print("  a) Delete all data   b) Delete a project   c) Delete all insights   d) Delete all configs")
    choice = _inp("Choice").lower()
    if choice == "a":
        args_ns.delete_target = "all"
        handle_delete(args_ns)
    elif choice == "b":
        pid = _inp_int("Project ID to delete")
        if pid is None:
            return
        args_ns.delete_target = "insight"
        args_ns.project_id = pid
        args_ns.scope = None
        handle_delete(args_ns)
    elif choice == "c":
        args_ns.delete_target = "insight"
        args_ns.project_id = None
        args_ns.scope = "all"
        handle_delete(args_ns)
    elif choice == "d":
        args_ns.delete_target = "config"
        args_ns.scope = "all"
        handle_delete(args_ns)
    else:
        print("  Invalid choice.")


def _iact_start_api():
    print("\n  FastAPI endpoints available at http://localhost:8000")
    print("  POST /privacy-consent  |  POST /projects/upload  |  GET /projects")
    print("  GET /projects/{id}  |  GET/POST /resume/{id}  |  GET/POST /portfolio/{id}")
    print("  GET /skills  |  GET /chronological/skills  |  GET /health")
    print("  Press Ctrl+C to stop.\n")
    try:
        import uvicorn
        uvicorn.run("src.api.app:app", host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("  Server stopped.")
    except ImportError:
        print("  Error: install uvicorn[standard] first.")


_INTERACTIVE_ACTIONS = {
    "1": _iact_analyze, "2": _iact_incremental, "3": _iact_list,
    "4": _iact_view_project, "5": _iact_view_portfolio, "6": _iact_view_resume,
    "7": _iact_generate, "8": _iact_edit_portfolio, "9": _iact_edit_resume,
    "10": _iact_skills, "11": _iact_set_role, "12": _iact_evidence,
    "13": _iact_thumbnail, "14": _iact_representation, "15": _iact_chronological,
    "16": _iact_delete, "17": _iact_start_api,
}


def _run_interactive() -> int:
    print(BANNER)
    while True:
        print(MAIN_MENU)
        choice = _inp("Select an option").strip()
        if choice == "0":
            print("  Goodbye!")
            return 0
        action = _INTERACTIVE_ACTIONS.get(choice)
        if action is None:
            print("  Invalid option.")
            continue
        try:
            action()
        except KeyboardInterrupt:
            print("\n  Interrupted. Returning to menu.")
        except Exception as exc:
            print(f"  Error: {exc}")


# ── Original argparse CLI (unchanged) ─────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    # No args → launch interactive mode
    if argv is None and len(sys.argv) == 1:
        return _run_interactive()

    parser = argparse.ArgumentParser(
        prog="python -m src.pipeline",
        description="Unified pipeline CLI for analysis, presentation, and display"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run the full artifact pipeline on a ZIP file"
    )
    analyze_parser.add_argument(
        "zip_path",
        help="Path to the ZIP file to analyze"
    )
    analyze_parser.add_argument(
        "--user-id",
        help="User ID for consent storage (default: $PIPELINE_USER_ID or current user)"
    )
    
    incremental_parser = subparsers.add_parser(
        "incremental",
        help="Merge a new ZIP file into an existing portfolio analysis"
    )
    incremental_parser.add_argument(
        "new_zip_path",
        help="Path to the new ZIP file to merge in"
    )
    incremental_parser.add_argument(
        "old_zip_hash",
        help="Hash of the existing ZIP analysis to update (from 'list')"
    )
    incremental_parser.add_argument(
        "--user-id",
        help="User ID (default: $PIPELINE_USER_ID or current OS user)"
    )

    present_parser = subparsers.add_parser(
        "present",
        help="Generate portfolio and resume items from stored project insights"
    )
    
    present_mode = present_parser.add_mutually_exclusive_group(required=True)
    present_mode.add_argument(
        "--project-id",
        type=int,
        help="Generate items for a single project by ID"
    )
    present_mode.add_argument(
        "--zip-hash",
        help="Zip hash for selecting projects"
    )
    present_mode.add_argument(
        "--all",
        action="store_true",
        help="Generate items for all projects"
    )
    
    present_parser.add_argument(
        "--project-name",
        help="Project name (required with --zip-hash for single project)"
    )
    present_parser.add_argument(
        "--all-in-zip",
        action="store_true",
        help="Generate items for all projects in the specified zip hash"
    )
    present_parser.add_argument(
        "--db-path",
        help="Path to insights database"
    )
    present_parser.add_argument(
        "--encryption-key-env",
        help="Environment variable name containing encryption key"
    )
    present_parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of projects (only for --all)"
    )
    
    portfolio_parser = subparsers.add_parser(
        "show-portfolio",
        help="Display human-friendly portfolio showcase for a project"
    )
    
    portfolio_mode = portfolio_parser.add_mutually_exclusive_group(required=True)
    portfolio_mode.add_argument(
        "--project-id",
        type=int,
        help="Project ID"
    )
    portfolio_mode.add_argument(
        "--zip-hash",
        help="Zip hash (requires --project-name)"
    )
    
    portfolio_parser.add_argument(
        "--project-name",
        help="Project name (required with --zip-hash)"
    )
    portfolio_parser.add_argument(
        "--db-path",
        help="Path to insights database"
    )
    portfolio_parser.add_argument(
        "--encryption-key-env",
        help="Environment variable name containing encryption key"
    )
    
    resume_parser = subparsers.add_parser(
        "show-resume",
        help="Display human-friendly resume item for a project"
    )
    
    resume_mode = resume_parser.add_mutually_exclusive_group(required=True)
    resume_mode.add_argument(
        "--project-id",
        type=int,
        help="Project ID"
    )
    resume_mode.add_argument(
        "--zip-hash",
        help="Zip hash (requires --project-name)"
    )
    
    resume_parser.add_argument(
        "--project-name",
        help="Project name (required with --zip-hash)"
    )
    resume_parser.add_argument(
        "--db-path",
        help="Path to insights database"
    )
    resume_parser.add_argument(
        "--encryption-key-env",
        help="Environment variable name containing encryption key"
    )
    
    list_parser = subparsers.add_parser(
        "list",
        help="List available projects from the insights database"
    )
    list_parser.add_argument(
        "--db-path",
        help="Path to insights database"
    )
    list_parser.add_argument(
        "--encryption-key-env",
        help="Environment variable name containing encryption key"
    )
    list_parser.add_argument(
        "--language",
        action="append",
        help="Filter by programming language (can be specified multiple times)"
    )
    list_parser.add_argument(
        "--framework",
        action="append",
        help="Filter by framework (can be specified multiple times)"
    )
    list_parser.add_argument(
        "--zip-path",
        help="Filter projects by ZIP file path"
    )
    list_parser.add_argument(
        "--zip-hash",
        help="Filter projects by ZIP hash"
    )

    delete_parser = subparsers.add_parser(
        "delete",
        help="Delete stored insights or user configurations",
        description=(
            "Delete stored insights and/or user configurations.\n\n"
            "Examples:\n"
            "  python -m src.pipeline delete all\n"
            "  python -m src.pipeline delete insight --project-id 1\n"
            "  python -m src.pipeline delete insight all\n"
            "  python -m src.pipeline delete config all\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    delete_parser.add_argument(
        "--db-path",
        help="Path to the database (default: data/app.db)"
    )
    delete_subparsers = delete_parser.add_subparsers(dest="delete_target", help="Delete target")

    delete_subparsers.add_parser(
        "all",
        help="Delete all insights and user configurations"
    )

    delete_insight_parser = delete_subparsers.add_parser(
        "insight",
        help="Delete insights by project id or delete all insights"
    )
    delete_insight_parser.add_argument(
        "--project-id",
        type=int,
        help="Project ID from `list`"
    )
    delete_insight_parser.add_argument(
        "scope",
        nargs="?",
        choices=["all"],
        help="Delete all insights"
    )

    delete_config_parser = delete_subparsers.add_parser(
        "config",
        help="Delete all user configurations"
    )
    delete_config_parser.add_argument(
        "scope",
        nargs="?",
        choices=["all"],
        help="Delete all user configurations"
    )
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "analyze":
            return handle_analyze(args)
        elif args.command == "incremental":
            return handle_incremental(args)
        elif args.command == "present":
            return handle_present(args)
        elif args.command == "show-portfolio":
            return handle_show_portfolio(args)
        elif args.command == "show-resume":
            return handle_show_resume(args)
        elif args.command == "list":
            return handle_list(args)
        elif args.command == "delete":
            return handle_delete(args)
        else:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def handle_analyze(args) -> int:
    """Handle the 'analyze' subcommand"""
    from src.pipeline.orchestrator import (
        ArtifactPipeline,
        resolve_data_access_consent,
        resolve_llm_consent
    )
    
    user_id = args.user_id or os.getenv("PIPELINE_USER_ID") or getpass.getuser() or "default"
    zip_path = args.zip_path
    data_consent = resolve_data_access_consent(zip_path, user_id)
    if not data_consent:
        print("✗ Data access consent not granted. Exiting.")
        return 0
    
    llm_consent = resolve_llm_consent(zip_path, user_id)
    print(f"\n🚀 Starting artifact pipeline for: {zip_path}")
    print(f"   User: {user_id}")
    print(f"   LLM: {'enabled' if llm_consent else 'disabled'}\n")
    
    pipeline = ArtifactPipeline()
    result = pipeline.start(zip_path, use_llm=llm_consent, data_access_consent=True)
    
    if not result:
        print("\n✓ Pipeline completed (no data to process)")
        return 0
    
    print("\n✅ Pipeline completed successfully!")
    
    return 0


def handle_incremental(args) -> int:
    """Handle the 'incremental' subcommand — merge a new ZIP into an existing analysis."""
    from src.pipeline.orchestrator import ArtifactPipeline
    from src.insights.storage import ProjectInsightsStore

    user_id = args.user_id or os.getenv("PIPELINE_USER_ID") or getpass.getuser() or "default"
    old_zip_hash: str = args.old_zip_hash
    new_zip_path: str = args.new_zip_path

    if not os.path.isfile(new_zip_path):
        print(f"✗ New ZIP file not found: {new_zip_path}", file=sys.stderr)
        return 1

    store = ProjectInsightsStore()
    old_projects = store.list_projects_for_zip(old_zip_hash)
    if not old_projects:
        print(f"✗ No existing analysis found for zip_hash: {old_zip_hash}", file=sys.stderr)
        return 1

    print(f"\n🔄 Incremental update")
    print(f"   User         : {user_id}")
    print(f"   Old ZIP hash : {old_zip_hash[:16]}...")
    print(f"   New ZIP      : {new_zip_path}\n")

    pipeline = ArtifactPipeline(insights_store=store)
    merge_summary = pipeline.incremental_update(
        new_zip_path=new_zip_path,
        old_zip_hash=old_zip_hash,
    )

    if merge_summary.get("status") == "cancelled":
        print(f"\n✗ Update cancelled: {merge_summary.get('message', '')}")
        return 1

    print(f"\n✅ Incremental update complete!")
    print(f"   New ZIP hash      : {merge_summary.get('new_zip_hash', 'N/A')}")
    print(f"   New projects      : {merge_summary.get('new_only_projects', [])}")
    print(f"   Retained projects : {merge_summary.get('retained_projects', [])}")
    print(f"   Updated projects  : {merge_summary.get('updated_projects', [])}")
    print(f"   Total projects    : {merge_summary.get('total_projects', 0)}")
    return 0


def handle_present(args) -> int:
    """Handle the 'present' subcommand"""
    from src.pipeline.presentation_pipeline import PresentationPipeline
    
    encryption_key = None
    if args.encryption_key_env:
        key_str = os.getenv(args.encryption_key_env)
        if key_str:
            encryption_key = key_str.encode('utf-8')
    
    # Initialize pipeline
    pipeline = PresentationPipeline(
        db_path=args.db_path,
        encryption_key=encryption_key
    )
    
    if args.project_id:
        result = pipeline.generate_by_id(args.project_id, regenerate=True)
        print_single_result(result)
        return 0 if result.success else 1
    
    elif args.zip_hash and args.project_name:
        result = pipeline.generate_by_name(args.zip_hash, args.project_name, regenerate=True)
        print_single_result(result)
        return 0 if result.success else 1
    
    elif args.zip_hash and args.all_in_zip:
        result = pipeline.generate_for_zip(args.zip_hash, regenerate=True)
        print_batch_result(result)
        return 0 if result.failed == 0 else 1
    
    elif args.all:
        result = pipeline.generate_all(regenerate=True, limit=args.limit)
        print_batch_result(result)
        return 0 if result.failed == 0 else 1
    
    else:
        print("Error: Invalid argument combination for 'present'", file=sys.stderr)
        return 1


def handle_show_portfolio(args) -> int:
    """Handle the 'show-portfolio' subcommand"""
    from src.pipeline.presentation_pipeline import PresentationPipeline
    
    if args.zip_hash and not args.project_name:
        print("Error: --zip-hash requires --project-name", file=sys.stderr)
        return 1
    
    # Get encryption key if specified
    encryption_key = None
    if args.encryption_key_env:
        key_str = os.getenv(args.encryption_key_env)
        if key_str:
            encryption_key = key_str.encode('utf-8')
    
    # Initialize pipeline
    pipeline = PresentationPipeline(
        db_path=args.db_path,
        encryption_key=encryption_key
    )
    
    # Generate items
    if args.project_id:
        result = pipeline.generate_by_id(args.project_id, regenerate=True)
    else:
        result = pipeline.generate_by_name(args.zip_hash, args.project_name, regenerate=True)
    
    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    
    format_portfolio(result.portfolio_item)
    return 0


def handle_show_resume(args) -> int:
    """Handle the 'show-resume' subcommand"""
    from src.pipeline.presentation_pipeline import PresentationPipeline
    
    if args.zip_hash and not args.project_name:
        print("Error: --zip-hash requires --project-name", file=sys.stderr)
        return 1
    
    # Get encryption key if specified
    encryption_key = None
    if args.encryption_key_env:
        key_str = os.getenv(args.encryption_key_env)
        if key_str:
            encryption_key = key_str.encode('utf-8')
    
    # Initialize pipeline
    pipeline = PresentationPipeline(
        db_path=args.db_path,
        encryption_key=encryption_key
    )
    
    # Generate items
    if args.project_id:
        result = pipeline.generate_by_id(args.project_id, regenerate=True)
    else:
        result = pipeline.generate_by_name(args.zip_hash, args.project_name, regenerate=True)
    
    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    
    format_resume(result.resume_item)
    return 0


def handle_list(args) -> int:
    """Handle the 'list' subcommand"""
    from src.pipeline.presentation_pipeline import PresentationPipeline
    
    encryption_key = None
    if hasattr(args, 'encryption_key_env') and args.encryption_key_env:
        key_str = os.getenv(args.encryption_key_env)
        if key_str:
            encryption_key = key_str.encode('utf-8')
    
    pipeline = PresentationPipeline(db_path=getattr(args, 'db_path', None), encryption_key=encryption_key)
    
    # Apply filters if specified
    filters = {}
    if hasattr(args, 'language') and args.language:
        filters['languages'] = args.language
    if hasattr(args, 'framework') and args.framework:
        filters['frameworks'] = args.framework
    if hasattr(args, 'zip_path') and args.zip_path:
        filters['zip_path'] = args.zip_path
    if hasattr(args, 'zip_hash') and args.zip_hash:
        filters['zip_hash'] = args.zip_hash
    
    projects = pipeline.list_available_projects(filters=filters if filters else None)
    
    if not projects:
        filter_msg = ""
        if filters:
            filter_parts = []
            if 'languages' in filters:
                filter_parts.append(f"languages: {', '.join(filters['languages'])}")
            if 'frameworks' in filters:
                filter_parts.append(f"frameworks: {', '.join(filters['frameworks'])}")
            if 'zip_path' in filters:
                filter_parts.append(f"zip_path: {filters['zip_path']}")
            if 'zip_hash' in filters:
                filter_parts.append(f"zip_hash: {filters['zip_hash']}")
            filter_msg = f" (filtered by {'; '.join(filter_parts)})"
        print(f"\nNo projects found in database{filter_msg}.\n")
        return 0
    
    filter_info = ""
    if filters:
        filter_parts = []
        if 'languages' in filters:
            filter_parts.append(f"Language: {', '.join(filters['languages'])}")
        if 'frameworks' in filters:
            filter_parts.append(f"Framework: {', '.join(filters['frameworks'])}")
        if 'zip_path' in filters:
            filter_parts.append(f"Zip Path: {filters['zip_path']}")
        if 'zip_hash' in filters:
            filter_parts.append(f"Zip Hash: {filters['zip_hash']}")
        filter_info = f" [Filtered by {' | '.join(filter_parts)}]"
    
    print(f"\n{'='*100}")
    print(f"Available Projects ({len(projects)} total){filter_info}")
    print(f"{'='*100}\n")
    print(f"{'ID':<6} | {'Project Name':<30} | {'Zip Hash':<12} | {'Code':<5} | {'Docs':<5} | {'Git':<4} | {'Updated'}")
    print(f"{'-'*6}-+-{'-'*30}-+-{'-'*12}-+-{'-'*5}-+-{'-'*5}-+-{'-'*4}-+-{'-'*19}")
    
    for proj in projects:
        zip_short = proj['zip_hash'][:12] if proj['zip_hash'] else 'N/A'
        name_short = proj['project_name'][:30] if proj['project_name'] else 'N/A'
        git_status = 'Yes' if proj['is_git_repo'] else 'No'
        updated = proj.get('updated_at', 'N/A')[:19]
        
        print(
            f"{proj['project_id']:<6} | {name_short:<30} | {zip_short:<12} | "
            f"{proj['code_files']:<5} | {proj['doc_files']:<5} | {git_status:<4} | {updated}"
        )
    
    print(f"\n{'='*100}\n")
    return 0


def handle_delete(args) -> int:
    """Handle the 'delete' subcommand."""
    from src.insights.storage import DEFAULT_DB_PATH, ProjectInsightsStore

    if not args.delete_target:
        print("Error: Missing delete target. Use 'delete -h' for options.", file=sys.stderr)
        return 1

    db_path = args.db_path or DEFAULT_DB_PATH

    if args.delete_target == "all":
        if not confirm_action(
            "Are you sure you want to delete all insights and user configurations? This cannot be undone."
        ):
            print("Cancelled.")
            return 0
        insights_store = ProjectInsightsStore(db_path=db_path)
        insights_counts = insights_store.delete_all()
        configs_deleted = delete_user_configurations_all(db_path)
        print(f"Deleted projects: {insights_counts.get('deleted_projects', 0)}")
        print(f"Deleted user configurations: {configs_deleted}")
        return 0

    if args.delete_target == "insight":
        if args.project_id and args.scope:
            print("Error: Use either --project-id or 'all' for delete insight.", file=sys.stderr)
            return 1
        if not args.project_id and args.scope != "all":
            print("Error: Provide --project-id or 'all' for delete insight.", file=sys.stderr)
            return 1

        if args.scope == "all":
            if not confirm_action(
                "Are you sure you want to delete all insights? This cannot be undone."
            ):
                print("Cancelled.")
                return 0
            insights_store = ProjectInsightsStore(db_path=db_path)
            insights_counts = insights_store.delete_all()
            print(f"Deleted projects: {insights_counts.get('deleted_projects', 0)}")
            print(f"Deleted zips: {insights_counts.get('deleted_zips', 0)}")
            return 0

        if not confirm_action(
            f"Are you sure you want to delete insights for project id {args.project_id}? This cannot be undone."
        ):
            print("Cancelled.")
            return 0
        insights_counts = delete_insights_for_project_id(db_path, args.project_id)
        print(f"Deleted projects: {insights_counts.get('deleted_projects', 0)}")
        print(f"Deleted zips: {insights_counts.get('deleted_zips', 0)}")
        return 0

    if args.delete_target == "config":
        if args.scope != "all":
            print("Error: Use 'all' for delete config.", file=sys.stderr)
            return 1
        if not confirm_action(
            "Are you sure you want to delete all user configurations? This cannot be undone."
        ):
            print("Cancelled.")
            return 0
        configs_deleted = delete_user_configurations_all(db_path)
        print(f"Deleted user configurations: {configs_deleted}")
        return 0

    print(f"Unknown delete target: {args.delete_target}", file=sys.stderr)
    return 1


def confirm_action(prompt: str) -> bool:
    """Prompt user for confirmation before destructive actions."""
    try:
        response = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return response in {"y", "yes"}


def delete_user_configurations_all(db_path: str) -> int:
    """Delete all rows in user_configurations. Returns number of deleted rows."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        if not table_exists(conn, "user_configurations"):
            return 0
        conn.execute("DELETE FROM user_configurations;")
        conn.commit()
        return conn.execute("SELECT changes();").fetchone()[0]


def delete_insights_for_project_id(db_path: str, project_info_id: int) -> Dict[str, int]:
    """Delete insights for a single project_info id. Returns counts."""
    from src.insights.storage import PROJECT_INFO_TABLE, PROJECTS_TABLE, INGEST_TABLE

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        if not table_exists(conn, PROJECT_INFO_TABLE):
            return {"deleted_projects": 0, "deleted_zips": 0}
        conn.isolation_level = None
        conn.execute("BEGIN IMMEDIATE;")
        try:
            row = conn.execute(
                f"SELECT project_id, ingest_id FROM {PROJECT_INFO_TABLE} WHERE id = ?;",
                (project_info_id,),
            ).fetchone()
            if not row:
                conn.execute("ROLLBACK;")
                return {"deleted_projects": 0, "deleted_zips": 0}

            project_id, ingest_id = row
            conn.execute(f"DELETE FROM {PROJECT_INFO_TABLE} WHERE id = ?;", (project_info_id,))
            deleted_projects = conn.execute("SELECT changes();").fetchone()[0]

            remaining_for_project = conn.execute(
                f"SELECT COUNT(*) FROM {PROJECT_INFO_TABLE} WHERE project_id = ?;",
                (project_id,),
            ).fetchone()[0]
            if remaining_for_project == 0:
                conn.execute(f"DELETE FROM {PROJECTS_TABLE} WHERE id = ?;", (project_id,))

            remaining_for_ingest = conn.execute(
                f"SELECT COUNT(*) FROM {PROJECT_INFO_TABLE} WHERE ingest_id = ?;",
                (ingest_id,),
            ).fetchone()[0]
            deleted_zips = 0
            if remaining_for_ingest == 0:
                conn.execute(f"DELETE FROM {INGEST_TABLE} WHERE id = ?;", (ingest_id,))
                deleted_zips = 1

            conn.execute("COMMIT;")
            return {"deleted_projects": deleted_projects, "deleted_zips": deleted_zips}
        except Exception:
            conn.execute("ROLLBACK;")
            raise


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?;",
        (table_name,),
    ).fetchone()
    return bool(row)


def print_single_result(result) -> None:
    """Print a single PresentationResult as compact JSON"""
    print("\n" + "="*70)
    print("PRESENTATION RESULT")
    print("="*70)
    print(json.dumps(result.to_dict(), indent=2))
    print("="*70 + "\n")


def print_batch_result(result) -> None:
    """Print a BatchPresentationResult with summary"""
    print("\n" + "="*70)
    print("BATCH PRESENTATION RESULTS")
    print("="*70)
    print(f"Total Processed: {result.total_processed}")
    print(f"Successful: {result.successful}")
    print(f"Failed: {result.failed}")
    
    if result.successful > 0:
        print("\nSuccessful Projects:")
        for r in result.results:
            if r.success:
                print(f"  ✓ {r.project_name} (ID: {r.project_id})")
    
    if result.failed > 0:
        print("\nFailed Projects:")
        for r in result.results:
            if not r.success:
                print(f"  ✗ {r.project_name} (ID: {r.project_id}): {r.error}")
    
    print("="*70 + "\n")


def format_portfolio(portfolio_item: Dict[str, Any]) -> None:
    """Format and print a portfolio item in human-friendly format"""
    print("\n" + "="*70)
    print("PORTFOLIO SHOWCASE")
    print("="*70 + "\n")
    
    print(f"Project Name: {portfolio_item.get('project_name', 'N/A')}")
    print(f"Tagline: {portfolio_item.get('tagline', 'N/A')}")
    print(f"\nDescription:")
    print(f"  {portfolio_item.get('description', 'N/A')}")
    
    languages = portfolio_item.get('languages', [])
    if languages:
        print(f"\nLanguages: {', '.join(languages)}")
    
    frameworks = portfolio_item.get('frameworks', [])
    if frameworks:
        print(f"Frameworks: {', '.join(frameworks)}")
    
    skills = portfolio_item.get('skills', [])
    if skills:
        print(f"Skills: {', '.join(skills)}")
    
    key_features = portfolio_item.get('key_features', [])
    if key_features:
        print(f"\nKey Features:")
        for feature in key_features:
            print(f"  • {feature}")
    
    is_collab = portfolio_item.get('is_collaborative', False)
    commits = portfolio_item.get('total_commits', 0)
    loc = portfolio_item.get('total_lines', 0)
    
    print(f"\nMetrics:")
    print(f"  Collaboration: {'Yes' if is_collab else 'No'}")
    if commits > 0:
        print(f"  Commits: {commits}")
    if loc > 0:
        print(f"  Lines of Code: {loc:,}")
    
    print("\n" + "="*70 + "\n")


def format_resume(resume_item: Dict[str, Any]) -> None:
    """Format and print a resume item in human-friendly format"""
    print("\n" + "="*70)
    print("RESUME ITEM")
    print("="*70 + "\n")
    
    print(f"Project Name: {resume_item.get('project_name', 'N/A')}")
    print("\nBullets:")
    
    bullets = resume_item.get('bullets', [])
    for bullet in bullets:
        print(f"  • {bullet}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

"""
    chronological_skills.py
---
    Generates a chronological timeline of detected skills based on file
    modification times. Integrates with CodeAnalyzer to infer skills from
    code content and uses file metadata to order discoveries in time.

---
    Run from root directory with:
        docker compose run --rm backend python3 -m src.analyze.chronological_skills    
"""

from datetime import datetime
from pathlib import Path
from typing import List, Dict
from src.analyze.code_analyzer import CodeAnalyzer, AnalysisResult


class ChronologicalSkillList:
    def __init__(self):
        self.analyzer = CodeAnalyzer()

    def build_skill_timeline(self, directory_path: str) -> List[Dict]:
        """
        Analyze a directory and generate a chronological timeline of skill emergence.
        """
        results = self.analyzer.analyze_directory(directory_path)
        skill_events = []

        for r in results:
            file_path = Path(r.file_path)
            try:
                timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
            except Exception:
                timestamp = datetime.now()

            skill_events.append({
                "file": str(file_path),
                "timestamp": timestamp,
                "skills": sorted(r.skills),
                "language": r.language,
                "frameworks": r.frameworks
            })

        # Sort events by modification time
        skill_events.sort(key=lambda e: e["timestamp"])
        return skill_events

    def summarize_evolution(self, events: List[Dict]) -> List[Dict]:
        """
        Produce a high-level summary showing when new skills first appeared.
        """
        seen_skills = set()
        timeline = []

        for e in events:
            new_skills = [s for s in e["skills"] if s not in seen_skills]
            if new_skills:
                timeline.append({
                    "date": e["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "new_skills": new_skills,
                    "source_file": e["file"]
                })
                seen_skills.update(new_skills)

        return timeline

# if __name__ == "__main__":
#     from pprint import pprint

#     skill_builder = ChronologicalSkillList()
#     directory = "tests/categorize/demo_projects"

#     print("\n=== Building Skill Timeline ===\n")
#     events = skill_builder.build_skill_timeline(directory)
#     timeline = skill_builder.summarize_evolution(events)

#     pprint(timeline)
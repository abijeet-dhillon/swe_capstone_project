from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import re


class ProjectComparison:
    def compare_projects(self, projects: List[Dict[str, Any]], user_id: Optional[str] = None) -> Dict[str, Any]:
        if len(projects) < 2:
            return {"error": "Need at least 2 projects to compare"}
        
        sorted_projects = sorted(projects, key=lambda p: p.get('created_at', p.get('first_commit', '2000-01-01')))
        
        return {
            "summary": self._summary(sorted_projects),
            "skill_evolution": self._skill_evolution(sorted_projects),
            "quality_progression": self._quality(sorted_projects),
            "testing_maturity": self._testing(sorted_projects),
            "collaboration_growth": self._collaboration(sorted_projects),
            "recommendations": self._recommendations(sorted_projects),
            "growth_score": self._growth_score(sorted_projects),
        }
    
    def compare_two(self, p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, Any]:
        skills1, skills2 = set(p1.get('key_skills', [])), set(p2.get('key_skills', []))
        score1, score2 = self._score(p1), self._score(p2)
        
        return {
            "project_1": p1.get('project_name'),
            "project_2": p2.get('project_name'),
            "skill_diff": {"added": list(skills2 - skills1), "removed": list(skills1 - skills2), "common": list(skills1 & skills2)},
            "size_diff": {"lines": p2.get('total_lines', 0) - p1.get('total_lines', 0), "files": p2.get('total_files', 0) - p1.get('total_files', 0)},
            "quality_diff": {"tests": p2.get('test_files', 0) - p1.get('test_files', 0), "docs": p2.get('documentation_files', 0) - p1.get('documentation_files', 0)},
            "winner": "tie" if abs(score1 - score2) < 5 else (p1.get('project_name') if score1 > score2 else p2.get('project_name')),
        }
    
    def _score(self, p: Dict[str, Any]) -> float:
        return len(p.get('key_skills', [])) * 5 + p.get('test_files', 0) * 3 + p.get('total_commits', 0) * 0.1
    
    def _summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        langs = self._extract_langs(projects)
        frameworks = self._extract_frameworks(projects)
        first, last = projects[0], projects[-1]
        
        return {
            "total_projects": len(projects),
            "time_span": f"{first.get('created_at', '')} to {last.get('created_at', '')}",
            "languages": langs,
            "frameworks": frameworks,
            "total_commits": sum(p.get('total_commits', 0) for p in projects),
            "total_lines": sum(p.get('total_lines', 0) for p in projects),
            "avg_project_size": sum(p.get('total_lines', 0) for p in projects) // len(projects),
            "earliest_project": first.get('project_name'),
            "latest_project": last.get('project_name'),
        }
    
    def _skill_evolution(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        timeline = defaultdict(list)
        
        for idx, p in enumerate(projects):
            for skill in p.get('key_skills', []):
                timeline[skill].append({'project': p.get('project_name'), 'index': idx})
        
        new_skills = [s for s, occ in timeline.items() if len(occ) == 1 and occ[0]['index'] == len(projects) - 1]
        consistent = [s for s, occ in timeline.items() if len(occ) >= len(projects) * 0.6]
        
        insights = []
        if new_skills:
            insights.append(f"Recently learned: {', '.join(new_skills[:3])}")
        if consistent:
            insights.append(f"Core skills: {', '.join(consistent[:3])}")
        
        return {"skill_timeline": {k: len(v) for k, v in timeline.items()}, "new_skills": new_skills, "consistent_skills": consistent, "insights": insights}
    
    def _quality(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        metrics = []
        
        for p in projects:
            doc_ratio = (p.get('documentation_files', 0) / max(p.get('total_files', 1), 1)) * 100
            test_ratio = (p.get('test_files', 0) / max(p.get('code_files', 1), 1)) * 100
            complexity = p.get('complexity_score', 50)
            score = doc_ratio * 0.3 + test_ratio * 0.4 + (100 - complexity) * 0.3
            
            metrics.append({'project': p.get('project_name'), 'quality_score': score, 'test_ratio': test_ratio})
        
        improvement = 0
        trend = "insufficient_data"
        if len(metrics) >= 2:
            first, last = metrics[0]['quality_score'], metrics[-1]['quality_score']
            improvement = ((last - first) / first) * 100 if first > 0 else 0
            trend = "improving" if improvement > 10 else "declining" if improvement < -10 else "stable"
        
        return {"metrics": metrics, "improvement_percentage": improvement, "trend": trend}
    
    def _testing(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        progression = []
        
        for p in projects:
            ratio = (p.get('test_files', 0) / max(p.get('total_files', 1), 1)) * 100
            maturity = "none" if ratio == 0 else "basic" if ratio < 10 else "moderate" if ratio < 30 else "comprehensive"
            progression.append({'project': p.get('project_name'), 'test_ratio': ratio, 'maturity': maturity})
        
        levels = [p['maturity'] for p in progression]
        insight = "Testing evolved significantly" if 'none' in levels[:2] and 'comprehensive' in levels[-2:] else "Strong testing practices" if levels[-1] in ['comprehensive', 'moderate'] else "Testing needs improvement"
        
        return {"progression": progression, "current_maturity": levels[-1] if levels else "unknown", "insight": insight}
    
    def _collaboration(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        solo = sum(1 for p in projects if not p.get('is_collaborative', len(p.get('contributors', [])) > 1))
        team = len(projects) - solo
        
        insight = "Primarily independent work" if solo > team else "Strong collaborative experience" if team > solo * 2 else "Balanced solo and team experience"
        
        return {"solo_projects": solo, "collaborative_projects": team, "collaboration_ratio": team / len(projects), "insight": insight}
    
    def _recommendations(self, projects: List[Dict[str, Any]]) -> List[str]:
        recs = []
        
        if len(self._extract_langs(projects)) < 3:
            recs.append("💡 Add projects in different languages")
        
        has_backend = any(p.get('language') in ['Python', 'Java', 'Go'] for p in projects)
        has_frontend = any(p.get('framework') in ['React', 'Vue', 'Angular'] for p in projects)
        if not (has_backend and has_frontend):
            recs.append("💡 Add full-stack project")
        
        avg_tests = sum((p.get('test_files', 0) / max(p.get('code_files', 1), 1)) * 100 for p in projects) / len(projects)
        if avg_tests < 20:
            recs.append("💡 Increase test coverage")
        
        if projects[-1].get('created_at', '') < '2024-01-01':
            recs.append("💡 Add recent projects")
        
        return recs or ["✨ Strong portfolio!"]
    
    def _growth_score(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(projects) < 2:
            return {"score": 0, "rating": "insufficient_data"}
        
        first, last = projects[0], projects[-1]
        size_growth = (last.get('total_lines', 0) / max(first.get('total_lines', 1), 1)) - 1
        test_growth = last.get('test_files', 0) - first.get('test_files', 0)
        skill_growth = len(last.get('key_skills', [])) - len(first.get('key_skills', []))
        
        score = min(100, max(0, size_growth * 20 + test_growth * 5 + skill_growth * 10 + 30))
        rating = "exceptional" if score >= 80 else "strong" if score >= 60 else "moderate" if score >= 40 else "needs_focus"
        
        return {
            "score": round(score, 1),
            "rating": rating,
            "message": f"Portfolio shows {rating} growth",
            "factors": {"size_growth": round(size_growth * 100, 1), "test_growth": test_growth, "skill_growth": skill_growth}
        }
    
    def _extract_langs(self, projects: List[Dict[str, Any]]) -> List[str]:
        langs = set()
        lang_keywords = ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust', 'TypeScript', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin']
        for p in projects:
            if p.get('language'):
                langs.add(p['language'])
            langs.update(s for s in p.get('key_skills', []) if s in lang_keywords)
        return sorted(list(langs))
    
    def _extract_frameworks(self, projects: List[Dict[str, Any]]) -> List[str]:
        frameworks = set()
        fw_keywords = ['Django', 'Flask', 'React', 'Vue', 'Angular', 'Express', 'Spring', 'Rails', 'Laravel']
        for p in projects:
            if p.get('framework'):
                frameworks.add(p['framework'])
            frameworks.update(s for s in p.get('key_skills', []) if s in fw_keywords)
        return sorted(list(frameworks))


def match_to_job_description(projects: List[Dict[str, Any]], job_desc: str) -> List[Tuple[str, float, str]]:
    job_lower = job_desc.lower()
    keywords = set(re.findall(r'\b\w{4,}\b', job_lower))
    tech = {'python', 'java', 'javascript', 'react', 'django', 'flask', 'api', 'rest', 'sql', 'docker', 'kubernetes', 'testing', 'git', 'vue', 'angular'}
    
    scored = []
    for p in projects:
        score = 0
        matched = []
        
        for skill in [s.lower() for s in p.get('key_skills', [])]:
            if skill in job_lower:
                score += 10
                matched.append(skill)
            if skill in tech and skill in keywords:
                score += 5
        
        desc = (p.get('description', '') + ' ' + p.get('project_name', '')).lower()
        score += sum(2 for kw in keywords if kw in desc)
        
        if p.get('created_at', '') > '2023-01-01':
            score += 5
        if p.get('is_collaborative') and any(kw in job_lower for kw in ['team', 'collaborate', 'agile']):
            score += 3
        
        reason = f"Matches: {', '.join(matched[:3])}" if matched else "General fit"
        scored.append((p.get('project_name', 'Unknown'), score, reason))
    
    return sorted(scored, key=lambda x: x[1], reverse=True)

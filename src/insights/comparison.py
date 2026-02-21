from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import re


class ProjectComparison:
    def __init__(self):
        self.insights = []
    
    def compare_projects(self, projects: List[Dict[str, Any]], user_id: Optional[str] = None) -> Dict[str, Any]:
        if len(projects) < 2:
            return {"error": "Need at least 2 projects to compare"}
        
        sorted_projects = sorted(projects, key=lambda p: p.get('created_at', p.get('first_commit', '2000-01-01')))
        
        return {
            "summary": self._generate_summary(sorted_projects),
            "skill_evolution": self._analyze_skill_evolution(sorted_projects),
            "quality_progression": self._analyze_quality_progression(sorted_projects),
            "testing_maturity": self._analyze_testing_maturity(sorted_projects),
            "collaboration_growth": self._analyze_collaboration(sorted_projects),
            "recommendations": self._generate_recommendations(sorted_projects),
            "growth_score": self._calculate_growth_score(sorted_projects),
        }
    
    def compare_two(self, project1: Dict[str, Any], project2: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "project_1": project1.get('project_name'),
            "project_2": project2.get('project_name'),
            "skill_diff": self._skill_difference(project1, project2),
            "size_diff": {
                "lines": project2.get('total_lines', 0) - project1.get('total_lines', 0),
                "files": project2.get('total_files', 0) - project1.get('total_files', 0),
            },
            "quality_diff": {
                "tests": project2.get('test_files', 0) - project1.get('test_files', 0),
                "docs": project2.get('documentation_files', 0) - project1.get('documentation_files', 0),
            },
            "winner": self._determine_winner(project1, project2),
        }
    
    def _skill_difference(self, p1: Dict[str, Any], p2: Dict[str, Any]) -> Dict[str, List[str]]:
        skills1 = set(p1.get('key_skills', []))
        skills2 = set(p2.get('key_skills', []))
        return {
            "added": list(skills2 - skills1),
            "removed": list(skills1 - skills2),
            "common": list(skills1 & skills2),
        }
    
    def _determine_winner(self, p1: Dict[str, Any], p2: Dict[str, Any]) -> str:
        score1 = self._project_score(p1)
        score2 = self._project_score(p2)
        if abs(score1 - score2) < 5:
            return "tie"
        return p1.get('project_name') if score1 > score2 else p2.get('project_name')
    
    def _project_score(self, project: Dict[str, Any]) -> float:
        return (
            len(project.get('key_skills', [])) * 5 +
            project.get('test_files', 0) * 3 +
            project.get('total_commits', 0) * 0.1
        )
    
    def _generate_summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        all_langs = self._extract_all_languages(projects)
        all_frameworks = self._extract_all_frameworks(projects)
        
        return {
            "total_projects": len(projects),
            "time_span": self._calculate_time_span(projects),
            "languages": all_langs,
            "languages_count": len(all_langs),
            "frameworks": all_frameworks,
            "total_commits": sum(p.get('total_commits', 0) for p in projects),
            "total_lines": sum(p.get('total_lines', 0) for p in projects),
            "avg_project_size": sum(p.get('total_lines', 0) for p in projects) // len(projects),
            "earliest_project": projects[0].get('project_name'),
            "latest_project": projects[-1].get('project_name'),
        }
    
    def _calculate_time_span(self, projects: List[Dict[str, Any]]) -> str:
        if len(projects) < 2:
            return "N/A"
        first_date = projects[0].get('created_at', projects[0].get('first_commit'))
        last_date = projects[-1].get('created_at', projects[-1].get('last_commit'))
        if first_date and last_date:
            return f"{first_date} to {last_date}"
        return "Unknown"
    
    def _analyze_skill_evolution(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        skill_timeline = defaultdict(list)
        
        for idx, project in enumerate(projects):
            skills = project.get('key_skills', []) or project.get('skills', [])
            timestamp = project.get('created_at', project.get('first_commit'))
            for skill in skills:
                skill_timeline[skill].append({
                    'project': project.get('project_name'),
                    'index': idx,
                    'timestamp': timestamp,
                })
        
        new_skills = [s for s, occ in skill_timeline.items() if len(occ) == 1 and occ[0]['index'] == len(projects) - 1]
        consistent_skills = [s for s, occ in skill_timeline.items() if len(occ) >= len(projects) * 0.6]
        abandoned_skills = [s for s, occ in skill_timeline.items() if len(occ) >= 2 and occ[-1]['index'] < len(projects) - 2]
        
        insights = []
        if new_skills:
            insights.append(f"Recently learned: {', '.join(new_skills[:3])}")
        if consistent_skills:
            insights.append(f"Core skills: {', '.join(consistent_skills[:3])}")
        
        return {
            "skill_timeline": {k: len(v) for k, v in skill_timeline.items()},
            "new_skills": new_skills,
            "consistent_skills": consistent_skills,
            "abandoned_skills": abandoned_skills,
            "insights": insights,
        }
    
    def _analyze_quality_progression(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        quality_metrics = []
        
        for project in projects:
            doc_ratio = self._calculate_doc_ratio(project)
            test_ratio = self._calculate_test_ratio(project)
            complexity = project.get('complexity_score', 50)
            quality_score = (doc_ratio * 0.3 + test_ratio * 0.4 + (100 - complexity) * 0.3)
            
            quality_metrics.append({
                'project': project.get('project_name'),
                'quality_score': quality_score,
                'documentation_ratio': doc_ratio,
                'test_ratio': test_ratio,
                'complexity': complexity,
            })
        
        if len(quality_metrics) >= 2:
            first_score = quality_metrics[0]['quality_score']
            last_score = quality_metrics[-1]['quality_score']
            improvement = ((last_score - first_score) / first_score) * 100 if first_score > 0 else 0
            trend = "improving" if improvement > 10 else "declining" if improvement < -10 else "stable"
        else:
            improvement = 0
            trend = "insufficient_data"
        
        insights = []
        if improvement > 20:
            insights.append(f"Code quality improved {improvement:.1f}% over time")
        if quality_metrics[-1]['test_ratio'] > 30:
            insights.append("Strong testing practices in recent projects")
        if quality_metrics[-1]['documentation_ratio'] > 20:
            insights.append("Well-documented recent projects")
        
        return {
            "metrics": quality_metrics,
            "improvement_percentage": improvement,
            "trend": trend,
            "insights": insights,
        }
    
    def _analyze_testing_maturity(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        test_progression = []
        
        for project in projects:
            test_files = project.get('test_files', 0)
            total_files = project.get('total_files', 1)
            test_ratio = (test_files / total_files * 100) if total_files > 0 else 0
            
            if test_ratio == 0:
                maturity = "none"
            elif test_ratio < 10:
                maturity = "basic"
            elif test_ratio < 30:
                maturity = "moderate"
            else:
                maturity = "comprehensive"
            
            test_progression.append({
                'project': project.get('project_name'),
                'test_ratio': test_ratio,
                'test_files': test_files,
                'maturity': maturity,
            })
        
        maturity_levels = [p['maturity'] for p in test_progression]
        if 'none' in maturity_levels[:2] and 'comprehensive' in maturity_levels[-2:]:
            insight = "Testing practices evolved from none to comprehensive"
        elif maturity_levels[-1] in ['comprehensive', 'moderate']:
            insight = "Maintains strong testing practices"
        else:
            insight = "Testing practices could be improved"
        
        return {
            "progression": test_progression,
            "current_maturity": maturity_levels[-1] if maturity_levels else "unknown",
            "insight": insight,
        }
    
    def _analyze_collaboration(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        collab_data = []
        
        for project in projects:
            contributors = project.get('contributors', [])
            is_collaborative = project.get('is_collaborative', len(contributors) > 1)
            
            collab_data.append({
                'project': project.get('project_name'),
                'contributors': len(contributors),
                'is_collaborative': is_collaborative,
            })
        
        solo_count = sum(1 for p in collab_data if not p['is_collaborative'])
        team_count = len(collab_data) - solo_count
        
        insight = ""
        if solo_count > team_count:
            insight = "Primarily independent work"
        elif team_count > solo_count * 2:
            insight = "Strong collaborative experience"
        else:
            insight = "Balanced solo and team experience"
        
        return {
            "solo_projects": solo_count,
            "collaborative_projects": team_count,
            "collaboration_ratio": team_count / len(collab_data) if collab_data else 0,
            "insight": insight,
        }
    
    def _generate_recommendations(self, projects: List[Dict[str, Any]]) -> List[str]:
        recommendations = []
        
        languages = self._extract_all_languages(projects)
        if len(languages) < 3:
            recommendations.append("💡 Add projects in different languages to show versatility")
        
        has_backend = any('backend' in str(p.get('description', '')).lower() or 
                         p.get('language') in ['Python', 'Java', 'Go', 'Node.js']
                         for p in projects)
        has_frontend = any('frontend' in str(p.get('description', '')).lower() or
                          p.get('framework') in ['React', 'Vue', 'Angular']
                          for p in projects)
        
        if not (has_backend and has_frontend):
            recommendations.append("💡 Add full-stack project to demonstrate end-to-end skills")
        
        avg_test_ratio = sum(self._calculate_test_ratio(p) for p in projects) / len(projects)
        if avg_test_ratio < 20:
            recommendations.append("💡 Increase test coverage to demonstrate quality focus")
        
        avg_doc_ratio = sum(self._calculate_doc_ratio(p) for p in projects) / len(projects)
        if avg_doc_ratio < 15:
            recommendations.append("💡 Add more documentation to showcase communication skills")
        
        if projects:
            latest_date = projects[-1].get('created_at', projects[-1].get('last_commit', ''))
            if latest_date and latest_date < '2024-01-01':
                recommendations.append("💡 Add recent projects to show current activity")
        
        return recommendations or ["✨ Strong portfolio across all metrics!"]
    
    def _calculate_growth_score(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(projects) < 2:
            return {"score": 0, "rating": "insufficient_data"}
        
        first = projects[0]
        last = projects[-1]
        
        size_growth = (last.get('total_lines', 0) / max(first.get('total_lines', 1), 1)) - 1
        test_growth = last.get('test_files', 0) - first.get('test_files', 0)
        skill_growth = len(last.get('key_skills', [])) - len(first.get('key_skills', []))
        
        score = min(100, max(0, (size_growth * 20) + (test_growth * 5) + (skill_growth * 10) + 30))
        
        if score >= 80:
            rating = "exceptional"
            message = "Portfolio shows exceptional growth trajectory"
        elif score >= 60:
            rating = "strong"
            message = "Portfolio shows strong growth trajectory"
        elif score >= 40:
            rating = "moderate"
            message = "Portfolio shows moderate growth trajectory"
        else:
            rating = "needs_focus"
            message = "Portfolio growth could be stronger"
        
        return {
            "score": round(score, 1),
            "rating": rating,
            "message": message,
            "factors": {
                "size_growth": round(size_growth * 100, 1),
                "test_growth": test_growth,
                "skill_growth": skill_growth,
            }
        }
    
    def _extract_all_languages(self, projects: List[Dict[str, Any]]) -> List[str]:
        languages = set()
        for project in projects:
            lang = project.get('language')
            if lang:
                languages.add(lang)
            skills = project.get('key_skills', [])
            for skill in skills:
                if skill in ['Python', 'JavaScript', 'Java', 'C++', 'Go', 'Rust', 'TypeScript', 'C#', 'Ruby', 'PHP', 'Swift', 'Kotlin']:
                    languages.add(skill)
        return sorted(list(languages))
    
    def _extract_all_frameworks(self, projects: List[Dict[str, Any]]) -> List[str]:
        frameworks = set()
        for project in projects:
            fw = project.get('framework')
            if fw:
                frameworks.add(fw)
            skills = project.get('key_skills', [])
            for skill in skills:
                if skill in ['Django', 'Flask', 'React', 'Vue', 'Angular', 'Express', 'Spring', 'Rails', 'Laravel']:
                    frameworks.add(skill)
        return sorted(list(frameworks))
    
    def _calculate_doc_ratio(self, project: Dict[str, Any]) -> float:
        doc_files = project.get('documentation_files', 0)
        total_files = project.get('total_files', 1)
        return (doc_files / total_files * 100) if total_files > 0 else 0
    
    def _calculate_test_ratio(self, project: Dict[str, Any]) -> float:
        test_files = project.get('test_files', 0)
        code_files = project.get('code_files', 1)
        return (test_files / code_files * 100) if code_files > 0 else 0


def match_to_job_description(projects: List[Dict[str, Any]], job_desc: str) -> List[Tuple[str, float, str]]:
    job_desc_lower = job_desc.lower()
    keywords = set(re.findall(r'\b\w{4,}\b', job_desc_lower))
    
    tech_keywords = {
        'python', 'java', 'javascript', 'react', 'node', 'django', 'flask',
        'api', 'rest', 'database', 'sql', 'mongodb', 'aws', 'docker',
        'kubernetes', 'testing', 'ci/cd', 'agile', 'git', 'vue', 'angular'
    }
    
    scored_projects = []
    
    for project in projects:
        score = 0
        matched_skills = []
        
        skills = [s.lower() for s in project.get('key_skills', [])]
        for skill in skills:
            if skill in job_desc_lower:
                score += 10
                matched_skills.append(skill)
            if skill in tech_keywords and skill in keywords:
                score += 5
        
        desc = (project.get('description', '') + ' ' + project.get('project_name', '')).lower()
        for keyword in keywords:
            if keyword in desc:
                score += 2
        
        if project.get('created_at', '') > '2023-01-01':
            score += 5
        
        if project.get('is_collaborative', False):
            if any(kw in job_desc_lower for kw in ['team', 'collaborate', 'agile']):
                score += 3
        
        reason = f"Matches: {', '.join(matched_skills[:3])}" if matched_skills else "General fit"
        scored_projects.append((project.get('project_name', 'Unknown'), score, reason))
    
    return sorted(scored_projects, key=lambda x: x[1], reverse=True)

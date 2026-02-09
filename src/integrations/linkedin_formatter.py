"""LinkedIn post formatter for portfolio items"""
from __future__ import annotations
from typing import Any, Dict, List


class LinkedInFormatter:
    """Formats portfolio items into LinkedIn-ready post text."""
    MAX_LENGTH = 3000

    def format_portfolio_post(
        self, portfolio_item: Dict[str, Any], include_hashtags: bool = True, include_emojis: bool = True
    ) -> Dict[str, Any]:
        project_name = portfolio_item.get("project_name", "Project")
        tagline = portfolio_item.get("tagline", "")
        description = portfolio_item.get("description", "")
        languages = portfolio_item.get("languages") or []
        frameworks = portfolio_item.get("frameworks") or []
        skills = portfolio_item.get("skills") or []
        is_collaborative = portfolio_item.get("is_collaborative", False)

        sections = []
        sections.append(self._format_header(project_name, tagline, include_emojis))
        if description:
            sections.append(self._format_description(description, 500))
        if languages or frameworks:
            sections.append(self._format_tech_stack(languages, frameworks, include_emojis))
        if skills:
            sections.append(self._format_skills(skills, include_emojis))
        
        metrics = {
            "total_commits": portfolio_item.get("total_commits"),
            "total_lines": portfolio_item.get("total_lines"),
            "total_files": portfolio_item.get("total_files"),
        }
        if any(v is not None for v in metrics.values()):
            metrics_section = self._format_metrics(metrics, include_emojis)
            if metrics_section:
                sections.append(metrics_section)

        sections.append(self._format_call_to_action(is_collaborative))
        text = "\n\n".join(sections)

        hashtags = []
        if include_hashtags:
            hashtags = self._generate_hashtags(languages, frameworks, skills)
            if hashtags:
                text = f"{text}\n\n{' '.join(hashtags)}"

        text = self._truncate_if_needed(text)
        preview = text[:500]
        if len(text) > 500:
            preview = preview.rsplit(" ", 1)[0] + "..."

        return {
            "text": text,
            "char_count": len(text),
            "exceeds_limit": len(text) > self.MAX_LENGTH,
            "hashtags": hashtags,
            "preview": preview,
        }

    def _format_header(self, project_name: str, tagline: str, include_emojis: bool) -> str:
        emoji = "🚀 " if include_emojis else ""
        return f"{emoji}{project_name} - {tagline}" if tagline else f"{emoji}{project_name}"

    def _format_description(self, description: str, max_length: int = 500) -> str:
        if not description:
            return ""
        if len(description) > max_length:
            truncated = description[:max_length]
            last_sentence_end = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
            if last_sentence_end > max_length * 0.7:
                description = truncated[: last_sentence_end + 1]
            else:
                description = truncated.rsplit(" ", 1)[0] + "..."
        return description

    def _format_tech_stack(self, languages: List[str], frameworks: List[str], include_emojis: bool) -> str:
        emoji = "💻 " if include_emojis else ""
        parts = []
        if languages:
            parts.append(f"• Languages: {', '.join(languages[:10])}")
        if frameworks:
            parts.append(f"• Frameworks: {', '.join(frameworks[:10])}")
        return f"{emoji}Tech Stack:\n" + "\n".join(parts) if parts else ""

    def _format_skills(self, skills: List[str], include_emojis: bool) -> str:
        if not skills:
            return ""
        emoji = "✨ " if include_emojis else ""
        skills_text = " • ".join(skills[:8])
        return f"{emoji}Key Skills:\n• {skills_text}"

    def _format_metrics(self, metrics: Dict[str, Any], include_emojis: bool) -> str:
        parts = []
        if metrics.get("total_commits"):
            parts.append(f"• {metrics['total_commits']:,} commits")
        if metrics.get("total_lines"):
            parts.append(f"• {metrics['total_lines']:,} lines of code")
        if metrics.get("total_files"):
            parts.append(f"• {metrics['total_files']} files")
        if not parts:
            return ""
        emoji = "📊 " if include_emojis else ""
        return f"{emoji}Project Highlights:\n" + "\n".join(parts)

    def _generate_hashtags(self, languages: List[str], frameworks: List[str], skills: List[str]) -> List[str]:
        hashtags = set()
        for lang in languages[:5]:
            tag = lang.lower().replace(" ", "").replace("+", "plus").replace("#", "sharp")
            if tag:
                hashtags.add(f"#{tag}")
        for fw in frameworks[:3]:
            tag = fw.lower().replace(" ", "").replace(".", "")
            if tag and len(tag) > 2:
                hashtags.add(f"#{tag}")
        for tag in ["#coding", "#portfolio", "#softwareengineering", "#projects", "#webdevelopment"][:4]:
            hashtags.add(tag)
        return sorted(list(hashtags))[:12]

    def _format_call_to_action(self, is_collaborative: bool) -> str:
        if is_collaborative:
            return "Excited to share this collaborative project! Grateful for the opportunity to work with such a talented team. Check out my portfolio for more details."
        return "Excited to share this project showcasing modern development practices! Check out my portfolio for more details. Always open to feedback and connecting with fellow developers."

    def _truncate_if_needed(self, text: str) -> str:
        if len(text) <= self.MAX_LENGTH:
            return text
        truncated = text[: self.MAX_LENGTH - 3]
        last_newline = truncated.rfind("\n")
        if last_newline > self.MAX_LENGTH * 0.8:
            return truncated[:last_newline] + "..."
        last_sentence = max(truncated.rfind(". "), truncated.rfind("! "), truncated.rfind("? "))
        if last_sentence > self.MAX_LENGTH * 0.8:
            return truncated[: last_sentence + 1] + "..."
        last_space = truncated.rfind(" ")
        if last_space > 0:
            return truncated[:last_space] + "..."
        return truncated + "..."

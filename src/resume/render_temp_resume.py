from pathlib import Path

from src.resume.resume_artifact import render_resume_template, write_rendered_resume


def main() -> None:
    resume_dir = Path(__file__).resolve().parent
    template_name = "resume_template.tex"
    output_name = "tmp_resume_rendered.tex"

    context = {
        "name": "Dave Smith",
        "phone": "+1 (555) 010-0000",
        "email": "dave.smith@example.com",
        "linkedin_url": "https://linkedin.com/in/davesmith",
        "linkedin_label": "linkedin.com/in/davesmith",
        "github_url": "https://github.com/davesmith",
        "github_label": "github.com/davesmith",
        "education": [
            {
                "school": "Example State University",
                "start_date": "Sep 2020",
                "end_date": "May 2024",
                "degree": "B.Sc. in Computer Science",
                "location": "Example City, ST",
            }
        ],
        "skills": {
            "Advanced": ["Python", "APIs"],
            "Proficient": ["SQL", "Git"],
            "Working Knowledge": ["Docker", "Linux"],
            "Familiar": ["LaTeX", "JavaScript"],
        },
        "projects": [
            {
                "name": "Portfolio Dashboard",
                "start_date": "Jan 2024",
                "end_date": "Apr 2024",
                "tech_stack": "Python, FastAPI, SQLite",
                "github_url": "https://github.com/davesmith/portfolio-dashboard",
                "github_label": "Project GitHub",
                "bullets": [
                    "Built REST endpoints for project and resume workflows.",
                    "Improved template rendering reliability and test coverage.",
                ],
            }
        ],
        "awards": [
            {
                "name": "Dean's List",
                "date": "2023",
                "organization": "Example State University",
                "bullets": ["Recognized for strong academic performance."],
            }
        ],
    }

    rendered = render_resume_template(
        context,
        template_path=resume_dir / template_name,
    )
    output_path = write_rendered_resume(rendered, resume_dir / output_name)
    print(f"Rendered template written to: {output_path}")


if __name__ == "__main__":
    main()

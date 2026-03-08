from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def main() -> None:
    resume_dir = Path(__file__).resolve().parent
    template_name = "resume_template.tex"
    output_name = "tmp_resume_rendered.tex"

    context = {
        "name": "Abijeet Dhillon",
        "phone": "+1 (250) 555-1234",
        "email": "abijeet@example.com",
        "linkedin_url": "https://linkedin.com/in/abijeet",
        "linkedin_label": "linkedin.com/in/abijeet",
        "github_url": "https://github.com/abijeet-dhillon",
        "github_label": "github.com/abijeet-dhillon",
        "education": [
            {
                "school": "University of British Columbia",
                "start_date": "Sep 2022",
                "end_date": "May 2026",
                "degree": "B.Sc. in Computer Science",
                "location": "Kelowna, BC",
            }
        ],
        "skills": {
            "Advanced": ["Python", "FastAPI"],
            "Proficient": ["SQL", "Git"],
            "Working Knowledge": ["Docker", "Linux"],
            "Familiar": ["LaTeX", "React"],
        },
        "projects": [
            {
                "name": "Digital Work Artifact Miner",
                "start_date": "Jan 2026",
                "end_date": "Present",
                "tech_stack": "Python, FastAPI, SQLite",
                "github_url": "https://github.com/COSC-499-W2025/capstone-project-team-14",
                "github_label": "Project GitHub",
                "bullets": [
                    "Built API endpoints for resume and project presentation workflows.",
                    "Improved data pipeline robustness and template rendering flow.",
                ],
            }
        ],
        "awards": [
            {
                "name": "Dean's List",
                "date": "2025",
                "organization": "University of British Columbia",
                "bullets": ["Recognized for academic standing in top cohort."],
            }
        ],
    }

    env = Environment(loader=FileSystemLoader(str(resume_dir)), autoescape=False)
    template = env.get_template(template_name)
    rendered = template.render(**context)

    output_path = resume_dir / output_name
    output_path.write_text(rendered, encoding="utf-8")
    print(f"Rendered template written to: {output_path}")


if __name__ == "__main__":
    main()

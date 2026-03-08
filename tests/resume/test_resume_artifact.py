from src.resume.resume_artifact import (
    build_resume_context,
    escape_latex,
    generate_resume_tex_artifact,
)


def test_build_resume_context_handles_missing_optional_fields():
    context = build_resume_context({"projects": {"OnlyProject": {"project_name": "OnlyProject"}}})

    assert context["name"] == ""
    assert context["email"] == ""
    assert context["education"] == []
    assert context["awards"] == []
    assert context["skills"] == {
        "Advanced": [],
        "Proficient": [],
        "Working Knowledge": [],
        "Familiar": [],
    }
    assert context["projects"] == [
        {
            "name": "OnlyProject",
            "start_date": "",
            "end_date": "",
            "tech_stack": "",
            "github_url": "",
            "github_label": "",
            "bullets": [],
        }
    ]


def test_escape_latex_escapes_common_special_characters():
    escaped = escape_latex(r"\ { } $ & # _ % ~ ^")
    assert r"\textbackslash{}" in escaped
    assert r"\{" in escaped
    assert r"\}" in escaped
    assert r"\$" in escaped
    assert r"\&" in escaped
    assert r"\#" in escaped
    assert r"\_" in escaped
    assert r"\%" in escaped
    assert r"\textasciitilde{}" in escaped
    assert r"\textasciicircum{}" in escaped


def test_generate_resume_tex_artifact_writes_escaped_template_output(tmp_path):
    template_path = tmp_path / "resume_template.tex"
    template_path.write_text(
        "{{ name }}|{{ email }}|{{ projects[0].name }}|{{ projects[0].bullets[0] }}",
        encoding="utf-8",
    )
    output_path = tmp_path / "reports" / "report_20260101_120000.tex"

    report = {
        "projects": {
            "ProjectAlpha": {
                "project_name": "Project_Alpha & Co",
                "project_metrics": {
                    "skills": ["Python", "FastAPI"],
                    "frameworks": ["Jinja2"],
                    "languages": ["Python"],
                    "total_lines": 1200,
                },
                "resume_item": {
                    "project_name": "Project_Alpha & Co",
                    "bullets": [
                        "Improved reliability by 40% using feature_1 & feature#2 with {care} and $budget."
                    ],
                },
                "git_analysis": {
                    "contributors": [
                        {"author": {"name": "Jane ^ Doe", "email": "jane_doe@example.com"}, "commits": 5}
                    ]
                },
            }
        }
    }

    rendered_path = generate_resume_tex_artifact(
        report,
        output_path,
        template_path=template_path,
    )

    assert rendered_path == output_path
    assert rendered_path.exists()
    rendered = rendered_path.read_text(encoding="utf-8")
    assert r"Jane \textasciicircum{} Doe" in rendered
    assert r"jane\_doe@example.com" in rendered
    assert r"Project\_Alpha \& Co" in rendered
    assert r"40\%" in rendered
    assert r"feature\_1 \& feature\#2" in rendered
    assert r"\{care\}" in rendered
    assert r"\$budget." in rendered

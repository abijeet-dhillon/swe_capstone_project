from pathlib import Path
import pytest
from src.resume.resume_artifact import (
    build_resume_context,
    escape_latex,
    render_resume_template,
    generate_resume_tex_artifact,
    generate_resume_pdf_artifact,
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

def test_build_resume_context_uses_explicit_resume_owner_over_git_contributor():
    context = build_resume_context(
        {
            "resume_owner": {"name": "Actual Student"},
            "projects": {
                "OnlyProject": {
                    "project_name": "OnlyProject",
                    "git_analysis": {
                        "contributors": [
                            {"author": {"name": "Top Contributor", "email": "top@example.com"}, "commits": 99}
                        ]
                    },
                }
            },
        }
    )
    assert context["name"] == "Actual Student"
    assert context["email"] == ""

def test_build_resume_context_includes_optional_profile_fields_and_education():
    context = build_resume_context(
        {
            "resume_owner": {
                "name": "Actual Student",
                "phone": "555-111-2222",
                "email": "student@example.com",
                "linkedin_url": "https://linkedin.com/in/student",
                "github_url": "https://github.com/student",
                "education": [
                    {
                        "school": "University of Victoria",
                        "degree": "BSc Computer Science",
                        "location": "Victoria, BC",
                        "start_date": "Sep 2022",
                        "is_current": True,
                        "expected_graduation": "May 2027",
                    }
                ],
            },
            "projects": {"OnlyProject": {"project_name": "OnlyProject"}},
        }
    )
    assert context["phone"] == "555-111-2222"
    assert context["email"] == "student@example.com"
    assert context["linkedin_url"] == "https://linkedin.com/in/student"
    assert context["linkedin_label"] == "LinkedIn"
    assert context["github_url"] == "https://github.com/student"
    assert context["github_label"] == "GitHub"
    assert context["education"] == [
        {
            "school": "University of Victoria",
            "degree": "BSc Computer Science",
            "location": "Victoria, BC",
            "start_date": "Sep 2022",
            "end_date": "Expected May 2027",
        }
    ]

def test_render_resume_template_renders_contact_info_inline():
    context = build_resume_context(
        {
            "resume_owner": {
                "name": "Actual Student",
                "phone": "555-111-2222",
                "email": "student@example.com",
                "linkedin_url": "https://linkedin.com/in/student",
                "github_url": "https://github.com/student",
            },
            "projects": {"OnlyProject": {"project_name": "OnlyProject"}},
        }
    )

    rendered = render_resume_template(context)
    address_block = rendered.split("\\address{", 1)[1].split("}\n\\begin{document}", 1)[0]

    assert "555-111-2222" in address_block
    assert r"\href{mailto:student@example.com}" in address_block
    assert r"\href{https://linkedin.com/in/student}" in address_block
    assert r"\href{https://github.com/student}" in address_block
    assert r"\enspace $|$ \enspace" in address_block
    assert r"\\" not in address_block

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
        "resume_owner": {"name": "Actual Student"},
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
    assert "Actual Student" in rendered
    assert r"Project\_Alpha \& Co" in rendered
    assert r"40\%" in rendered
    assert r"feature\_1 \& feature\#2" in rendered
    assert r"\{care\}" in rendered
    assert r"\$budget." in rendered

def test_build_resume_context_fallback_bullets_do_not_claim_all_repo_commits_without_match():
    context = build_resume_context(
        {
            "resume_owner": {"name": "Actual Student"},
            "projects": {
                "TeamProject": {
                    "project_name": "TeamProject",
                    "project_metrics": {"total_lines": 800, "skills": ["Python"]},
                    "git_analysis": {
                        "total_commits": 42,
                        "total_contributors": 3,
                        "git_identifier_matched": False,
                        "user_contribution": None,
                    },
                }
            },
        }
    )
    bullets = context["projects"][0]["bullets"]
    assert any("Worked on a 3-contributor repository with 42 commits." == bullet for bullet in bullets)

def test_generate_resume_pdf_artifact_raises_on_compiler_failure(tmp_path, monkeypatch):
    template_path = tmp_path / "resume_template.tex"
    template_path.write_text("{{ name }}", encoding="utf-8")
    def fail_run(*_args, **_kwargs):
        raise FileNotFoundError("pdflatex not found")
    monkeypatch.setattr("src.resume.resume_artifact.subprocess.run", fail_run)
    with pytest.raises(RuntimeError):
        generate_resume_pdf_artifact({"projects": {"P": {"project_name": "P"}}}, tmp_path / "reports" / "report.pdf", template_path=template_path)

def test_generate_resume_pdf_artifact_writes_pdf_without_tex_in_reports(tmp_path, monkeypatch):
    template_path = tmp_path / "resume_template.tex"
    template_path.write_text("{{ name }}", encoding="utf-8")
    output_path = tmp_path / "reports" / "report_20260101_120000.pdf"
    def fake_run(_cmd, cwd, **_kwargs):
        (Path(cwd) / "resume.pdf").write_bytes(b"%PDF-1.4\n")
    monkeypatch.setattr("src.resume.resume_artifact.subprocess.run", fake_run)
    rendered_path = generate_resume_pdf_artifact({"projects": {"P": {"project_name": "P"}}}, output_path, template_path=template_path)
    assert rendered_path.exists()
    assert not output_path.with_suffix(".tex").exists()

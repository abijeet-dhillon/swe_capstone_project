from pathlib import Path

import pytest
from jinja2.exceptions import TemplateNotFound

from src.resume import render_temp_resume


def test_main_renders_and_writes_output_happy_path(tmp_path, monkeypatch, capsys):
    resume_dir = tmp_path / "resume"
    resume_dir.mkdir(parents=True, exist_ok=True)
    (resume_dir / "resume_template.tex").write_text(
        r"""
\name{ {{ name }} }
{{ email }}
{% for edu in education %}{{ edu.school }}{% endfor %}
{% for project in projects %}{{ project.name }}{% endfor %}
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(render_temp_resume, "__file__", str(resume_dir / "render_temp_resume.py"))

    render_temp_resume.main()

    output_path = resume_dir / "tmp_resume_rendered.tex"
    assert output_path.exists()
    rendered = output_path.read_text(encoding="utf-8")
    assert "Dave Smith" in rendered
    assert "dave.smith@example.com" in rendered
    assert "Example State University" in rendered
    assert "Portfolio Dashboard" in rendered

    out = capsys.readouterr().out
    assert "Rendered template written to:" in out
    assert str(output_path) in out


def test_main_raises_when_template_missing(tmp_path, monkeypatch):
    resume_dir = tmp_path / "resume"
    resume_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(render_temp_resume, "__file__", str(resume_dir / "render_temp_resume.py"))

    with pytest.raises(TemplateNotFound):
        render_temp_resume.main()


def test_main_overwrites_existing_output_edge_case(tmp_path, monkeypatch):
    resume_dir = tmp_path / "resume"
    resume_dir.mkdir(parents=True, exist_ok=True)
    (resume_dir / "resume_template.tex").write_text("{{ name }}", encoding="utf-8")

    output_path = resume_dir / "tmp_resume_rendered.tex"
    output_path.write_text("OLD_CONTENT", encoding="utf-8")

    monkeypatch.setattr(render_temp_resume, "__file__", str(resume_dir / "render_temp_resume.py"))

    render_temp_resume.main()

    rendered = output_path.read_text(encoding="utf-8")
    assert rendered == "Dave Smith"
    assert rendered != "OLD_CONTENT"

import os
import shutil
import tempfile
from contextlib import contextmanager

from fastapi.testclient import TestClient

from src.api import deps
from src.api.app import app
from src.config.config_manager import UserConfigManager


@contextmanager
def profile_client(seed: bool = True, extra_fields: dict | None = None):
    td = tempfile.mkdtemp()
    try:
        manager = UserConfigManager(db_path=os.path.join(td, "app.db"))
        if seed:
            manager.create_config("u", "/tmp/t.zip", False)
        if extra_fields:
            manager.update_config("u", **extra_fields)
        app.dependency_overrides[deps.get_config_manager] = lambda: manager
        yield TestClient(app), manager
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_get_profile_returns_structured_fields():
    with profile_client(
        extra_fields={
            "name": "Jane Smith",
            "email": "j@x.com",
            "phone_number": "123",
            "linkedin_url": "https://linkedin.com/in/jane",
            "github_url": "https://github.com/jane",
            "education": [
                {
                    "school": "UVic",
                    "degree": "BSc",
                    "location": "Victoria",
                    "from": "Sep 2022",
                    "to": "May 2026",
                    "still_studying": False,
                }
            ],
            "awards": ["Dean's List"],
            "portfolio_title": "Full-Stack Developer",
        }
    ) as (client, _):
        r = client.get("/profile/u")
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "Jane Smith"
        assert d["contact"]["email"] == "j@x.com"
        assert d["contact"]["github_url"] == "https://github.com/jane"
        assert d["education"][0]["school"] == "UVic"
        assert d["awards"] == ["Dean's List"]
        assert d["portfolio"]["title"] == "Full-Stack Developer"


def test_get_profile_defaults_when_unset():
    with profile_client() as (client, _):
        r = client.get("/profile/u")
        assert r.status_code == 200
        d = r.json()
        assert d["name"] is None
        assert d["contact"]["email"] is None
        assert d["education"] == []
        assert d["awards"] == []


def test_get_profile_404_unknown_user():
    with profile_client(seed=False) as (client, _):
        assert client.get("/profile/nobody").status_code == 404


def test_patch_profile_updates_structured_fields():
    with profile_client() as (client, manager):
        r = client.patch(
            "/profile/u",
            json={
                "name": "Alice Cooper",
                "contact": {"email": "alice@example.com", "phone_number": "999"},
                "education": [{"school": "UVic", "degree": "BSc", "from": "2022", "to": "2026"}],
                "awards": ["Scholarship Winner"],
                "portfolio": {"title": "Developer", "about_me": "Building tools"},
            },
        )
        assert r.status_code == 200
        stored = manager.load_config("u", silent=True)
        assert stored is not None
        assert stored.name == "Alice Cooper"
        assert stored.email == "alice@example.com"
        assert stored.phone_number == "999"
        assert stored.education and stored.education[0]["school"] == "UVic"
        assert stored.awards == ["Scholarship Winner"]
        assert stored.portfolio_title == "Developer"


def test_patch_profile_partial_leaves_other_values():
    with profile_client(extra_fields={"name": "Bob", "email": "bob@example.com"}) as (client, manager):
        r = client.patch("/profile/u", json={"contact": {"github_url": "https://github.com/bob"}})
        assert r.status_code == 200
        stored = manager.load_config("u", silent=True)
        assert stored is not None
        assert stored.name == "Bob"
        assert stored.email == "bob@example.com"
        assert stored.github_url == "https://github.com/bob"


def test_patch_profile_404_unknown_user():
    with profile_client(seed=False) as (client, _):
        assert client.patch("/profile/nobody", json={"name": "Ghost"}).status_code == 404

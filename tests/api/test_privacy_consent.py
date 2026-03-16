import os
import shutil
import tempfile

from fastapi.testclient import TestClient

from src.api import deps
from src.api.app import app
from src.config.config_manager import UserConfigManager


def test_privacy_consent_creates_config():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        manager = UserConfigManager(db_path=db_path)
        app.dependency_overrides[deps.get_config_manager] = lambda: manager

        client = TestClient(app)
        response = client.post(
            "/privacy-consent",
            json={
                "user_id": "tester",
                "zip_path": "/tmp/demo.zip",
                "llm_consent": True,
                "data_access_consent": True,
                "resume_owner_name": "Resume Owner",
            },
        )

        assert response.status_code == 200
        stored = manager.load_config("tester", silent=True)
        assert stored is not None
        assert stored.llm_consent is True
        assert stored.llm_consent_asked is True
        assert stored.data_access_consent is True
        assert stored.resume_owner_name == "Resume Owner"
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)


def test_git_identifier_set_and_get():
    td = tempfile.mkdtemp()
    try:
        db_path = os.path.join(td, "app.db")
        manager = UserConfigManager(db_path=db_path)
        manager.create_config("git_tester", "/tmp/test.zip", False)
        app.dependency_overrides[deps.get_config_manager] = lambda: manager

        client = TestClient(app)
        response = client.post(
            "/git-identifier",
            json={"user_id": "git_tester", "git_identifier": "test@example.com"},
        )
        assert response.status_code == 200
        assert response.json()["git_identifier"] == "test@example.com"

        get_response = client.get("/git-identifier/git_tester")
        assert get_response.status_code == 200
        assert get_response.json()["git_identifier"] == "test@example.com"
    finally:
        app.dependency_overrides.clear()
        shutil.rmtree(td, ignore_errors=True)

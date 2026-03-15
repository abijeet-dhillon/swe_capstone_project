import os
import shutil
import tempfile
from contextlib import contextmanager

import pytest
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


def test_get_profile_returns_all_fields():
    with profile_client(extra_fields={"first_name": "Jane", "last_name": "Smith", "email": "j@x.com", "github_username": "jsmith", "git_identifier": "j@x.com"}) as (client, _):
        r = client.get("/profile/u")
        assert r.status_code == 200
        d = r.json()
        assert d["first_name"] == "Jane" and d["last_name"] == "Smith"
        assert d["email"] == "j@x.com" and d["github_username"] == "jsmith"


def test_get_profile_nulls_when_unset():
    with profile_client() as (client, _):
        r = client.get("/profile/u")
        assert r.status_code == 200
        d = r.json()
        assert all(d[k] is None for k in ("first_name", "last_name", "email", "github_username"))


def test_get_profile_404_unknown_user():
    with profile_client(seed=False) as (client, _):
        assert client.get("/profile/nobody").status_code == 404


def test_patch_profile_updates_fields():
    with profile_client() as (client, manager):
        r = client.patch("/profile/u", json={"first_name": "Alice", "email": "a@x.com"})
        assert r.status_code == 200
        stored = manager.load_config("u", silent=True)
        assert stored.first_name == "Alice" and stored.email == "a@x.com"


def test_patch_profile_partial_leaves_others_unchanged():
    with profile_client(extra_fields={"first_name": "Bob", "last_name": "Jones"}) as (client, manager):
        client.patch("/profile/u", json={"github_username": "bjones"})
        stored = manager.load_config("u", silent=True)
        assert stored.first_name == "Bob" and stored.last_name == "Jones" and stored.github_username == "bjones"


def test_patch_profile_404_unknown_user():
    with profile_client(seed=False) as (client, _):
        assert client.patch("/profile/nobody", json={"first_name": "Ghost"}).status_code == 404

"""
Tests for the filter API endpoints.
"""

import os
import shutil
import tempfile

import httpx
import pytest

from src.api import deps
from src.api.app import app
from src.insights.project_filter import ProjectFilterEngine
from src.insights.storage import ProjectInsightsStore
from src.api.routers.filter import get_filter_engine
from tests.insights.utils import build_pipeline_payload


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def setup():
    td = tempfile.mkdtemp()
    db_path = os.path.join(td, "app.db")
    store = ProjectInsightsStore(db_path=db_path, encryption_key=b"dev")
    store.record_pipeline_run(os.path.join(td, "demo.zip"), build_pipeline_payload())
    engine = ProjectFilterEngine(db_path=db_path)

    app.dependency_overrides[deps.get_store] = lambda: store
    app.dependency_overrides[get_filter_engine] = lambda: engine
    yield
    app.dependency_overrides.clear()
    shutil.rmtree(td, ignore_errors=True)


@pytest.mark.anyio
class TestFilterEndpoint:
    async def test_filter_all(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/filter/", json={})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 2

    async def test_filter_with_search(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/filter/", json={"search_text": "Alpha"})
        assert resp.status_code == 200
        assert any("Alpha" in p["project_name"] for p in resp.json()["projects"])

    async def test_filter_with_metrics(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/filter/", json={"metrics": {"min_lines": 1}, "sort_by": "loc_desc"})
        assert resp.status_code == 200
        assert all(p["total_lines"] >= 1 for p in resp.json()["projects"])

    async def test_filter_with_limit(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/filter/", json={"limit": 1})
        assert resp.status_code == 200
        assert len(resp.json()["projects"]) <= 1

    async def test_filter_metrics_validation(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post("/filter/", json={"metrics": {"min_lines": 100, "max_lines": 10}})
        assert resp.status_code == 422


@pytest.mark.anyio
class TestSearchEndpoint:
    async def test_search_returns_results(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/filter/search", params={"q": "Project"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
        assert resp.json()["search_term"] == "Project"

    async def test_search_no_results(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/filter/search", params={"q": "zzz_nonexistent_zzz"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_search_requires_query(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/filter/search")
        assert resp.status_code == 422


@pytest.mark.anyio
class TestOptionsEndpoint:
    async def test_returns_structure(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/filter/options")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sort_options"]) > 0
        assert len(data["project_types"]) > 0


@pytest.mark.anyio
class TestPresetEndpoints:
    async def _save(self, c, name="Test Preset"):
        return await c.post("/filter/presets", json={
            "name": name,
            "description": f"Preset: {name}",
            "filter_config": {"metrics": {"min_lines": 1}, "sort_by": "loc_desc"},
        })

    async def test_save_and_get_preset(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await self._save(c)
            assert resp.status_code == 200
            pid = resp.json()["id"]
            get_resp = await c.get(f"/filter/presets/{pid}")
            assert get_resp.status_code == 200
            assert get_resp.json()["id"] == pid

    async def test_list_presets(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            await self._save(c, "A")
            await self._save(c, "B")
            resp = await c.get("/filter/presets")
            assert resp.status_code == 200
            names = {p["name"] for p in resp.json()["presets"]}
            assert "A" in names and "B" in names

    async def test_delete_preset(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            pid = (await self._save(c)).json()["id"]
            assert (await c.delete(f"/filter/presets/{pid}")).status_code == 200
            assert (await c.get(f"/filter/presets/{pid}")).status_code == 404

    async def test_delete_not_found(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            assert (await c.delete("/filter/presets/99999")).status_code == 404

    async def test_apply_preset(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            pid = (await self._save(c)).json()["id"]
            resp = await c.post(f"/filter/presets/{pid}/apply")
            assert resp.status_code == 200
            assert resp.json()["total"] >= 1

    async def test_apply_not_found(self, setup):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            assert (await c.post("/filter/presets/99999/apply")).status_code == 404

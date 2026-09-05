from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.dependencies import get_incident_processor
from app.repositories.idempotency import idempotency_store
from app.models.knowledge_base import KnowledgeBase, KBArticle
from app.models.incident import IncidentPayload

# ---------------------------------------------------------------------------
# Environment / caching hygiene
# ---------------------------------------------------------------------------
# get_incident_processor (and possibly get_settings) are @lru_cache'd in the
# real app, so credentials/services are only built once per process. That's
# exactly the kind of caching that caused a real stale-credential bug during
# development -- these fixtures make sure it can't quietly leak state
# between test cases instead of assuming it "just works".


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
    monkeypatch.setenv("SERVICENOW_INSTANCE_URL", "https://test.service-now.com")
    monkeypatch.setenv("SERVICENOW_USERNAME", "test-user")
    monkeypatch.setenv("SERVICENOW_PASSWORD", "test-pass")


@pytest.fixture(autouse=True)
def _clear_caches():
    if hasattr(get_incident_processor, "cache_clear"):
        get_incident_processor.cache_clear()

    try:
        from app.core.config import get_settings

        if hasattr(get_settings, "cache_clear"):
            get_settings.cache_clear()
    except ImportError:
        pass

    yield

    if hasattr(get_incident_processor, "cache_clear"):
        get_incident_processor.cache_clear()


@pytest.fixture(autouse=True)
def _reset_idempotency_store():
    """idempotency_store is a module-level singleton shared by the whole
    app -- without this, a claim() made by one test would silently affect
    a later test that reuses the same incident_sys_id."""
    idempotency_store._states.clear()
    yield
    idempotency_store._states.clear()


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------


@pytest.fixture
def payload_factory():
    def _make(**overrides) -> dict:
        payload = {
            "incident_sys_id": "sys_id_001",
            "number": "INC0000001",
            "short_description": "Printer not printing after office move",
            "description": "It was working yesterday. I tried turning it off and on.",
            "priority": 3,
        }
        payload.update(overrides)
        return payload

    return _make


@pytest.fixture
def incident_factory(payload_factory):
    def _make(**overrides) -> IncidentPayload:
        return IncidentPayload(**payload_factory(**overrides))

    return _make


@pytest.fixture
def kb_data() -> KnowledgeBase:
    """Mirrors the 5 supplied KB articles so service-level tests exercise
    the real grounding text, not a stand-in."""
    return KnowledgeBase(
        articles=[
            KBArticle(
                id=1,
                text="Printer not printing: Restart the printer and unplug the cable for 30 seconds.",
            ),
            KBArticle(
                id=2,
                text="Email not sending: Check SMTP settings and ensure port 587 is open.",
            ),
            KBArticle(
                id=3,
                text="Cannot access system: Reset password via the 'Forgot Password' page.",
            ),
            KBArticle(
                id=4,
                text="Slow network: Restart the router and check cable connections.",
            ),
            KBArticle(
                id=5,
                text="Browser pages not loading: Clear cache and try incognito mode.",
            ),
        ]
    )


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
def client(_test_env) -> TestClient:
    """TestClient as a context manager so FastAPI's lifespan (which reads
    settings on startup) actually runs against our patched test env vars."""
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class FakeIncidentProcessor:
    """Stand-in for IncidentProcessor injected via dependency_overrides so
    webhook-layer tests never touch real Gemini/ServiceNow."""

    def __init__(self, exc: Exception | None = None):
        self.calls: list[IncidentPayload] = []
        self._exc = exc

    async def process_incident(self, incident: IncidentPayload) -> None:
        self.calls.append(incident)
        if self._exc is not None:
            raise self._exc


@pytest.fixture
def fake_processor() -> FakeIncidentProcessor:
    return FakeIncidentProcessor()


@pytest.fixture
def client_with_fake_processor(client, fake_processor):
    app.dependency_overrides[get_incident_processor] = lambda: fake_processor
    yield client, fake_processor

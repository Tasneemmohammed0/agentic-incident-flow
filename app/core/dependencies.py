from pathlib import Path
from functools import lru_cache

from app.core.config import get_settings
from app.models.knowledge_base import KnowledgeBase
from app.repositories.idempotency import idempotency_store
from app.services.gemini_service import GeminiService
from app.services.incident_processor import IncidentProcessor
from app.services.servicenow_service import ServiceNowService


def load_kb_data() -> KnowledgeBase:
    kb_path = Path(__file__).parent.parent / "data" / "kb_articles.json"
    return KnowledgeBase.model_validate_json(kb_path.read_text(encoding="utf-8"))


@lru_cache
def get_incident_processor() -> IncidentProcessor:
    settings = get_settings()

    return IncidentProcessor(
        gemini_service=GeminiService(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
        ),
        service_now_service=ServiceNowService(
            instance_url=str(settings.servicenow_instance_url),
            username=settings.servicenow_username,
            password=settings.servicenow_password,
        ),
        idempotency_store=idempotency_store,
        kb_data=load_kb_data(),
    )

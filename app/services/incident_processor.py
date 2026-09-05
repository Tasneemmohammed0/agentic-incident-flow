import json
import logging

from pathlib import Path
from app.repositories.idempotency import IdempotencyStore
from app.services.gemini_service import GeminiService
from app.services.servicenow_service import ServiceNowService
from app.models.knowledge_base import KnowledgeBase
from app.models.incident import IncidentPayload
from app.repositories.idempotency import idempotency_store
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class IncidentProcessor:
    """
    Ties together gemini decision and serviceNow writeback
    """

    def __init__(
        self,
        gemini_service: GeminiService,
        service_now_service: ServiceNowService,
        idempotency_store: IdempotencyStore,
        kb_data: KnowledgeBase,
    ):
        self._gemini_service = gemini_service
        self._service_now_service = service_now_service
        self._idempotency_store = idempotency_store
        self._kb_data = kb_data

    async def process_incident(self, incident: IncidentPayload):
        try:
            result = await self._gemini_service.decide(self._kb_data, incident)
            logger.info(
                "Decision for incident %s: %s", incident.number, result.decision
            )

            # ToDo: Update the incident in ServiceNow based on the decision

            await self._idempotency_store.complete(incident.incident_sys_id)
            logger.info(
                "Incident %s processing completed and marked as complete in idempotency store",
                incident.number,
            )
        except Exception as e:
            logger.error("Error processing incident %s: %s", incident.number, str(e))
            # Optionally, you can also mark the incident as failed in the idempotency store
            await self._idempotency_store.release(incident.incident_sys_id)

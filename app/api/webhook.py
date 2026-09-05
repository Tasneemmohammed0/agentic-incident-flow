import logging

from fastapi import APIRouter, Depends, status, BackgroundTasks

from app.models.incident import IncidentPayload
from app.repositories.idempotency import idempotency_store
from app.core.dependencies import get_incident_processor
from app.services.incident_processor import IncidentProcessor

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook_handler(
    payload: IncidentPayload,
    background_tasks: BackgroundTasks,
    processor: IncidentProcessor = Depends(get_incident_processor),
):
    claimed = await idempotency_store.claim(payload.incident_sys_id)

    if not claimed:
        return {
            "message": "Incident already being processed",
        }

    logger.info(
        "Webhook received for incident %s, description: %s query: (number: %s, priority: %d)",
        payload.incident_sys_id,
        payload.short_description,
        payload.number,
        payload.priority,
    )

    background_tasks.add_task(processor.process_incident, payload)

    return {"message": "Webhook received", "payload": payload}

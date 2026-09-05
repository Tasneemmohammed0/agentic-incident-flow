import logging

from fastapi import APIRouter, Depends, status

from app.models.incident import IncidentPayload
from app.repositories.idempotency import identempotency_store
from app.dependencies import get_incident_processor
from app.services.incident_processor import IncidentProcessor

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook_handler(
    payload: IncidentPayload,
    processor: IncidentProcessor = Depends(get_incident_processor),
):
    claimed = await identempotency_store.claim(payload.incident_sys_id)

    logger.info(
        "Webhook received for incident %s (number: %s, priority: %d)",
        payload.incident_sys_id,
        payload.number,
        payload.priority,
    )

    if not claimed:
        return {
            "message": "Duplicate webhook received",
        }
    return {"message": "Webhook received", "payload": payload}

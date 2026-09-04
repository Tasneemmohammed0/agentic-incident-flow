import logging

from fastapi import APIRouter, status

from app.models.incident import IncidentPayload
from app.repositories.idempotency import identempotency_store

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook_handler(payload: IncidentPayload):
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

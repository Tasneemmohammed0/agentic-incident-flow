from fastapi import APIRouter, status

from app.models.incident import IncidentPayload

router = APIRouter()


@router.post("/webhook", status_code=status.HTTP_202_ACCEPTED)
async def webhook_handler(payload: IncidentPayload):
    return {"message": "Webhook received", "payload": payload}

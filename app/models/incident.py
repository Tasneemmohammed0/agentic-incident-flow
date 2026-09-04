from pydantic import BaseModel, Field


class IncidentPayload(BaseModel):
    incident_sys_id: str = Field(
        min_length=1, description="The sys_id of the incident in ServiceNow"
    )
    number: str = Field(min_length=1, description="The incident number in ServiceNow")
    short_description: str = Field(
        min_length=1, description="The short description of the incident"
    )
    description: str | None = None
    priority: int = Field(ge=1, le=5, description="The priority of the incident (1-5)")

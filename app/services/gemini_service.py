from __future__ import annotations

import logging
from google.genai import types
from google import genai

from app.models.knowledge_base import KnowledgeBase
from app.prompt import build_prompt
from app.models.incident import IncidentPayload
from app.models.decision import IncidentDecision

logger = logging.getLogger(__name__)


class GeminiService:

    def __init__(self, api_key: str, model: str) -> None:
        """
        Args:
            api_key: Gemini API key (see config.GEMINI_API_KEY).
            model: Gemini model name to call (see config.GEMINI_MODEL).
        """
        self._model = model
        self._client = genai.Client(api_key=api_key)

    async def decide(
        self, kb_data: KnowledgeBase, incident: IncidentPayload
    ) -> IncidentDecision:
        """
        Args:
            kb_data: Knowledge base data to provide context for the decision.
            incident: Incident data to provide context for the decision.

        Returns:
            IncidentDecision: The decision made by the Gemini model.
        """
        prompt = build_prompt(kb_data, incident)
        logger.debug(
            "Sending incident %s to Gemini (%s)",
            incident.number,
            self._model,
        )

        try:
            response = await self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=IncidentDecision,
                ),
            )

            if not response.text:
                logger.warning(
                    "Gemini returned empty response for incident %s",
                    incident.number,
                )
                return IncidentDecision(
                    decision="escalate",
                    message="The incident requires manual review because automated triage was unavailable.",
                )

            parsed = IncidentDecision.model_validate_json(response.text)

        except Exception as exc:
            logger.exception(
                "Gemini call failed for incident %s",
                incident.number,
            )

            return IncidentDecision(
                decision="escalate",
                message="The incident requires manual review because automated triage was unavailable.",
            )

        return parsed

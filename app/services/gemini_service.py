from __future__ import annotations

import asyncio
import logging

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.models.knowledge_base import KnowledgeBase
from app.models.incident import IncidentPayload
from app.models.decision import IncidentDecision
from app.prompt import build_prompt

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
            IncidentDecision: The decision made by Gemini.
            Falls back to ESCALATE if Gemini is unavailable.
        """

        prompt = build_prompt(kb_data, incident)

        logger.debug(
            "Sending incident %s to Gemini (%s)",
            incident.number,
            self._model,
        )

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0,
                        response_mime_type="application/json",
                        response_schema=IncidentDecision,
                    ),
                )

                logger.debug(
                    "Raw Gemini response for %s:\n%s",
                    incident.number,
                    response.text,
                )

                if not response.text:
                    logger.warning(
                        "Gemini returned empty response for incident %s",
                        incident.number,
                    )
                    return self._fallback_decision(incident)

                return IncidentDecision.model_validate_json(response.text)

            except APIError as exc:
                # Retry only transient Gemini errors.
                if exc.code in (429, 500, 502, 503, 504):
                    if attempt < max_attempts:
                        delay = 2 ** (attempt - 1)

                        logger.warning(
                            "Gemini temporarily unavailable for incident %s "
                            "(attempt %d/%d, status=%s). "
                            "Retrying in %d seconds...",
                            incident.number,
                            attempt,
                            max_attempts,
                            exc.code,
                            delay,
                        )

                        await asyncio.sleep(delay)
                        continue

                    logger.error(
                        "Gemini unavailable after %d attempts for incident %s",
                        max_attempts,
                        incident.number,
                    )

                else:
                    logger.exception(
                        "Gemini API error for incident %s: %s",
                        incident.number,
                        exc,
                    )

                return self._fallback_decision(incident)

            except Exception:
                logger.exception(
                    "Unexpected Gemini error for incident %s",
                    incident.number,
                )

                return self._fallback_decision(incident)

        # Defensive fallback. The loop should never reach this point.
        return self._fallback_decision(incident)

    @staticmethod
    def _fallback_decision(incident: IncidentPayload) -> IncidentDecision:
        """
        Safe fallback when automated triage is unavailable.
        """

        logger.warning(
            "Using fallback ESCALATE decision for incident %s",
            incident.number,
        )

        return IncidentDecision(
            decision="escalate",
            message=(
                "The incident requires manual review because "
                "automated triage was unavailable."
            ),
        )

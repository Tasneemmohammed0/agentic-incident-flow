from __future__ import annotations

import json
import logging
import re

from google import genai

from app.prompt import build_prompt
from app.models.incident import IncidentPayload
from app.models.decision import DecisionPayload

logger = logging.getLogger(__name__)

VALID_DECISIONS = {"respond", "ask", "escalate"}


class GeminiService:

    def __init__(self, api_key: str, model: str) -> None:
        """
        Args:
            api_key: Gemini API key (see config.GEMINI_API_KEY).
            model: Gemini model name to call (see config.GEMINI_MODEL).
        """
        self._model = model
        self._client = genai.Client(api_key=api_key)

    def decide(self, kb_data: dict, incident: IncidentPayload) -> DecisionPayload:
        """
        Args:
            kb_data: Knowledge base data to provide context for the decision.
            incident: Incident data to provide context for the decision.

        Returns:
            DecisionPayload: The decision made by the Gemini model.
        """
        prompt = build_prompt(kb_data, incident)
        logger.debug("Prompt sent to Gemini:\n%s", prompt)

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            raw_text = response.text or ""

        except Exception as exc:
            logger.exception("Gemini call failed for %s: %s", incident.number, exc)
            return {"decision": "escalate", "message": f"Gemini call failed: {exc}"}

        if not raw_text:
            logger.warning("Gemini response was empty for %s", incident.number)
            return {
                "decision": "escalate",
                "message": "Gemini response was empty",
            }

        parsed = self._extract_json(raw_text)
        if not parsed or "decision" not in parsed or "message" not in parsed:
            logger.warning(
                "Gemini response could not be parsed for %s: %s",
                incident.number,
                raw_text,
            )
            return {
                "decision": "escalate",
                "message": f"Gemini response could not be parsed: {raw_text}",
            }

        if parsed["decision"] not in VALID_DECISIONS:
            logger.warning(
                "Gemini response had invalid decision for %s: %s",
                incident.number,
                parsed["decision"],
            )
            return {
                "decision": "escalate",
                "message": f"Gemini response had invalid decision: {parsed['decision']}",
            }

    @staticmethod
    def _kb_articles_to_text(kb_data: dict) -> str:
        """Flattens the KB JSON into plain text for the prompt."""
        lines = []
        for article in kb_data.get("articles", []):
            lines.append(f"[{article['id']}] {article['title']}\n{article['body']}")
        return "\n\n".join(lines)

    @staticmethod
    def _extract_json(raw_text: str) -> dict | None:
        text = raw_text.strip()
        text = re.sub(r"^```(json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    return None
        return None

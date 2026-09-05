from __future__ import annotations

import logging
import httpx

logger = logging.getLogger(__name__)


class ServiceNowService:
    """
    ServiceNowService is responsible for interacting with the ServiceNow API.
    It provides methods to create, update, and retrieve incidents from ServiceNow.
    """

    def __init__(
        self, instance_url: str, username: str, password: str, timeout: float = 15.0
    ):

        self._base_url = instance_url.rstrip("/")
        self._auth = (username, password)
        self._timeout = timeout

        logger.info(
            "ServiceNow configured: instance=%s username=%s",
            self._base_url,
            username,
        )

    def _table_url(self, sys_id: str) -> str:
        return f"{self._base_url}/api/now/table/incident/{sys_id}"

    async def _patch(self, sys_id: str, body: dict) -> None:
        url = self._table_url(sys_id)
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.patch(
                url, json=body, auth=self._auth, headers=headers
            )
            response.raise_for_status()

    async def resolve_with_solution(self, sys_id: str, message: str) -> None:
        """decision == 'respond': set work_notes AND close_notes to the
        solution, resolve the ticket, and set a valid close_code."""
        body = {
            "work_notes": message,
            "state": "6",  # Resolved
            "close_notes": message,
            "close_code": "Solved (Permanently)",
        }
        await self._patch(sys_id, body)

    async def add_clarifying_question(self, sys_id: str, message: str) -> None:
        """decision == 'ask': customer-visible comment, not a work note."""
        await self._patch(sys_id, {"comments": message})

    async def add_escalation_note(self, sys_id: str, message: str) -> None:
        """decision == 'escalate': internal-only work note."""
        await self._patch(sys_id, {"work_notes": f"Escalated by AI triage: {message}"})

    async def write_back(self, sys_id: str, decision: str, message: str) -> None:
        """Dispatch to the right write-back call for a decision."""
        if decision == "respond":
            await self.resolve_with_solution(sys_id, message)
        elif decision == "ask":
            await self.add_clarifying_question(sys_id, message)
        else:
            await self.add_escalation_note(sys_id, message)
        logger.info("Wrote back decision=%s for sys_id=%s", decision, sys_id)

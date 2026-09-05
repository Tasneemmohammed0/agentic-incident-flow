#!/usr/bin/env python3

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.models.knowledge_base import KnowledgeBase
from app.models.incident import IncidentPayload
from app.services.gemini_service import GeminiService

DEFAULT_KB_PATH = Path("data/kb_articles.json")
DEFAULT_TESTS_PATH = Path("data/test_incidents.json")
DEFAULT_MODEL = "gemini-2.5-flash"

from dotenv import load_dotenv

load_dotenv(override=True)


@dataclass
class CaseResult:
    number: str
    short_description: str
    expected: str
    actual: str | None
    message: str | None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.actual == self.expected


def load_knowledge_base(path: Path) -> KnowledgeBase:
    data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, list):
        data = {"articles": data}
    return KnowledgeBase.model_validate(data)


def load_test_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data["incidents"] if isinstance(data, dict) else data
    if not cases:
        raise ValueError(f"No test incidents found in {path}")
    return cases


def build_payload(index: int, case: dict[str, Any]) -> IncidentPayload:
    return IncidentPayload(
        incident_sys_id=case.get("incident_sys_id", f"test-sys-id-{index}"),
        number=case.get("number", f"TEST{index:04d}"),
        short_description=case["short_description"],
        description=case["description"],
        priority=case.get("priority", 3),
    )


async def run_case(
    gemini: GeminiService, kb: KnowledgeBase, index: int, case: dict[str, Any]
) -> CaseResult:
    payload = build_payload(index, case)
    expected = case["expected_decision"]

    try:
        decision = await gemini.decide(kb, payload)
    except Exception as exc:
        return CaseResult(
            number=payload.number,
            short_description=payload.short_description,
            expected=expected,
            actual=None,
            message=None,
            error=str(exc),
        )

    return CaseResult(
        number=payload.number,
        short_description=payload.short_description,
        expected=expected,
        actual=decision.decision,
        message=decision.message,
    )


async def run_all(kb_path: Path, tests_path: Path, model: str) -> list[CaseResult]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(
            "GEMINI_API_KEY is not set. Export it, or put it in your .env.",
            file=sys.stderr,
        )
        sys.exit(2)

    kb = load_knowledge_base(kb_path)
    cases = load_test_cases(tests_path)
    gemini = GeminiService(api_key=api_key, model=model)

    results = []
    for i, case in enumerate(cases, start=1):
        results.append(await run_case(gemini, kb, i, case))
    return results


def print_report(results: list[CaseResult], verbose: bool) -> bool:
    all_passed = True
    width = max((len(r.short_description) for r in results), default=20)

    for r in results:
        if r.error:
            status = "ERROR"
            all_passed = False
        elif r.passed:
            status = "PASS"
        else:
            status = "FAIL"
            all_passed = False

        print(
            f"[{status:5}] {r.short_description:<{width}}  "
            f"expected={r.expected:<9} actual={r.actual}"
        )
        if r.error:
            print(f"          error: {r.error}")
        elif verbose and r.message:
            print(f"          message: {r.message}")

    passed = sum(1 for r in results if r.passed)
    print(f"\n{passed}/{len(results)} test incidents matched their expected decision.")
    return all_passed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kb", type=Path, default=DEFAULT_KB_PATH, help="Path to kb_articles.json"
    )
    parser.add_argument(
        "--tests",
        type=Path,
        default=DEFAULT_TESTS_PATH,
        help="Path to test_incidents.json",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("GEMINI_MODEL", DEFAULT_MODEL),
        help="Gemini model to use (defaults to $GEMINI_MODEL, else %(default)s)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Also print each decision's message",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for label, path in (("knowledge base", args.kb), ("test incidents", args.tests)):
        if not path.exists():
            print(f"Can't find the {label} file at {path}", file=sys.stderr)
            sys.exit(2)

    results = asyncio.run(run_all(args.kb, args.tests, args.model))
    all_passed = print_report(results, args.verbose)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

from app.models.incident import IncidentPayload
from app.models.knowledge_base import KnowledgeBase

DECISION_PROMPT_TEMPLATE = """You are an IT support triage assistant.

Use ONLY the knowledge articles provided below. Do not use outside
knowledge, invent facts, or invent troubleshooting steps.

KNOWLEDGE ARTICLES:
{kb_articles}

INCOMING TICKET:
Number: {number}
Priority: {priority}
Short description: {short_description}
Description: {description}

Choose exactly ONE decision:

1. "respond"
   Use only when the ticket contains enough information to confidently
   apply a knowledge article's solution to the reported problem.

   The article must clearly match the problem AND the ticket must provide
   enough detail to justify giving the article's troubleshooting steps.

2. "ask"
   Use when a knowledge article may apply, but the ticket is too vague
   to confidently determine that its solution applies.

   Ask ONE short, specific clarifying question.
   Do not provide troubleshooting steps.

3. "escalate"
   Use when no knowledge article applies or the request is outside the
   provided technical knowledge.

Give ONE short sentence explaining why it must be escalated.

IMPORTANT RULES:

IMPORTANT:

* Do not treat a general symptom as sufficient evidence for "respond".
* Do not assume missing technical details.
* If the ticket is vague and an article only generally matches the symptom,
  choose "ask".
* "respond" requires enough information to justify the article's solution.
* "ask" is preferred when there is a plausible article match but important
  information is missing.
* For "ask", ask exactly ONE clarifying question and do not provide a solution.

Return ONLY valid JSON with exactly these two fields:

{{
"decision": "respond | ask | escalate",
"message": "short message"
}}

Do not include markdown, explanations, reasoning, or additional fields.
"""


def _kb_articles_to_text(kb_data: KnowledgeBase) -> str:
    return "\n\n".join(
        f"Article {article.id}: {article.text}" for article in kb_data.articles
    )


def build_prompt(
    kb_data: KnowledgeBase,
    incident: IncidentPayload,
) -> str:
    return DECISION_PROMPT_TEMPLATE.format(
        kb_articles=_kb_articles_to_text(kb_data),
        number=incident.number,
        priority=incident.priority,
        short_description=incident.short_description,
        description=incident.description,
    )

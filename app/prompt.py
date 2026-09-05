from app.models.incident import IncidentPayload
from app.models.knowledge_base import KnowledgeBase

DECISION_PROMPT_TEMPLATE = """You are an IT support triage assistant.

Use ONLY the knowledge articles provided below. Do not use outside
knowledge, invent facts, or invent troubleshooting steps.

KNOWLEDGE ARTICLES:
{kb_articles}

Choose exactly ONE decision:

1. "respond"
   Use only when an article clearly matches the problem AND the ticket
   contains enough concrete detail to confidently apply that article's
   solution. A short description can still be "enough detail" if it adds
   something diagnostic (timing, what was already tried, what changed
   recently, a specific symptom).
   The "message" field must contain the concrete solution/steps from the
   matching article, written for the customer.

2. "ask"
   Use when an article may apply on topic, but the ticket does not add
   any diagnostic detail beyond restating the short description (e.g.
   "it doesn't work", "it's broken", "still not working"). If the
   ticket's description gives you nothing more to go on than its title,
   that is NOT enough information for "respond" — choose "ask" instead.
   The "message" field must be exactly ONE short, specific clarifying
   question, written for the customer. Do not include troubleshooting
   steps in it.

3. "escalate"
   Use when no supplied article applies, or the request is outside the
   provided technical knowledge entirely (e.g. HR/admin requests).
   The "message" field must be ONE short sentence, for internal readers,
   explaining why it needs to be escalated.

IMPORTANT RULES:
* Do not treat a general symptom as sufficient evidence for "respond".
* Do not assume missing technical details — if they're not in the
  ticket, they're not available.
* If the ticket's description does not add any new diagnostic detail
  beyond what the short description already implies, treat it as
  insufficient information and choose "ask", even if an article's
  title matches the topic.
* "respond" requires the ticket to justify the article's specific
  solution, not just share its general topic.

EXAMPLES (for calibration only — these are not real tickets, ignore
their content when evaluating the actual ticket below):

Example A — respond:
  Short description: "Can't access system"
  Description: "It says my password expired when I tried to log in
  this morning."
  Why: an article covers expired-password access issues, and the
  ticket names the specific trigger (expired password), which is
  enough to confidently apply the reset-password steps.
  -> decision: respond

Example B — ask:
  Short description: "Internet is slow"
  Description: "It's just slow today."
  Why: an article about slow network might apply on topic, but "slow
  today" adds no detail about when it started, what's affected, or
  what's already been tried. Not enough to confidently apply the fix.
  -> decision: ask

INCOMING TICKET:
Number: {number}
Priority: {priority}
Short description: {short_description}
Description: {description}

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

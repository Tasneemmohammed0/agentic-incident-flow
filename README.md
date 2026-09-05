# Agentic Incident Flow

A small service that watches for new incidents on a ServiceNow PDI, asks Gemini what to do about each one using a fixed set of knowledge-base articles, and writes the decision straight back onto the ticket. No human touches it in between.

Built for the Sprints × BARQ Systems AI Engineering Internship.

## How it works

1. **A ticket is created** on a ServiceNow developer instance (PDI).
2. **A Business Rule fires** on insert and POSTs the incident to this service as JSON.
3. **This service asks Gemini for a decision** (`respond`, `ask`, or `escalate`) using only the five knowledge-base articles it's given. Gemini never gets to use outside knowledge.
4. **This service writes the decision back** onto the same ticket via the ServiceNow REST API.

```
ServiceNow PDI ──(Business Rule)──▶ POST /webhook ──▶ Gemini ──▶ ServiceNow REST API ──▶ same ticket, updated
```

The webhook responds in under ~2 seconds; the Gemini call and the write-back happen afterwards in a background task.

## Project structure

```
app/
├── main.py                      # FastAPI app, health checks, validation error handler
├── api/
│   └── webhook.py                # POST /webhook
├── core/
│   └── dependencies.py           # DI wiring for IncidentProcessor
├── models/
│   ├── incident.py                # IncidentPayload (the inbound webhook body)
│   ├── decision.py                # IncidentDecision (decision + message)
│   └── knowledge_base.py          # KnowledgeBase / KBArticle
├── repositories/
│   └── idempotency.py             # In-memory "have we seen this incident?" guard
├── services/
│   ├── gemini_service.py          # Calls Gemini, retries transient errors, falls back to escalate
│   ├── servicenow_service.py      # Writes decisions back to the incident record
│   └── incident_processor.py      # Ties Gemini decision + ServiceNow write-back together
└── prompt.py                      # The exact prompt sent to Gemini

scripts/
└── test_incidents.py              # Runs the three fixture tickets through the real pipeline

data/
├── kb_articles.json               # The five knowledge-base articles Gemini is allowed to use
└── test_incidents.json            # The three test tickets and their expected decisions

business_rule.js                   # Paste into the PDI — fires the webhook on incident insert
justfile                           # Task runner shortcuts (see below)
.env.example                       # Required environment variables (no real values)
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management
- [just](https://github.com/casey/just) (optional, but the commands below assume it — everything it runs is also a plain `uv run ...` command if you'd rather skip it)
- A free ServiceNow **Personal Developer Instance** (PDI)
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/) — no credit card needed
- [ngrok](https://ngrok.com/) or any tunnel that gives your local service a public URL

## Setup

```bash
git clone https://github.com/Tasneemmohammed0/agentic-incident-flow.git
cd agentic-incident-flow

just install        # or: uv sync

cp .env.example .env
# now fill in the values below
```

### Environment variables

| Variable | What it's for |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key from Google AI Studio |
| `GEMINI_MODEL` | Which Gemini model to call, e.g. `gemini-2.5-flash` |
| `SERVICENOW_INSTANCE_URL` | Your PDI URL, e.g. `https://dev123456.service-now.com` |
| `SERVICENOW_USERNAME` | ServiceNow account used for the REST write-back |
| `SERVICENOW_PASSWORD` | Password for that account |
| `DEBUG` | `true`/`false` — toggles more verbose logging |


## Running it locally

```bash
just run                  # uv run uvicorn app.main:app --reload
# or on a specific port:
just run-port 8080
```

Check it's alive:

```bash
curl http://localhost:8000/health
```

## Wiring up ServiceNow

1. Spin up your PDI (this can take a few minutes to provision the first time).
2. Expose your local service publicly:
   ```bash
   ngrok http 8000
   ```
   Copy the `https://...ngrok-free.app` URL it gives you.
3. In the PDI, go to **System Definition → Business Rules** and create a new rule on the `incident` table:
   - **When:** after insert
   - **Script:** paste in `business_rule.js` and swap the placeholder URL for `<your-ngrok-url>/webhook`
4. Create a test incident in the PDI. Your local service should log an incoming webhook request within a second or two, and the ticket should update automatically once Gemini responds.

Heads up: the free ngrok URL changes every time you restart it, so you'll need to update the Business Rule's URL each time unless you're on a paid ngrok plan with a reserved domain.

## The decision logic

Gemini is only allowed to use the five articles in `data/kb_articles.json` — nothing from outside them. The full prompt lives in `app/prompt.py` and always returns strict JSON:

```json
{
  "decision": "respond | ask | escalate",
  "message": "short message"
}
```

- **`respond`** — an article clearly covers the problem *and* the ticket has enough concrete detail to apply it. `message` becomes the actual solution.
- **`ask`** — an article might apply, but the ticket doesn't add any detail beyond restating its own title. `message` becomes one clarifying question.
- **`escalate`** — nothing in the knowledge base covers it (or the call fails), and a human needs to look at it. `message` is a short internal note.

### What gets written back to ServiceNow

| Decision | ServiceNow effect |
|---|---|
| `respond` | Sets `work_notes` and `close_notes` to the solution, resolves the ticket (`state = 6`), sets `close_code = Solved (Permanently)` |
| `ask` | Adds a **customer-visible comment** with the clarifying question |
| `escalate` | Adds an **internal-only work note** flagging it for a human |

## Reliability details

- **Idempotency:** each incoming `incident_sys_id` is claimed before processing starts. If the same incident arrives twice (retries, duplicate Business Rule fires, etc.), the second one is a no-op. This is an in-memory guard, so it resets if the service restarts.
- **Gemini retries:** transient errors (`429`, `500`, `502`, `503`, `504`) are retried up to 3 times with exponential backoff. Anything else — or running out of retries — falls back to an automatic `escalate` decision, so a flaky API call never leaves a ticket untouched.
- **Bad payloads:** a malformed webhook body doesn't crash the service — it's logged (including the raw body) and answered with a `422` and a clear error detail.

## Testing

The three fixture tickets in `data/test_incidents.json` are meant to each produce a specific decision:

Run them against the real Gemini pipeline (no ServiceNow or webhook involved — this hits `GeminiService` directly):

```bash
just test
```

which runs:

```bash
uv run python -m scripts.test_incidents \
  --kb data/kb_articles.json \
  --tests data/test_incidents.json \
  --verbose
```

You'll get a `PASS`/`FAIL`/`ERROR` line per ticket, a summary count, and a non-zero exit code if anything didn't match — so it's safe to drop into CI.

## Other `just` commands

| Command | What it does |
|---|---|
| `just` | Lists all available recipes |
| `just install` | Installs dependencies (`uv sync`) |
| `just add <package>` | Adds a new dependency |
| `just run` | Starts the dev server with auto-reload |
| `just run-port <port>` | Same, on a custom port |
| `just test` | Runs the fixture tickets against the Gemini pipeline |
| `just clean` | Removes `__pycache__` and `.pyc` files |

## API reference

**`GET /`** and **`GET /health`** — basic liveness checks, no auth.

**`POST /webhook`** — the ServiceNow Business Rule target. Returns `202` immediately; processing happens in the background.

Example body (matches `payload_contract.json`):

```json
{
  "incident_sys_id": "9c3f1a2e8f7a1010f...",
  "number": "INC0010023",
  "short_description": "Printer not printing after office move",
  "description": "It was working yesterday. I tried turning it off and on.",
  "priority": 3
}
```
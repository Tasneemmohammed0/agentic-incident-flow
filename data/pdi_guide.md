# Task 0 — ServiceNow PDI Guide

You do not need any ServiceNow experience. Follow these steps in order.

## Step 1 — Get your free developer instance (PDI)

1. Go to https://developer.servicenow.com and create a free account.
2. Sign in, then click **Request Instance** (choose the latest release).
3. After a few minutes you will get:
   - your instance URL, like `https://devXXXXXX.service-now.com`
   - an `admin` username and password.
4. Open the instance URL and log in as `admin`.

Note: a PDI goes to sleep after some hours of inactivity. If it looks down,
go back to the developer portal and wake it up.

## Step 2 — Expose your local service

Your Python service will run on your laptop, so ServiceNow needs a public URL
to reach it.

1. Install ngrok from https://ngrok.com (free).
2. Start your FastAPI service on port 8000.
3. Run: `ngrok http 8000`
4. Copy the `https://....ngrok-free.app` URL. This is your public endpoint.

Every time you restart ngrok the URL changes — remember to update the
Business Rule (Step 3) when it does.

## Step 3 — Create the Business Rule (sends new incidents to your service)

1. In your PDI, use the top-left search ("All") and type **Business Rules**
   (under System Definition). Open it and click **New**.
2. Fill in:
   - **Name:** `Task0 - Send Incident to Agent`
   - **Table:** `Incident [incident]`
   - **Advanced:** checked
   - **When to run:** When = `after`, and check **Insert**
3. Open the **Advanced** tab and paste the script from `business_rule.js`
   (in this asset pack).
4. In the script, replace `YOUR_ENDPOINT` with your ngrok URL, keeping
   `/webhook` at the end. Example:
   `https://ab12cd34.ngrok-free.app/webhook`
5. Click **Submit**.

## Step 4 — Test the trigger

1. In your PDI, search "All" for **Incident**, then **Create New**.
2. Fill Short description with anything (e.g. "Printer not printing after
   office move") and click **Submit**.
3. Watch your FastAPI logs — the JSON payload should arrive within seconds.

If nothing arrives:
- Check **System Logs > System Log > All** in the PDI and search for `Task0`
  (the script writes log lines with `gs.info` / `gs.error`).
- Check that ngrok is still running and the URL in the Business Rule matches.

## Step 5 — Write the result back to the incident

Your service updates the same incident through the standard Table API:

```
PATCH https://devXXXXXX.service-now.com/api/now/table/incident/{incident_sys_id}
Authorization: Basic <admin username and password>
Content-Type: application/json
```

Useful fields for the body:

| Decision  | Fields to set |
|-----------|----------------|
| respond   | `work_notes` (the solution), `state`: `6`, `close_notes` (the solution), `close_code`: `"Solved (Permanently)"` or any valid close code |
| ask       | `comments` (your clarifying question — comments are visible to the user) |
| escalate  | `work_notes` (why it is escalated) |

Tip: `work_notes` are internal; `comments` are customer-visible.
You can verify each update by refreshing the incident form in the PDI.

## Step 6 — You are done when…

Creating an incident in the PDI makes your service run, call Gemini, and the
decision appears back on the same ticket — with no manual steps in between.

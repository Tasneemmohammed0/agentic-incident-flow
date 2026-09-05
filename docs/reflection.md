# Reflection

Two things gave me the most trouble in this task, and honestly, neither was what I expected to be difficult when I started.

## ServiceNow authentication

The biggest headache was getting the ServiceNow REST API write-back working. My Python app kept getting `401 Unauthorized`, even though I could log into ServiceNow normally and the REST API seemed to be working.

At first, I thought something was wrong with my Python request or the ServiceNow permissions. I spent quite a bit of time checking the integration user, roles, REST API settings, and credentials.

The actual issue turned out to be related to **Basic Authentication restrictions in newer ServiceNow PDI releases**. The API user needed the `snc_basic_auth_api_access` role for Basic Auth requests. Once I added that role and configured the integration user correctly, I was able to authenticate and successfully test the PATCH request against the incident.

One thing that helped a lot was testing the REST API separately with `curl`. It allowed me to isolate the problem and confirm whether the issue was with my Python application or with ServiceNow authentication. This was probably the biggest debugging lesson for me from the task: when an integration fails, test each part separately instead of assuming the problem is in the code.

## Respond vs. ask

The other challenging part was getting Gemini to consistently understand the difference between `respond` and `ask`.

At first, I thought the rule would be simple: if a knowledge article matches the ticket, respond; if the ticket is vague, ask. But I realized that "vague" isn't really the important part.

For example, the printer test is also quite short, but it gives enough useful information to apply the knowledge article. The email test is different. The user says, `"It just doesn't work."`, which basically adds no useful information beyond the title.

Gemini initially saw "Cannot send email", found the email knowledge article, and immediately returned its troubleshooting steps. The problem was that it was matching the topic correctly but wasn't checking whether there was enough information in the ticket to confidently apply the solution.

I had to keep refining the prompt to make that distinction clearer. The main change was making it explicit that a relevant article is not enough by itself. For `respond`, the ticket also needs to contain enough information to justify using that article's solution. If the article might apply but important information is missing, the correct decision is `ask`.

This was probably the part of the task where I learned the most about working with LLMs. Writing a rule that sounds clear to a person doesn't always mean the model will interpret it in the way you intended, so testing, comparing results, and refining the prompt were necessary.

## What I'd improve with more time

With more time, I would replace the current in-memory idempotency tracking with persistent storage. Right now, restarting the application clears the processed-incident state, which is acceptable for this task but wouldn't be reliable in a real system.

I would also add authentication or another protection mechanism to the webhook. Since the service is exposed through ngrok, anyone who discovers the URL could potentially send requests to it. That would need to be addressed before using this outside a development environment.

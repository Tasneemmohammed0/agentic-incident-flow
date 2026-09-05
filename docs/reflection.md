# Reflection

Two things gave me the most trouble in this task, and honestly, neither was what I expected to be difficult when I started.

## ServiceNow authentication

The biggest headache was getting the ServiceNow REST API write-back working. My Python app kept getting `401 Unauthorized`, which was confusing because when I tested the same integration account and credentials manually with `curl`, I was getting `200 OK`.

At first, I thought the problem was on the ServiceNow side. I checked the integration user, roles, permissions, and REST API settings, and spent quite a bit of time trying to figure out what was wrong.

Eventually, I tested the API separately with `curl` and confirmed that the credentials and PATCH request were actually working. That helped me narrow the problem down to my own application.

The issue was related to how my application loads its configuration. I use `@lru_cache` for the settings and for creating the service dependencies, so the ServiceNow client keeps the credentials it was created with until the application restarts. I had updated the password in my `.env`, but I hadn't fully restarted the server, so the running application was still using the old password.

It was a good reminder that when debugging integrations, it's important to isolate each part of the system instead of assuming the external service is the problem. Testing the API independently with `curl` saved me a lot of time.

## Respond vs. ask

The other challenging part was getting Gemini to consistently understand the difference between `respond` and `ask`.

At first, I thought the rule would be simple: if a knowledge article matches the ticket, respond; if the ticket is vague, ask. But I realized that "vague" isn't really the important part.

For example, the printer test is also quite short, but it gives enough useful information to apply the knowledge article. The email test is different. The user says, `"It just doesn't work."` which basically adds no useful information beyond the title.

Gemini initially saw "Cannot send email", found the email knowledge article, and immediately returned its troubleshooting steps. The problem was that it was matching the topic correctly but wasn't checking whether there was enough information in the ticket to confidently apply the solution.

I had to keep refining the prompt to make that distinction clearer. The main change was making it explicit that a relevant article is not enough by itself. For `respond`, the ticket also needs to contain enough information to justify using that article's solution. If the article might apply but important information is missing, the correct decision is `ask`.

This was probably the part of the task where I learned the most about working with LLMs. Writing a rule that sounds clear to a person doesn't always mean the model will interpret it in the way you intended, so testing, comparing results, and refining the prompt were necessary.

## What I'd improve with more time

With more time, I replace the current in-memory idempotency tracking with persistent storage. Right now, restarting the application clears the processed-incident state, which is acceptable for this task but wouldn't be reliable in a real system.

I would also add authentication or another protection mechanism to the webhook. Since the service is exposed through ngrok, anyone who discovers the URL could potentially send requests to it. That would need to be addressed before using this outside a development environment.

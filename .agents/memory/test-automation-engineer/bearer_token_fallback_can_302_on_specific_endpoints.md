---
name: Bearer token fallback can 302 on specific endpoints
description: Every entity client falls back to ELITEA_API_TOKEN when no browser cookies are passed — but that fallback isn't guaranteed to work on every endpoint. Verify live before trusting it.
type: feedback
---

Confirmed live 2026-10-16 (ELITEA-3252/3253/3254/3255): a well-formed,
non-expired `ELITEA_API_TOKEN` 302-redirects to `/access_denied` on the
Project Context endpoints (`/elitea_core/project_context/prompt_lib/{id}/
project-context`), even though every other entity client in
`automation/api/client.py` (`ConversationAPI`, `AgentAPI`, `PipelineAPI`,
`CredentialAPI`, …) silently falls back to this exact same bearer token when
`browser_cookies` is empty, and that fallback has always worked for them.

Symptom if you don't catch it: `requests.exceptions.TooManyRedirects:
Exceeded 30 redirects` (the 302 loop never terminates because the final
`/access_denied` page itself keeps redirecting through auth).

Don't assume "the generic APIClient()/bearer fallback works everywhere
because it works on the entity clients I've already tested." Before writing
a new entity client (or a bare `APIClient().get(...)` call) against an
endpoint nobody has API-tested yet, do a quick live check with BOTH auth
modes (bearer token, and cookies extracted from a Playwright context after
navigating once) before building the fixture/client around whichever one you
assumed would work. If bearer 302s, build the client cookie-only (see
`ProjectContextAPI`) and don't bother wiring the bearer branch at all — a
silent bearer fallback that 302s is worse than no fallback, because it reads
as "unauthenticated" in logs when the real cause is "wrong auth mode for this
specific endpoint."

---
name: Review check — a numeric literal in a diff is "constant or config?"
description: Testid-provenance checks cannot catch a value that never comes from main. Trace every asserted number to its source.
type: feedback
---

**The review move.** For every numeric literal a diff asserts against rendered UI
(a limit, a remaining-capacity counter, a quota, a page size), ask *constant or
config?* and require the source pointer. One grep. It catches an environment
coupling that **no testid-provenance check can see, because the value never comes
from `main` at all** — it comes from a backend response.

If the number originates in a config query, the compliant shape is a **runtime
baseline + delta**: read it, assert `after == before - 1`. Never the endpoints.

**Worked case — ELITEA-0500 attach-oracle repair, 2026-08-28, review blocker.**
A `main`-targeted spec whose whole purpose was to kill a green-local/red-DEV
assertion shipped a fresh one: `to_contain_text("10 left")` / `"9 left"`.

```
AttachmentButton.jsx:194        remainingLabel = `${remainingAttachments} left`
attachmentValidationUtils.js:361  limits.MAX_ATTACHMENTS - attachments.length
useChatConfig.js:27             data.chat_max_upload_count ?? ATTACHMENT_LIMITS
                                data = useGetChatConfigQuery({ projectId })   # per-project, per-env
```

Two distinct failures, and the second is the one you would not predict:

1. **Env divergence** — any backend configured to anything but 10 fails outright.
2. **In-flight fallback race** — `useChatConfig.js:22-24` is
   `if (!data) return ATTACHMENT_LIMITS`, so the UI renders the *static fallback*
   until the config query lands, then flips. A baseline read too early latches a
   value the product is about to replace. Closing this needs a passive
   `page.expect_response(...)` gate on the config endpoint around navigation —
   not a sleep, not a poll.

**Tell for the second failure: a client-side fallback next to a server value.**
Whenever a hook reads config with a local default, there is a window where the
UI shows the default. Any test reading that surface needs the response gate.

**Reviewer-side signal that a fix is real:** ask for a mutation control. Inverting
`f"{before - 1} left"` to `f"{before} left"` produced
`expected '10 left' / Actual value: 'Attach Files9 left'` — which proves in one
run that the baseline was read live, that the counter moves, and that the
assertion is not vacuous.

Implementer-side companion (same incident, different angle):
`.agents/memory/test-automation-engineer/ui_numeric_literals_can_be_backend_config.md`.

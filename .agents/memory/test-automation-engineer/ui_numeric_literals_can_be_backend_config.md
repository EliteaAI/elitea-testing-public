---
name: A number rendered in the UI may be backend config — trace it before asserting it
description: Assert the DELTA with a runtime baseline; a hardcoded count passes provenance checks and still breaks per-env
type: feedback
---

**Before asserting any numeric literal a UI renders, trace where the number comes
from.** If it originates from a backend config query rather than a client
constant, hardcoding it produces a spec that is green on the backend you happened
to develop against and red everywhere else.

Worked case (ELITEA-0500, review blocker, fix round 1). The chat attachment
counter renders `"10 left"`, and `10` looks like a product constant. It is not:

```
AttachmentButton.jsx      remainingLabel = `${remainingAttachments} left`
attachmentValidationUtils.js  limits.MAX_ATTACHMENTS - attachments.length
useChatConfig.js:27       MAX_ATTACHMENTS: data.chat_max_upload_count ?? ATTACHMENT_LIMITS.MAX_ATTACHMENTS
                          data = useGetChatConfigQuery({ projectId })
```

`common/constants.js` holds only the **client-side fallback**. The real value is
per-project, per-environment.

**Why this class is dangerous: the main-provenance check cannot see it.** Verifying
every testid against EliteaUI `main` says nothing about a *value* that arrives over
the network at runtime. A spec can pass every locator and provenance gate and still
be env-coupled.

**The fix — assert the delta, read the baseline at runtime:**

```python
remaining_before = chat.get_remaining_attachment_slots()   # page object, regex over the control's own text
assert remaining_before >= 1
# ... attach ...
expect(chat.attach_files_button).to_contain_text(f"{remaining_before - 1} left", timeout=...)
```

Full evidentiary value (a live control decrements, a dead one does not), zero env
coupling.

**Also close the in-flight fallback race, don't tolerate it.** `useChatConfig.js`
does `if (!data) return ATTACHMENT_LIMITS`, so the control renders the *fallback*
until the config query lands — read the baseline too early on an env configured to
20 and you latch `10`, then wait forever for `9`. Gate on the config response
itself:

```python
with page.expect_response(lambda r: "/elitea_core/chat_config/prompt_lib/" in r.url, timeout=...):
    chat.navigate_to_chat(conversation_id=conversation_id)
```

**Prove a delta assertion is not vacuous with a red-green control** — invert it to
`f"{remaining_before} left"` and confirm it fails. On ELITEA-0500 that returned
`Actual value: Attach Files9 left`, which proved both that the baseline read a real
runtime `10` and that the counter genuinely moves.

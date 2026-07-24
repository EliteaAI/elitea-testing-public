---
name: blocking wait_for_url hijacked by cross-session navigation
description: A best-effort page.wait_for_url() on a loose regex can be satisfied by an unrelated navigation in this shared dev-token campaign environment, silently corrupting the test — use a non-blocking page.url read instead when the id is genuinely optional
type: feedback
---

ELITEA-2089 (PR #1023): a best-effort conversation-id capture used
`page.wait_for_url(re.compile(r"/chat/\d+"), timeout=UI_ELEMENT_TIMEOUT)`
right after creating an agent participant — reasoning "no message is sent,
so the conversation might not have a numeric URL id yet; wait a bit just in
case." The conversation genuinely NEVER gets a numeric URL id from creating a
participant alone (it stays at the bare `/chat` route — confirmed live,
unlike ELITEA-2166 which sends a message and does get `/chat/{id}`). So the
wait sat idle for the FULL timeout window every run.

During one of those idle windows, the test's browser context navigated to a
COMPLETELY unrelated, pre-existing conversation (`/chat/5704?name=Say+hello…`)
with a DIFFERENT agent (`edited_participant_id=1158` instead of the test's
own `5729`) — satisfying the loose regex and silently corrupting every
subsequent step (the test then clicked a REAL, WORKING edit button — just for
the wrong participant on the wrong conversation). This project's `campaign`
mode runs MANY implementer sessions concurrently against the SAME localhost
dev server under the SAME shared `VITE_DEV_TOKEN` identity — an idle
multi-second wait on a loose URL pattern is exactly the kind of window a
sibling session's own activity (or the app's own "restore last-viewed
conversation" logic, which `ChatPage.navigate_to_chat()`'s docstring already
warns can fire) can hijack.

**Root-caused via targeted debug prints** (page.url logged at 3 checkpoints:
after the row-check, before the edit click, after the edit click) rather than
guessed — the first checkpoint already showed the redirect had NOT happened
yet, isolating the `wait_for_url` call as the exact culprit window.

**Fix:** for a genuinely best-effort/optional capture, use a **non-blocking**
`re.search(r"/chat/(\d+)", page.url)` — no wait at all. If a wait IS needed
for a real assertion (not just best-effort cleanup), make the pattern as
SPECIFIC as possible to your own known state (e.g.
`re.compile(rf"edited_participant_id={agent_id}\b")`, not a bare
`edited_participant_id=`) so an unrelated match can't silently satisfy it —
and pair it with a strict follow-up assertion so a genuine mismatch still
fails loudly instead of silently passing.

---
name: SkillTestPanel runs the skill's own instructions unconditionally — don't assert exact LLM output text
description: Unlike agent-level chat (V2 autonomous invocation gates on a description-trigger match), the Skill test panel always applies the skill's instructions to whatever you type — no trigger gate. A reused fixture skill with its own transform instructions (e.g. "replace spaces with underscores") can turn a literal test message into a differently-formatted response non-deterministically across LLM runs. Assert a substring/non-empty/no-error check, not exact equality, when reusing someone else's fixture skill for an unrelated test.
type: feedback
---

## Rule

The Skill test panel (`SkillDetailPage`/`SkillTestPanel`) is a **direct**
prediction surface — send a message, it runs THIS skill's instructions
against it, no separate V2 trigger-match gate (that gate only exists at the
agent-chat level, for autonomous skill invocation).

If you reuse an existing fixture skill for an UNRELATED test (e.g. testing
model-settings UI, not the skill's own behavior), its instructions still
apply to your test message. `elitea-1735-skill-underscore`'s instructions
("replace ALL spaces between words with underscore characters") can
literal-transform `"Say OK"` into `"Say_OK"` — or the LLM may instead
interpret `"Say OK"` as a command and answer literally `"OK"`. **Both were
observed live for the identical skill + model** (AFS analysis run got
`"OK"`; implementer re-verification run got `"Say_OK"`) — this is genuine
LLM non-determinism, not a selector/timing bug.

**Fix:** assert what the case actually requires ("completes without error,
produces the expected UI state") via a substring/case-insensitive match
(`"ok" in response.lower()`) + non-empty + no error text — never hard-equal
a literal LLM-generated string when the test message routes through a
FIXTURE skill's own transform instructions you don't control.

If you need a deterministic literal response, create a dedicated disposable
skill with instructions like "You are a helpful assistant. Answer
concisely." — that's still not 100% deterministic (LLMs), but at least
doesn't compound with an unrelated skill's transform logic.

## Seen 1×

- ELITEA-2436 — reused `elitea-1735-skill-underscore` (read-only, per AFS
  Test Data) for a model-settings test; AFS's literal `"OK"` expectation did
  not reproduce on re-verification (got `"Say_OK"`), traced to the fixture
  skill's own unconditional instruction application in the test panel.

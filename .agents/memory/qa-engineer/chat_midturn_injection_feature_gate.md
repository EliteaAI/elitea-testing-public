---
name: Chat mid-turn injection feature gate
description: Interjection/queue UI is invisible until a per-project module_settings flag is PUT true via API — no reachable UI toggle in this harness.
type: project
---

Mid-turn injection (the "interjection" queue UI — `interjection-composer`,
`chat-inject-button`, `interjection-queue-area`/`-label`/`-item`) is gated by
TWO tiers, confirmed live 2026-10-16 (ELITEA-2875/2876/2877/2878):

1. **Platform tier** — `GET ${ELITEA_API_BASE}/elitea_core/platform_settings/prompt_lib`
   → `is_midturn_injection_blocked` (whitelist semantics if `true`). Already
   `false` (unblocked for everyone) on `dev.elitea.ai` as of this check.
2. **Project tier** — `GET ${ELITEA_API_BASE}/social/module_settings/{projectId}`
   → `midturn_injection_enabled`. **Defaults to `false`** for this suite's
   default project (`ELITEA_PROJECT_ID`). Enable with:
   `PUT ${ELITEA_API_BASE}/social/module_settings/{projectId}` body
   `{"midturn_injection_enabled": true}` — confirmed live, 200, persists.

Without BOTH tiers true, none of the interjection UI ever renders (the
`isInjectable` memo in `ChatBox.jsx` short-circuits to `false`), and a case
in this family will silently fail at "verify interjection-composer present"
with no further signal.

**No UI toggle reachable from this harness** — the settings card
(`MidturnInjection.jsx`, "Mid-turn input") is hidden (not disabled) whenever
either tier is off, and even when visible it lives in project-general
settings this harness hasn't needed to reach otherwise. The API PUT above is
the only practical way to flip it for automation. Any new test in this
family needs a fixture that does this PUT before the test and restores the
original value after — doesn't exist yet in `automation/fixtures/` as of
this session.

Full handle set (testids, FIFO drain mechanics, Stop's rescue-and-redrain
behavior, attach-blocking proof) is in
`test-specs/chat-interface/_surface.md` § Mid-turn interjection.

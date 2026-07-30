---
name: reproduce-elitea-bug
description: Reproduce a reported Elitea bug and reach a verdict, verifying on the DEV environment (dev.elitea.ai) — NOT just localhost — before concluding it is a real application defect. Elitea overlay on the generic reproducing-issues method; adds DEV verification, verdict labels, and evidence discipline. Reproduction + documentation only — never fixes code, and never files to elitea_issues (that is a separate, explicitly-requested step). Use when a `bug`-labelled card needs reproduction, whether triggered by the reproduce loop or asked for in a live session.
allowed-tools:
  - Bash
  - Read
  - Grep
  - Skill
---

# Reproduce an Elitea bug

The **Elitea overlay** on the bundle `reproducing-issues` skill. First follow that
skill's 5-phase method (Intake → Environment → Attempts → RCA hints → Confirmation
gate); this file adds only what is specific to Elitea. **Reproduction and
documentation only — you do NOT fix code, and you do NOT file application bugs.**

Works identically whether the **reproduce loop** dispatched you or a human asked in
a **live session** — the procedure is the same; only the loop's factory Deltas
(`factory/loops/reproduce.md`) differ.

## The one rule that makes a verdict trustworthy — verify on DEV (#699)

A bug reproduced **only on localhost:5173** is NOT a confirmed application defect.
Localhost runs the `automation/testids` integration branch against a dev backend
and carries local-env quirks (HMR state, `.env` oddities, unreviewed testid JSX).
Before any `confirmed` verdict, re-verify the same scenario on the **DEV
environment**:

- **URL:** `https://dev.elitea.ai/` (`APP_PREFIX` = `/app` on deployed envs).
- **Auth:** real Keycloak login (localhost's `VITE_DEV_TOKEN` bypass does NOT apply
  here). Log in with `TEST_USER_EMAIL` / `TEST_USER_PASSWORD` from `automation/.env.test`.
  The Keycloak field selector is `input[name="username"]`. Never print the values.
- **Browser Bash commands: `timeout=600000`** (Keycloak + SPA + WebSocket AI waits
  false-fail the 120s default).

Record where it reproduces in an **Environment** line: `localhost-only | DEV | both`.
Only `DEV` or `both` may become `repro:confirmed`. `localhost-only` ⇒ `repro:local-only`.

## Dedup check first — is this card already tracked?

Before spending a browser session reproducing, check whether another card already
tracks this defect (one command, cheap — you are already reading the card):

```bash
env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public --label bug \
  --state all --limit 300 --json number,title,state
```

Keyword-match the component + symptom locally. Apply the duplicate/sibling/regression
tests in `.agents/profile.md` § Bug filing — **duplicate = same object + same trigger
+ same expected/actual**; same pattern on a different object is a **sibling** (keep
both, cross-link), and a re-occurring CLOSED issue is a **regression** (not a dupe).

If it IS a real duplicate: add the `duplicate` label + comment
"Duplicate of #M — <why>" on the **higher-numbered** card, stamp `repro:triaged`, and
**leave it OPEN** — agents never close; the label is the human's sweep queue. Then
stop; don't reproduce it twice. If unsure, treat it as NOT a duplicate and reproduce
normally, noting "possible duplicate of #N".

## Rule out the non-bug explanations first

A "reproduction" that is really an artifact burns a dev's day. Run the rule-outs in
`.agents/role-overrides.md` § *interaction-discovery ladder* and the reproduce loop's
Deltas, in order — environment/service, auth/identity, test data, timing (WebSocket
~2–30s; MUI debounce), interaction mode, and finally **read the component source in
`../EliteaUI/src`** (the handlers state the intended mode as fact). For a 4xx/5xx,
cross-check the OpenAPI contract per `.agents/role-overrides.md` § *4xx/5xx*.
A bug is CONFIRMED only if the **intended** mode fails on DEV and none of the
above explains it — name the mode, the code pointer, and the rule-outs you ran.

## Evidence ATTACHES — never a bare local path

Capture at least one annotated screenshot of actual vs expected. Upload + embed it
per `.agents/role-overrides.md` § *screenshot evidence*; the `embed-evidence` skill
does this mechanically. A bare `.png` path a reader can't open is not evidence.

## Verdict + labels (the whole handoff)

Post a complete verdict on the card and stamp exactly one verdict label, plus the
terminal `repro:triaged` (which dequeues the card from the reproduce loop):

| Verdict | Label(s) | Then |
|---|---|---|
| Reproduced on DEV | `repro:confirmed` + `repro:triaged` | Post full repro report (steps, expected vs actual, evidence embedded, Environment line, rule-outs). **Surface the escalation option — do NOT file.** |
| Localhost only | `repro:local-only` + `repro:triaged` | Post finding; recommend it is env/local, not an app bug. Do not file. |
| Not reproducible | `repro:not-reproducible` + `repro:triaged` | Post exactly what you tried and where behaviour diverged. Do not file. |
| Case-text assumed wrong mode | `repro:triaged` | Post finding; recommend a case-text clarification (the #40 pattern). Do not file. |
| Already tracked by another card | `duplicate` + `repro:triaged` | Comment "Duplicate of #M — <why>" on the higher-numbered card. Leave it **OPEN** — never close. No reproduction needed. |

Tracker/board writes are prefixed `env -u GITHUB_TOKEN gh …` (identity rule,
`.agents/profile.md` § Issue tracker).

## STOP at the verdict — never file to elitea_issues

Reaching `repro:confirmed` is where this skill ends. **Escalating a confirmed bug to
`EliteaAI/elitea_issues` is a separate step that happens only on an explicit user
request** (the `file-app-bug` skill). Do NOT auto-proceed, and in the loop do NOT
treat "confirmed" as license to file — surface the confirmed bug and the escalation
option, and stop. This is the operator's standing guardrail
(`.agents/profile.md` § Bug filing).

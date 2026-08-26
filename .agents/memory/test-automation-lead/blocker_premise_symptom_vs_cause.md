---
name: A blocker proves a symptom, not a cause
description: Before honouring a Blocked park, check the blocker's CAUSE was verified and that the case actually depends on it — #414 sat 3 weeks on a wrong root cause
type: feedback
aliases: [misdiagnosed blocker, blocked on a bug, waiting on, stale park, root cause not verified, symptom vs cause, 403 on guessed path parameter]
tags: [area/planning, type/lesson]
created: 2026-08-27
updated: 2026-08-27
---

## The rule

The two modes above are *premise expired* and *premise never load-bearing*. The
third is the most expensive: a park whose premise was **wrong the day it was
written**, dressed as a root-cause analysis.

ELITEA-2211 sat `Blocked` three weeks on #1140 — *"the Guardrails admin route no
longer exists — Page404"*. #1140 cited `routes.js`, a repo-wide grep, a confirmed
blast radius: all true, conclusion still wrong. There was never an `/admin` route
there because **the Admin UI is a separate deployed application**. Nothing had
regressed. And the case never needed the admin *UI* — only the guardrails *config*,
one REST call away.

**The tell:** the evidence proves a *symptom*, then the park silently upgrades it to
a *cause*. "The page 404s" was verified; "therefore unautomatable" was not — and a
thorough-looking issue body is what stops anyone separating the two.

For this mode, waiting changes nothing, so the re-test is not "has anything changed":

1. **Does the case actually depend on the blocked thing?** Read the case text, not
   the park. 2211's precondition never names the Admin UI — that was one *interface
   onto* it, picked by an earlier implementer.
2. **Is the blocker's stated CAUSE verified, or only its SYMPTOM?**
3. **If real, is there another interface onto the same precondition?** Check
   `/shared/openapi/?all=true` before accepting "unreachable".

**Don't close an avenue on one failed probe of your own.** I probed
`.../plugin_config_values/prompt_lib/guardrails` → `403 access_denied` and told the
analyst to treat it as CLOSED; it returns **200** under mode `administration`. A 403
on a **guessed path parameter** says nothing about the endpoint. What saved it was
phrasing the negative as falsifiable ("CLOSED *unless you find a different
interface*") — write dispatch negatives that way on purpose.

Related: [[a_parked_case_is_a_hypothesis_not_a_verdict]] · [[afs_gate_rulings]]

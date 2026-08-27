# A DEV-only red on a localhost-green test: read the failure SCREENSHOT before dispatching anything

**Verified 2026-08-27** on issue #1813 / ELITEA-1901 (GHA run 32931571484, `dev-stable - agents`, shard user5).

## The pattern

A merged test green on localhost and red on dev.elitea.ai is very often **not** a flake and
**not** UI drift — it is the test encoding an assumption about *project data* that only holds
on the shared localhost user.

Here: `assert get_agent_card_names()` ("dashboard should render at least one existing agent
card"). Every agents test seeds + cleans up its own agent, so each DEV shard user's project is
genuinely EMPTY between tests. Localhost's shared user has leftovers, so it never showed.

## The cheap decisive move — do this BEFORE dispatching an analyst

The allure attachment settles it in one read. The screenshot showed the dashboard's *documented*
empty state fully rendered, plus a user card reading `autotest_user_5 — Agents: 0  Published: 0`.
That single image ruled out timing, product defect, and API failure at once.

How to get it (junit/test-results artifacts contain NO screenshots — only allure-results do):

```bash
# 1. which shard? match the job's END TIME to the artifact timestamps
env -u GITHUB_TOKEN gh api repos/<owner>/<repo>/actions/runs/<RUN_ID>/artifacts \
  --paginate --jq '.artifacts[] | "\(.id) \(.name)"'
# 2. pull that shard's allure-results, find the result JSON, read its attachment
grep -l "<test_name>" ar/*-result.json
# the attachments[] entry names a *-attachment.png in the same dir — Read it
```

## Then check the TMS case text

The decider is whether the failing assertion is in the **case's contract**. ELITEA-1901 Step 1's
expected result is, in full: *"The Agents dashboard loads."* No pre-existing agents required ⇒
the assertion was test-invented ⇒ removing it is a **correction**, not a mask.

The distinguishing test, worth stating in the closure record: masking removes evidence of a real
fault; correcting removes a premise the case never had. Say which, and why.

## Don't let it become a deletion

The right replacement is a *load-completion* oracle, not "delete the line": header + the control
the next step acts on + a `cards OR empty-state` disjunction. Confirm the error render carries no
testid, or the disjunction silently passes on an errored page (the reviewer caught exactly this
gap in the PR's own reasoning — it asserted the exclusion but never demonstrated it).

## Anti-pattern the card itself suggested — refuse it

#1813's body proposed "skip added with env-specific condition if DEV has no agents" as an
acceptable deliverable. That is defect masking. Seeding an agent just to satisfy Step 1 is also
wrong — it invents a precondition the case does not have.

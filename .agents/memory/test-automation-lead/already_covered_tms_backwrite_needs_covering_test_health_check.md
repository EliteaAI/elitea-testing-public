---
name: already-covered TMS back-write needs a covering-test health check first
description: Don't reflexively back-write an already-covered case to ready/automated just because the AFS coverage claim is textually sound — verify the covering test's own current gate status first
type: feedback
---

## What happened (2026-08-19, wave-15)

ELITEA-2471/2472/2473/2474 were correctly classified `already-covered` by the
analyst (near-verbatim duplicates of ELITEA-2212/2213/2214/2215, whose tests
already exist and were merged in an earlier/different session). The natural
next step — matching prior-wave precedent (e.g. ELITEA-2194, ELITEA-2456) — is
to TMS back-write them `ready`/`automated` pointing at the covering test.

Checked the covering tests' own health before doing that, and found:
`test_hitl_sensitive_action_authorization.py` (covers 2471/2472/2473) is
`guardrails`-marked and **excluded from local execution entirely** (needs a
deployed env's Admin UI); `test_direct_toolkit_call_complete_flow.py` (covers
2474) is already documented as excluded from any gate for an open,
non-deterministic defect (#1127). And the covering cases' OWN TMS records
(ELITEA-2211-2215) were themselves still `draft`/`manual` despite the code
being merged — meaning whoever implemented them never claimed `ready` either.

Backwriting 2471-2474 to `ready`/`automated` off the textual coverage claim
alone would have been LESS honest than the campaign's own standard elsewhere:
it asserts a live-verified pass that nobody — including me — actually
confirmed this session.

## Rule going forward

Before TMS-backwriting an `already-covered` disposition:
1. Find the covering test file and check for exclusion markers (`guardrails`
   marker, `# Known defect: #N` / gate-exclusion docstring, `pytest.mark.skip`).
2. Check the covering case's OWN TMS record. If it's still `draft`/`manual`
   despite merged code, that's a signal nobody has confirmed it passes either
   — don't inherit false confidence from it.
3. If either check is unclean: defer the back-write, say so explicitly in the
   closure record (name which check failed), and flag it as a follow-up gap —
   don't silently skip it, and don't force a `ready` you can't stand behind.

---
name: Sanctioned-RED specs should carry @pytest.mark.flaky(reruns=0)
description: pytest.ini's global --reruns=2 can never rescue an expected failure — it only triples wall clock
type: feedback
aliases: [reruns=0, sanctioned RED rerun waste, expected failure reruns]
tags: [area/pytest-config, type/gotcha]
created: 2026-08-30
updated: 2026-08-30
---

`automation/pytest.ini` sets a global `--reruns=2` with `--only-rerun` patterns. A
SANCTIONED-RED spec (an expected failure linked to an open product defect) can match
one of those patterns through its failure repr and then burn two extra full runs to
arrive at the same red.

Measured on ELITEA-2416 (`test_chat_error_invalid_llm_credential.py`, #1993):
**52.97 s** single attempt vs **161.38 s** with 2 auto-reruns — same signature all
three times.

Fix, with in-repo precedent (`tests/ui/chat/test_hitl_sensitive_action_authorization.py`,
#1834/#1835): mark the test `@pytest.mark.flaky(reruns=0)` with a comment naming the
defect. Verified 2026-08-30 that the marker overrides the CLI value in this venv
(pytest-rerunfailures 16.4). This is NOT masking — the test still fails; it just
fails once.

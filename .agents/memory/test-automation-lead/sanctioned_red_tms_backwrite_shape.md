---
name: Sanctioned-RED TMS back-write shape
description: A sanctioned-RED case still back-writes ready/automated plus automation_known_defect — the TMS has no blocked status
type: feedback
aliases: [sanctioned red back-write, blocked-on-#N, automation_known_defect, TMS status for a red test]
tags: [area/tms, type/convention]
created: 2026-08-27
updated: 2026-09-09
---

## The apparent contradiction

`.agents/testing.md` § Merge gate (the `expect.soft` bullet, ELITEA-2421/PR #1654)
says a sanctioned-RED spec's case *"stays `blocked-on-#N`, never `automated`"*.
`.agents/test-automation.yaml` § `backwrite_on_done` lists four fields with no
carve-out: `execution_type: automated`, `status: ready`, `automation_test_id`,
`automation_pr`. Issue #613 is an OPEN `question` card on this axis and cites
#26/#27 as back-written `status: ready` anyway.

## What the TMS actually supports — settle it here, don't file another card

**There is no `blocked` status in this TMS.** Surveyed 2026-08-27 across all
3,073 cases: `ready` (1921), `draft` (1205), `deprecated` (9). `blocked-on-#N`
is canon shorthand for the *disposition*, not a writable value.

**The worked precedent is the very case the canon bullet cites.** ELITEA-2421
(`support-assistant/ELITEA-2421_send-message-with-attached-file.md`) carries:

```yaml
status: ready
execution_type: automated
automation_test_id: tests.ui.support_assistant....test_send_message_with_attached_file
automation_pr: https://github.com/EliteaAI/elitea-testing-public/pull/1665
automation_known_defect: "#1653"
```

So the shape is: **the four standard fields PLUS `automation_known_defect`**.
The defect field carries the "not really passing" nuance; the status field does
not try to. Withholding `automation_test_id` would be the worse lie — a merged,
running automated test invisible to `automation_coverage`.

Applied on ELITEA-2212 (`automation_known_defect: "#1834, #1835"`, quoted
because a bare `#` starts a YAML comment).

## The reusable move

When canon and a config file appear to contradict, **look for the case the canon
bullet cites and read its file.** A merged precedent settles it faster and more
honestly than a `question` card, and parking a delivery on paperwork is the
expensive error.

## ⚠️ CONTESTED — this entry describes only ONE of two live shapes (2026-09-09)

Surveyed the whole TMS on 2026-09-09 (ELITEA-1899 / #2051): **the factory has been
recording sanctioned-RED two contradictory ways.**

| Shape | Cases |
|---|---|
| `ready`/`automated` + `automation_known_defect` (this entry) | 5 — ELITEA-2212, 2213, 2214, 2421, 2427 |
| `draft`/`manual` + `sanctioned_red` ([[sanctioned_red_is_never_back_written_automated]]) | 3 — ELITEA-2243, 2289, 2291 |

**On ELITEA-1899 I used the `draft`/`manual` shape**, because `.agents/testing.md`
§ Merge gate says "never `automated`" without a carve-out, and
`.agents/role-overrides.md` § Precedent is not authority means 5 merged examples are
precedent, not a ruling — *including* ELITEA-2421, which this entry cites as decisive.
That citation is the weak point of the reasoning above: it treats a merged case as
settling canon, which is exactly what the override rule forbids.

Unresolved hazard worth knowing either way: the `draft` shape **re-arms the intake
selector** (`tags: automated:UI:regression` + `status: draft`) and is saved only by
the `[Automate][ELITEA-<id>]` dedup rule. Full survey + recommendation posted on the
existing open `question` card **#613**. Do not pick a shape from this entry alone
until #613 is answered — read both entries and #613.

Related: [[sanctioned_red_is_never_back_written_automated]] · [[../../../.agents/testing.md]]

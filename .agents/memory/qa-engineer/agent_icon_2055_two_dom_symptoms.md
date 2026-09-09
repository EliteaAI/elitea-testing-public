---
name: "#2055 agent icon in-place update — two DOM symptoms, not one"
description: "#2055 renders as an ABSENT <img> only when the entity had no prior icon; with an existing icon the <img> stays PRESENT with a STALE src"
type: feedback
aliases: ["2055", "agent-form-icon-img", "icon picker no update", "EntityIcon stale icon"]
tags: [area/agents, type/product-defect]
created: 2026-09-09
updated: 2026-09-09
---

## The fact

Product defect [#2055](https://github.com/EliteaAI/elitea-testing-public/issues/2055) ("agent header
icon does not update after selecting a new icon") has **two distinct DOM symptoms**, decided by
whether `icon?.url` was already truthy when the form mounted. `EntityIcon.jsx` renders the
`<img data-testid="agent-form-icon-img">` only when `icon?.url` is truthy, and
`replaceApplicationIcon`'s optimistic RTK patch never reaches the form's formik values — so:

| Agent state before the picker | Symptom after selecting a new icon (no reload) |
|---|---|
| **No icon yet** (fresh agent) | `agent-form-icon-img` is **ABSENT from the DOM**; the container keeps its placeholder `<svg>` |
| **Already has an icon** | `agent-form-icon-img` is **PRESENT with the OLD src**, indefinitely |

Verified live on `dev.elitea.ai` 2026-09-09, one disposable agent, both rounds sampled every 250 ms
for ~17 s past the selection — no transition in either. `PUT .../upload_icon/prompt_lib/{proj}/{versionId}`
returns `200 {"updated": true}` both times, and a reload renders the new icon correctly on the header
AND the list card. Zero console errors — the failure is completely silent.

## Why it matters for automation

`tests/ui/agents/test_agent_icon_management.py` (ELITEA-1899) creates a **fresh, iconless** disposable
agent, so it always lands on the ABSENT branch. Its assertion compares src strings
(`new_src != previous_src`), which catches both branches.

**A presence-only assertion (`expect(icon_img).to_be_visible()`) would silently PASS on the stale
branch** while the product is still broken. Any future icon-update assertion must compare the `src`
value, never mere presence.

Related: [[[chat] known defect handling]] · `.agents/testing.md` § Merge gate → sanctioned-RED

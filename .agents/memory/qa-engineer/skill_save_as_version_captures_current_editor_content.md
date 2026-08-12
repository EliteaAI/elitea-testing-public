---
name: Skill save_as_version captures current editor content
description: save_as_version(name) snapshots whatever is currently in the instructions editor, not base's stored text — edit first, then save-as
type: project
---

`SkillDetailPage.save_as_version(name)` (`automation/pages/skill_detail_page.py:483`)
saves whatever text is **currently in the instructions CodeMirror editor** as
the new version's instructions — it does NOT clone the previously-active
version's stored instructions and does NOT take an `instructions` parameter.
To create a version whose instructions genuinely differ from `base`
(ELITEA-2440's whole point — test panel must reflect the switched-to
version), the correct order is:

```python
detail_page.fill_instructions("Always say V1")   # edit BEFORE save-as
detail_page.save_as_version("v1")                 # snapshots the edit above
```

Reversing the order (save-as first, edit after) creates a `v1` identical to
`base`, silently defeating any test asserting version-specific behavior — no
error, no warning, just a false-positive-shaped test.

Also confirmed live: `save_as_version()` auto-navigates to the new version
(URL gains its id segment immediately) — a follow-up
`switch_version(name)` call to that same version is a confirmed no-op, safe
to keep for 1:1 TMS-case step fidelity but doesn't itself change any state.

Full flow (create skill via UI form → edit → save-as-version → switch
between versions → test-panel prompt per version → assert version-specific
response) live-verified end-to-end, zero testid gaps, zero product defects:
`test-specs/skills/l3_test-panel-uses-selected-skill-version-instructions_ELITEA-2440.md`.

---
name: Tag name charset forbids hyphen
description: TagEditor's tag-name regex has no hyphen — uuid-suffix tags with underscore, not hyphen
type: feedback
---

Any tag-creation flow that goes through the shared `TagEditor.jsx` →
`AutoCompleteDropDown.jsx` (Skills, Pipelines, Agents — same component) validates
new tag names against `NormalTagNameInputRegExp = /^[\w,\s]+$/g`
(`EliteaUI/src/common/constants.js`). `\w` allows letters, digits, and
underscore only — **no hyphen**.

Symptom if you uuid-suffix a tag name with a hyphen (`f"regression-{uuid...}"`):
typing it and pressing Enter produces **zero visible error and zero chip** —
the Tags field just silently stays empty. Looks like a flaky wait/timing bug
at first glance (an empty `tags_chip.count()` right after `add_tag()`), but
it's the input validation rejecting the value.

Fix: uuid-suffix with underscore instead (`f"regression_{uuid...}"`). Same
issue will hit any new tag-filter test on Skills/Pipelines/Agents that
copies the `uuid.uuid4().hex[:8]` suffix pattern from `test_skill_tag_filter.py`
with a hyphen separator.

Also: selecting/re-typing an EXISTING tag name (second pipeline/skill reusing
a tag from the first) fires a known, not-filed cosmetic React dev-mode
console warning (`Invalid value for prop 'sx' on <svg>`, from `TagEditor`'s
`SvgCheckedIcon`) — filter it out of any console-error assertion the same way
`test_skill_tag_filter.py` does, or it'll false-positive a console-error check.

Origin: ELITEA-2013 (Pipeline Tags — Add and Filter) implementation.

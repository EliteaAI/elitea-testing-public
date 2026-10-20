---
name: Ask User clarification card is model-discretionary
description: Ask User card for incomplete skill request appears ~18% of runs; card handles; radio overlay needs row click
type: project
---

With `skill_builder` + `ask_user` toggles on, `Create a skill for onboarding` makes the model ask via the clarifying card in only ~3 of 17 fresh conversations (DEV, 2026-10-20); otherwise it guesses and creates the skill. Cases whose precondition is "the model asks" cannot gate 3/3 without a retry loop or a stronger prompt - classify blocked and let the lead decide. Card handles: `input[placeholder="Your option"]`, role radio rows (hidden input covered by overlay - click the visible row), `Skip`->`Continue`, answer summary text after submit. See test-specs/chat-interface/_surface.md.

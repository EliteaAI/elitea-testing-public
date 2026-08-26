---
name: Build with AI is one shared modal across Agents, Skills and Project Context
description: Every "Build with AI" flow renders entities/generate-entity-with-ai; subclass GenerateEntityModalPageBase and wire testids through the props it already accepts
type: reference
aliases: [build with ai, generate entity modal, GenerateEntityModal, generate draft, project context build with ai]
tags: [area/elitea-ui, type/pattern]
created: 2026-08-26
updated: 2026-08-26
---

## The shell is shared — the page object should be too

`src/[fsd]/entities/generate-entity-with-ai/` (`GenerateEntityButton.jsx` +
`GenerateEntityModal.jsx`) backs the Agent, Skill AND Project Context "Build with AI"
flows. Steps are always INPUT → LOADING → REVIEW; "Generate Draft" doubles as the retry
control; the review step's actions are "Back to prompt" + an entity-specific approve
label (`Apply` for Project Context, `Create Agent` for agents).

So a new entity's Build-with-AI page object is a **subclass of
`GenerateEntityModalPageBase`** (`automation/pages/generate_entity_modal_page_base.py`) —
supply `GENERATE_DRAFT_ROUTE`, `_is_generate_draft_url()`, and the locator fields.
`GenerateProjectContextModalPage` (2026-08-26) is the third one.

## Testids: the props already exist — do not touch the shared component

`GenerateEntityModal` accepts `modalTestId`, `promptInputTestId`, `errorAlertTestId`,
`loadingIndicatorTestId`, `generateButtonTestId`, `cancelButtonTestId`,
`backButtonTestId`, `approveButtonTestId`, `closeButtonTestId`; `GenerateEntityButton`
accepts `buttonTestId`. A feature that has no testids simply left them `undefined` —
supply them at ITS call site. Zero shared-component change, zero functional impact.

The one prop that was genuinely missing is `titleTestId`; added as a one-line additive
pass-through to `Modal.BaseModal`'s own pre-existing `titleTestId`
(EliteaAI/EliteaUI@18db47e7). Worth knowing: **`Modal.BaseModal` has no `keepMounted`**,
so a closed dialog's testid count is 0 — `to_have_count(0)` is a valid "dialog closed"
assertion.

## Base `wait_for_review_form()` needs a back-button testid

It waits on `back_button` + `approve_button`. If you skip the back-button testid (#511 —
no case exercises "Back to prompt"), the base method raises
`AttributeError: 'NoneType' object has no attribute 'wait_for'`. **Override it** to key
on the approve button plus the entity's own review field, as
`GenerateProjectContextModalPage` does.

Related: [[live_generate_draft_is_its_own_oracle]]

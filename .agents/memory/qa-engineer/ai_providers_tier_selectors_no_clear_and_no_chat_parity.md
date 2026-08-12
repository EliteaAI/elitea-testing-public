---
name: AI Providers tier selectors — no clear option, no chat parity
description: Settings→AI Providers Default/High-tier/Low-tier selectors mutate shared state live, no UI unset, only Default feeds chat
type: reference
---

Surface: `/settings/ai-providers`, LLMs section (ELITEA-2397 analysis,
2026-08-06). Full detail in `test-specs/settings-ai-providers/_surface.md`.

- Clicking a tier selector opens a listbox and selecting an option fires an
  IMMEDIATE `POST /api/v2/configurations/models/{project_id}` (no Save
  button) that mutates the SHARED live project's config — every other UI
  test that reads Default/High-tier/Low-tier for this project is affected.
- The dropdown has **no clear/"None" option** — once a tier has a value
  there is no UI-only path back to "unset". My own exploration left the
  shared `Private`/`399` project's High-tier at `GPT-5.2` (was unset before)
  because of this — could not revert via UI. Any test that mutates a tier
  starting from "unset" needs an API-level restore path or must accept it
  can't perfectly restore that state.
- **Only Default feeds the plain `/chat` new-conversation model selector**
  (`model-selector-button`). Confirmed via `EliteaUI/src` grep: Low-tier is
  consumed only by the Mermaid diagram "Quick Fix" AI-assist action; High-tier
  has ZERO frontend consumers anywhere. Don't assume tier-parity with Default
  for any case that touches these selectors — verify per-tier before writing
  a "used when starting a chat"-shaped assertion.
- Dropdown option testid is a PRE-EXISTING shared `Select.SingleSelect`
  convention (not added by any specific case): `[data-testid="select-option-{model_id}<<>>{value}"]`,
  auto-derived from whatever testid is threaded onto the field
  (`{field-testid}-combobox` for the trigger). Reusable anywhere this shared
  component is used with a testid.

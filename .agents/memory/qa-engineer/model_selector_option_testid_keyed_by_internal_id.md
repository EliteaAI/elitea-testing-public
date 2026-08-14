---
name: Model selector option testid keyed by internal id, not display name
description: LLMModelsMenu.jsx's model-selector-option-{name} testid uses the model's raw/internal id (e.g. eu.anthropic.claude-sonnet-4-5-...), never the display text shown in the UI — and the selected state is a genuine same-element conditional child render (Mui-selected class + CheckedIcon), not a testid ternary.
type: feedback
---

Confirmed live 2026-08-14 (ELITEA-2091 analysis) against `EliteaUI/src/[fsd]/widgets/llm-model-selector/ui/LLMModelsMenu.jsx`:

- Each model dropdown `MenuItem` carries `data-testid={`model-selector-option-${item.name}`}`
  where `item.name` is the model's INTERNAL id, not `item.display_name` (what's
  rendered on screen). Example confirmed live: clicking the item labelled
  "Anthropic Claude 4.5 Sonnet" resolves to
  `model-selector-option-eu.anthropic.claude-sonnet-4-5-20250929-v1:0`.
  Never build this testid from the display text you read off the page —
  either enumerate the rendered menu and pick one by matching its VISIBLE
  text first, or read `data-testid` off the matched item and reuse it.

- Selected-state is `selected={item.id === selectedModel?.id}` (sets MUI's
  `Mui-selected` class on the SAME testid'd `MenuItem` — the testid itself
  never changes) plus a conditionally-rendered `CheckedIcon` CHILD with no
  testid of its own. Compliant assertion: locate by the stable
  `model-selector-option-{name}` testid, then read its `class` attribute for
  `Mui-selected` (or count the child icon scoped under that one parent) — do
  NOT ask for a new testid on the checkmark icon itself, and do not treat
  this as a state-switched-testid anti-pattern (the parent testid is
  constant; only a class + a child render change).

- The composer's own trigger button testid is `model-selector-name` (NOT
  `model-selector-button` — that field/testid also exists and is the outer
  wrapper, but a live click on the visible model-name text resolves to
  `model-selector-name` specifically). `ChatPage.model_selector` currently
  points at `model-selector-button`; both work for opening the dropdown but
  confirm which one you're actually asserting text against.

- Model roster + the currently-selected default are environment/project
  dependent — this session saw `GPT-5.4` as default on the Team project
  (471) vs `Anthropic Claude 4.5 Sonnet` on the default Private project
  (399). Never hardcode "switch to Claude/GPT-X" — resolve the current
  selection at runtime and pick any other rendered option.

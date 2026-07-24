---
name: LLM Model Settings dialog testid wiring
description: Where the 5 testids for LLMModelSelector's Settings (gear) dialog actually live — 4 are trivial existing-prop wiring, 1 (Reasoning slider) needed a genuinely new prop threaded through a shared component, scoped to one call site only
type: feedback
---

ELITEA-1880 (PR EliteaAI/elitea-testing-public#1002): the Model Settings dialog
(`LLMModelSelector.jsx` gear button -> `LLMSettingsDialog.jsx`) had ZERO app
testids anywhere before this case, but most of the wiring already existed —
only one component needed real new code.

- **Gear button** (`model-settings-button`) — plain `data-testid=` add on the
  `<Button aria-label="model settings menu">` in `LLMModelSelector.jsx`.
  Generic name (shared widget, not agent-page-specific — same rationale as
  the pre-existing `model-selector-button`/`model-selector-name`).
- **Dialog container** (`model-settings-dialog`) — `LLMSettingsDialog.jsx`
  renders `<Modal.BaseModal>` without wiring its ALREADY-SUPPORTED
  `'data-testid'` destructured prop (`BaseModal.jsx` forwards it straight to
  the MUI `<Dialog data-testid={dataTestId}>`). Pure prop-wiring at the call
  site — zero `BaseModal.jsx` changes needed.
- **Dialog Close (X) button** (`model-settings-dialog-close-button`) — same
  `LLMSettingsDialog.jsx` call site, via `BaseModal`'s already-supported
  `closeButtonTestId` prop (wired to the header's Close `Button.BaseBtn`).
- **Max Completion Tokens radio group** (`model-settings-max-tokens-mode`,
  dynamic -> `-auto`/`-custom`) — `MaxTokensSection.jsx` just needed to pass
  `testId="model-settings-max-tokens-mode"` to the already-built
  `Checkbox.RadioButtonGroup` (`RadioButtonGroup.jsx` already builds
  `` `${testId}-${String(item.value).toLowerCase().replace(/\s+/g,'-')}` ``
  per item — trivial wiring, zero `RadioButtonGroup.jsx` changes).
- **Reasoning slider container** (`model-settings-reasoning-slider`) — the
  ONE genuinely new prop. `ReasoningSlider.jsx` wraps the shared
  `DiscreteSlider.jsx`, which only forwarded extra props to the *inner* MUI
  `<Slider>` (via `...sliderProps`), not the outer `<Box sx={styles.container}>`
  holding the Low/Medium/High labels. Added a new `containerTestId` prop to
  `DiscreteSlider.jsx`, destructured separately from `...sliderProps` and
  wired onto that outer `Box`. **Wired the new prop ONLY from
  `ReasoningSlider.jsx`** — the sibling `CreativitySlider.jsx` (same shared
  `DiscreteSlider`, different call site, renders for non-reasoning models)
  is untouched, since no case has exercised that branch yet (canon #511
  scope discipline — the prop exists and is available for whichever case
  gets there first, but adding the testid VALUE at an unexercised call site
  would be a blanket-add).

**Takeaway for the next dialog/shared-component testid gap in this family**:
check the shared component's prop list FIRST (`BaseModal`, `RadioButtonGroup`,
any `Checkbox.*`/`Modal.*` under `src/[fsd]/shared/ui/`) before assuming new
plumbing is needed — most gaps in this codebase are unwired existing props,
not missing capability. `DiscreteSlider.jsx` was the one genuine exception in
this pass (a component that forwards SOME extra props but not a testid to its
own wrapper element).

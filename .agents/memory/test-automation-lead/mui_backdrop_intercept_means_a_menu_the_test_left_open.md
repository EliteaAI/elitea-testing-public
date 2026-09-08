---
name: "'subtree intercepts pointer events' from a MuiBackdrop = a menu the TEST left open, not a product regression"
description: The Playwright call log names the culprit; read it before dispatching. On a searchable MUI Select, a page-level Escape is swallowed and the dropdown never closes.
type: feedback
aliases: [MuiBackdrop intercepts pointer events, version dropdown timeout, menu still open, Locator.click timeout 10000ms, invisible backdrop, MuiPopover MuiMenu MuiModal, swallowed Escape]
tags: [area/triage, area/ui, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The signature

```
Locator.click: Timeout 10000ms exceeded.
  - waiting for get_by_test_id("<some-trigger>")
    - locator resolved to <div data-testid="…" class="… MuiSelect-root …">
  - attempting click action
      - element is visible, enabled and stable
      - <div aria-hidden="true" class="MuiBackdrop-root MuiBackdrop-invisible MuiModal-backdrop …">
        from <div id="menu-" role="presentation" class="MuiPopover-root MuiMenu-root MuiModal-root …"> subtree
        intercepts pointer events
```

The intake pipeline files this as *"component X is unresponsive — a likely regression"*. It is
almost never that. `id="menu-"` is MUI Select's own popover id, so **the element being clicked is
blocked by its OWN dropdown, still open from an earlier step.** The 10 s of retries also rule out a
close animation — an exit transition is ~300 ms; a full 10 s means the menu never closed at all.

## Why the close silently fails (the 2026-09 mechanism, EliteaUI)

A page object that dismisses with a fire-and-forget `page.keyboard.press("Escape")` has no oracle.
Once EliteaAI/EliteaUI@cf648e9a (PR #857) gave the VERSION dropdown a **search field**,
`SingleSelectDropdown.jsx` mounts `<SimpleSearchBar … onKeyDown={e => e.stopPropagation()} />`;
`SimpleSearchBar` **autofocuses itself** and maps Escape to *clear the search box* **before** calling
that handler. Focus sits in the search box the moment the menu opens, so Escape is consumed **and**
stopped and MUI's `Modal` never sees it. Pressing it twice changes nothing.

Generalise: **a page-level `keyboard.press("Escape")` is not a close, it is a hope.** Any component
that autofocuses an input inside its popper breaks it, and nothing in the suite notices until a
downstream click deadlocks somewhere unrelated.

## The triage that settles it in ~6 tool calls, before any dispatch

1. Read the allure `-result.json` **call log**, not just `statusDetails.message`. The message says
   "timeout"; the call log names the intercepting element. That one block is the diagnosis.
2. Check which step FAILED against the step immediately BEFORE it in the same result. If the previous
   step ends in a menu-dismiss helper, you already have the culprit.
3. Sort the whole shard's results by start time to exclude an environment outage
   (`env_outage_page_is_a_fix_card_root_cause.md`) — passes bracketing the failures rule it out.
4. Only then dispatch, and hand over the mechanism **as a hypothesis to confirm or refute**, never as
   a conclusion.

## The fix shape that survives review

Not a longer timeout (10 s already elapsed with the backdrop up). Not `page.evaluate` DOM surgery
(fidelity policy). Press Escape **on an option** — `Locator.press()` focuses first, so the keydown
reaches the `MenuList` — and **confirm** closure with a conjunction of `aria-expanded="false"` on the
trigger AND `to_have_count(0)` on the options, bounded retry, then raise naming the live state.

⚠️ `aria-expanded` alone is a **leading** indicator: MUI emits it off React `open` state, which flips
before the backdrop unmounts. Alone it narrows the window; with the option-count term it closes it.

Related: [[dev_only_red_check_the_screenshot_first]] · [[harvest_gha_allure_artifacts_before_dispatching]] · [[env_outage_page_is_a_fix_card_root_cause]] · [[lead_run_matched_negative_control_on_dev]]

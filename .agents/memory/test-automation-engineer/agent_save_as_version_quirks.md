---
name: Agent Save As Version / VERSION selector quirks (implementer)
description: AgentDetailPage's Save As Version dialog + VERSION selector page-object surface — the version-selector-trigger-text-vs-URL race, aria-selected as the active-option handle, discard-button testid gap on the Agent page specifically, and the create_agent_full() workaround for the #524 temperature/reasoning_effort 400
type: feedback
---

## Context

From ELITEA-1888 ("Save As Version creates a named version visible in the
VERSION dropdown"). `AgentDetailPage` gained a full version-management
surface: `version_selector_trigger` (testid `agent-version-selector-trigger`),
`create_version_name_input`/`create_version_save_button`/
`create_version_cancel_button`/`create_version_close_button` (the "Create
version" dialog), a `VERSION_OPTION = '[data-testid="version-option-{}"]'`
dynamic-testid template (same shared pattern `SkillDetailPage.VERSION_OPTION`
already uses — declared separately per class, not inherited, since
`AgentDetailPage` and `SkillDetailPage` don't share a base), and methods
`open_save_as_version_dialog()` / `confirm_new_version()` /
`save_as_version()` (thin wrapper) / `get_version_selector_value()` /
`open_version_selector()` / `is_version_option_visible()` /
`is_version_option_active()`.

## Reusable facts

1. **Split the "click → dialog → confirm" method into two** when the AFS
   wants per-step assertions on the dialog's just-opened state (Name input
   visible, Save disabled while empty). A single monolithic
   `save_as_version(name)` (mirroring `SkillDetailPage`'s original shape)
   hides that intermediate assertion point from the test. Keep the
   combined method too, as a thin wrapper, for callers that don't need it.

2. **Real timing race: URL changes before the VERSION-selector trigger's
   own text re-renders.** After confirming a new version, waiting only for
   the URL's version-id path segment to change is NOT sufficient —
   `get_version_selector_value()` (reads `agent-version-selector-trigger`'s
   `innerText`) can still read the stale previous version name for a beat
   (a follow-up API call loads the new version's data before the trigger
   re-renders). Fix: a second `page.wait_for_function` polling the
   trigger's own `innerText` against the expected name, not a sleep.

3. **`aria-selected="true"`/`"false"` on the `version-option-{name}` MUI
   option is the clean "is this the active version" handle** — confirmed
   live, no new testid needed. `Locator.get_attribute("aria-selected") ==
   "true"` off the existing dynamic-testid locator is sufficient;
   `.Mui-selected` in the class list is the same signal but aria-selected
   is the more semantic read.

4. **`AgentFormPage.discard_button`'s `testid="discard-button"` is NOT
   actually wired up on the Agent detail page live** — confirmed via full
   `document.querySelectorAll('[data-testid]')` enumeration in both clean
   and dirty form states, zero hits. This is specific to the Agent page:
   `PipelineFormPage`/`CredentialDetailPage` each have their own working
   `discard-button` testid on their own pages. No test in the suite
   exercises `AgentFormPage.discard_button` yet — if a future case needs
   to assert Discard-button state on the Agent form, the testid needs to
   be added via `add-data-testid` first; don't assume the declared
   `LocatorDescriptor` means the element is actually reachable.

5. **`AgentAPI.create_agent_full()` with `llm_settings` that OMITS
   `reasoning_effort` entirely (not `"none"` — just absent, keep
   `temperature`) avoids the open #524 `temperature`/`reasoning_effort`
   400 conflict** that blocks the default `create_agent()` payload. Useful
   as a one-off environment-seeding script (NOT inside a shipped test —
   the reuse-existing-debris-agent pattern still applies to the test
   itself) when a case's test-data precondition needs a fresh disposable
   agent and the debris pool it would normally reuse has run dry (e.g.
   from repeated local dev-iteration runs, since save-as-version-style
   cases delete the WHOLE reused agent at teardown every run — the debris
   supply is finite, not renewable by the test itself).

## Where

- `automation/pages/agent_detail_page.py` — version-management locators +
  methods (search "ELITEA-1888" in the file's section header comment).
- `automation/pages/agent_form_page.py` — `save_as_version_button`
  (stripped a forbidden `fallback=` param here per an AFS-flagged
  pre-existing locator-policy violation).
- `automation/tests/ui/agents/test_agent_save_as_version.py`.

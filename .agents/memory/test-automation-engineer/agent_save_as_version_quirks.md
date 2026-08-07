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

5. **CORRECTED (post-merge-gate fix, see below):** `AgentAPI.create_agent_full()`
   with `llm_settings={"reasoning_effort": "none"}` and `temperature` KEY
   OMITTED ENTIRELY avoids the open #524 `temperature`/`reasoning_effort`
   400 conflict — confirmed live via 4 consecutive local runs. (The
   original version of this note said "omit `reasoning_effort`, keep
   `temperature`" — untested guess, superseded; #524's own validator error
   text is explicit that `temperature` conflicts with any `reasoning_effort`
   other than `'none'`, so setting it to `'none'` is the safe value, not
   omitting it.) **This is now the shipped, in-test pattern** — the
   reuse-existing-debris-agent design was replaced entirely: the debris
   pool (`elitea-1735-skills-agent` duplicates from ELITEA-1735) is finite
   and the test permanently deletes one member per run at teardown, so it
   silently exhausts under repeated runs (caught by the lead's independent
   3x pre-merge gate on run 3/3 — not flake, guaranteed-recurring). Fixed
   test creates a fresh, uniquely-named agent every run
   (`f"elitea-1888-sav-{uuid.uuid4().hex[:8]}"` — note the API's 32-char
   name cap: the more descriptive `elitea-1888-save-as-version-{uuid8}`
   400s with "String should have at most 32 characters") and deletes it at
   teardown — sustainable indefinitely, zero shared-pool dependency. Any
   other test that needs a throwaway agent and would otherwise reach for
   the `agent_id` fixture (which uses `create_agent()`'s broken shared
   defaults) or a debris-pool scavenge should use this same
   `create_agent_full()` + `reasoning_effort: "none"` pattern instead of
   either.

6. **Same trigger-vs-panel race also fires on a FRESH page load (not just
   same-page navigation) — ELITEA-1898 (Copy version link).** Opening a
   copied `/agents/all/{id}/{versionId}` URL in a brand-new tab (even
   through the `ProjectSwitcher` hard-reload redirect hop the leading
   `/{projectId}` prefix triggers) shows `agent-version-selector-trigger`'s
   text settle on the correct version NAME before `copy-version-id`'s text
   settles on the matching version ID — asserting `get_version_id()` right
   after `expect(version_selector_trigger).to_have_text(name)` passes can
   read the PREVIOUS version's id (observed: off-by-one id, 1/1 local runs).
   Fix: poll both together via one `page.wait_for_function` (trigger text
   AND `copy-version-id` text both equal their expected values) before
   reading either — same shape as `select_version_by_name()`'s own 3-way
   convergence check, just without the URL-segment leg (a full page load
   already guarantees the URL is correct by the time JS runs).

## Where

- `automation/pages/agent_detail_page.py` — version-management locators +
  methods (search "ELITEA-1888" in the file's section header comment).
- `automation/pages/agent_form_page.py` — `save_as_version_button`
  (stripped a forbidden `fallback=` param here per an AFS-flagged
  pre-existing locator-policy violation).
- `automation/tests/ui/agents/test_agent_save_as_version.py`.

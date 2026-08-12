---
name: POM/locator review scope beyond the mechanical grep
description: role-overrides.md's mechanical grep answers ONE question (testid vs raw handle). It does not answer where the locator is constructed, nor whether the sanctioned LocatorDescriptor mechanism was used. Three independent checks, every round.
type: feedback
---

## Rule — three checks, all three every pass

1. **Testid identity** — the mechanical grep from `.agents/role-overrides.md`
   § Reviewer slot. A hit is compliant only with a literal `[data-testid=`
   selector or an UPPER_CASE class constant that resolves to one.
2. **Construction site.** `page.locator(...)` / `.format(...)` executing
   anywhere in `automation/tests/**` is `CHANGES_REQUESTED` regardless of how
   testid-pure the selector string is. The rule gates WHERE it executes, not
   what it looks like. Tell: a dynamic-testid class constant whose only
   consumer outside its own declaration is a spec file —
   `grep -n "CONSTANT_NAME" automation/pages/*.py automation/tests/**/*.py`
   and count consumers. Remedy: wrap it in a page-object method.
3. **Sanctioned mechanism.** A static multi-match card-name locator must be a
   class-level `LocatorDescriptor(testid=…)`, not a raw string constant +
   inline `self.page.locator(...)` in a method body. `LocatorDescriptor.__get__`
   resolves via `page.get_by_test_id()` and returns a normal multi-match
   `Locator` supporting `.count()/.nth()/.all()` — 36 existing call sites prove
   it. "It's a list, so it needs a raw constant" is a false assumption, and PR
   authors have twice described the bypass as "brings it into compliance".

**Check 2 must be re-run every round, independently of how clean check 1 comes
back.** A round-1 grep that listed a line as "compliant" under the testid
filter is exactly how a POM violation rides unflagged into round 2.

## Seen 5× (3 construction-site, 2 mechanism)

- PR #620/ELITEA-1955 — self-check claimed 1 hit; the same grep found 3, two of them `.locator()` calls in `test_pipeline_mcp_node_empty_toolkit_before_attach.py`, both testid-anchored and both blocking.
- PR #643/ELITEA-1808 — `ARTIFACTS_TREE_ITEM`, a correctly-declared page-object constant, had its only consumer in the spec file (siblings `BUCKET_ROW` / `BUCKET_MENU_BUTTON` were correctly wrapped in methods).
- PR #670/ELITEA-1866 R2 — three `page.locator(ToolkitTestSettingsPage.X)` calls in a test body, carried over unflagged from round 1's "compliant" list.
- PR #537/ELITEA-1974 — `credentials_list_page.py` raw `ENTITY_CARD_*_SELECTOR` constants + `page.locator()` instead of `LocatorDescriptor`.
- PR #545/ELITEA-1869 — `agents_list_page.get_agent_card_names()` same bypass, different file.

See also: mechanical_grep_passes_non_testid_but_spec_file_locators_still_violate_pom.md ·
elitea_1808_pom_construction_site_not_selector_source_reviewer_check.md ·
recurring_locatordescriptor_bypass_for_card_name_lists.md

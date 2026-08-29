"""UI test — Set a LLM model as Default / High-tier / Low-tier (Settings -> AI Providers).

Test cases: ELITEA-2397, ELITEA-2414 (extension — the Default survives a reload)
AFS: test-specs/settings-ai-providers/l3_set-llm-model-default-high-low-tier_ELITEA-2397.md
AFS: test-specs/settings-ai-providers/lextend_default-llm-selection-persists-after-reload_ELITEA-2414.md

ELITEA-2414 (`extend-existing`) adds Step 6b. Its steps 1-2 (navigate to the
AI-configuration surface, change the Default LLM selector to a different model)
are this spec's Steps 1-6 exactly; its own subject — the Default still reading
the chosen model after a real `page.reload()` — was untested here. That matters
more on this control than on its siblings: there is NO Save button (selecting an
option fires the POST immediately), so an in-session assertion cannot tell
"persisted" from "optimistically rendered". ELITEA-2414's title says "Default
tier" while its step 2 says "Default LLM model selector"; the step text is the
concrete instruction and the Expected Final State refers back to it, so the
extension covers the Default selector only — High-tier/Low-tier appear in it
solely as an unchanged-siblings check.

Case-identity note (full write-up in the AFS, reused from ELITEA-2392 — same
root cause): the TMS case directs the tester to "Settings -> AI Configuration"
— no such page/nav-item exists. The real page is "AI Providers"
(`/settings/ai-providers`); its "LLMs" section (case says "LLM Models" —
cosmetic label drift) carries the Default/High-tier/Low-tier selectors this
case exercises. Filed clarification (reused, not re-filed):
EliteaAI/elitea-testing-public#1250.

Case-text drift SPECIFIC to this case (filed separately,
EliteaAI/elitea-testing-public#1253): case step 9 ("Repeat steps 2-8 for
High-tier and Low-tier selectors") implies High-tier/Low-tier feed the "start
a new chat" default model exactly like Default does. Live source inspection +
live verification shows this is true ONLY for Default — High-tier has ZERO
frontend consumers anywhere in EliteaUI outside this settings page's own
display code, and Low-tier is consumed only by the chat canvas's Mermaid
"Quick Fix" AI-assist action, a different, narrow surface. This test therefore
automates the FULL causal chain (selector -> badge -> new-chat model) for
Default only, and the selector-and-badge mechanics only (no new-chat claim)
for High-tier/Low-tier — per the Reverse-masking guard, it does not assert a
"used when starting a chat" contract the live product doesn't hold for those
two tiers.

**This test MUTATES shared, live project configuration** — the whole
`${TEST_USER}` project's Default/High-tier/Low-tier LLM assignments, the same
project every other UI test in this suite runs against (notably
ELITEA-2090's chat-default-LLM test). It captures every original value
before mutating and restores them in a `finally` block. The MUI tier
dropdowns offer no "clear"/blank option (confirmed live) — a tier that starts
UNSET cannot be restored to unset via the UI; if that's ever the case, the
`finally` block documents it via a `logger.warning` instead of silently
leaving worse state (AFS Cleanup). This test should not run concurrently with
any other test that reads/writes this project's LLM tier configuration.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: medium priority (AFS metadata: l3 -- this suite's l3 maps to p2,
      matching the sibling ELITEA-2392 test and settings-personal-tokens/
      settings-secrets tests)
    - regression
"""

import logging

import allure
import pytest
from pages.ai_providers_page import AIProvidersPage, pick_alternative_llm_model
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

UI_ELEMENT_TIMEOUT = 10_000


def _tier_state(body: dict, name_key: str, project_id_key: str) -> dict:
    """Extract a tier's current ``{name, project_id, value}`` from an LLM
    models response body. ``value`` is ``""`` for an originally-unset tier
    (blank name/project_id -- confirmed live for High-tier before this
    session's own exploration mutated it, ELITEA-2397 AFS Cleanup)."""
    name = body.get(name_key) or ""
    project_id = body.get(project_id_key)
    if not name or not project_id:
        return {"name": "", "project_id": None, "value": ""}
    return {"name": name, "project_id": project_id, "value": f"{name}<<>>{project_id}"}


def _display_name_for(items: list, name: str) -> str:
    """Look up an LLM item's display label by its raw ``name`` field."""
    for item in items:
        if item.get("name") == name:
            return item.get("display_name") or item["name"]
    return name


class TestSetLLMModelTiers:
    """ELITEA-2397 — Set a LLM model as Default / High-tier / Low-tier."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2397_set-a-llm-model-as-default-high-tier-low-tier.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2414_default-tier-selection-persists-after-page-reload.md",
        "onetest-ai Test Case link (ELITEA-2414)",
    )
    def test_set_llm_model_default_high_low_tier(self, page):
        """Selecting a different model for the LLMs section's Default tier
        updates the selector text immediately (no Save action), swaps the
        "Default" badge from the old model's card to the new model's card,
        survives a full page reload (ELITEA-2414), and changes the model a
        brand-new /chat composer starts with.
        High-tier and Low-tier show the same selector+badge mechanics but do
        NOT change the new-chat composer's model (case-text drift, see module
        docstring). Original values are restored in a finally block."""
        ai_providers_page = AIProvidersPage(page)
        chat_page = ChatPage(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> AI Providers, capturing the LLMs-scoped "
            "models response (original tier values + candidate option list)"
        ):
            llm_response = ai_providers_page.navigate_and_capture_llm_response()
            assert llm_response.status == 200, (
                f"Expected the LLM-scoped models request to return 200, got {llm_response.status}"
            )
            llm_body = llm_response.json()
            items = llm_body.get("items", [])
            expect(ai_providers_page.llms_section_header).to_have_attribute(
                "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
            )
            expect(ai_providers_page.llms_default_selector_combobox).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert ai_providers_page.get_configuration_card_count() > 0, (
                "Expected at least 1 configuration card under the auto-expanded LLMs section"
            )

        with allure.step("Step 2 — Capture original Default/High-tier/Low-tier values before mutating"):
            original_default = _tier_state(llm_body, "default_model_name", "default_model_project_id")
            original_high = _tier_state(llm_body, "high_tier_default_model_name", "high_tier_default_model_project_id")
            original_low = _tier_state(llm_body, "low_tier_default_model_name", "low_tier_default_model_project_id")
            assert original_default["value"], "Expected the shared project to have a Default LLM model configured"
            original_default_label = _display_name_for(items, original_default["name"])
            original_high_label = _display_name_for(items, original_high["name"]) if original_high["value"] else ""
            original_low_label = _display_name_for(items, original_low["name"]) if original_low["value"] else ""
            # Selector visible text is also captured -- High-tier may legitimately
            # render blank if the tier is unset (AFS step 2 verify).
            captured_default_text = ai_providers_page.llms_default_selector_combobox.text_content()
            captured_high_text = ai_providers_page.llms_high_tier_selector_combobox.text_content()
            captured_low_text = ai_providers_page.llms_low_tier_selector_combobox.text_content()
            logger.info(
                "Captured original tier selector text -- Default=%r High-tier=%r Low-tier=%r",
                captured_default_text, captured_high_text, captured_low_text,
            )

        try:
            with allure.step(
                "Step 3-4 — Default tier: click the selector, select a different model, "
                "verify the POST save call returns 200/success and the selector text updates"
            ):
                new_default = pick_alternative_llm_model(items, original_default["value"])
                new_default_value = f"{new_default['name']}<<>>{new_default['project_id']}"
                new_default_label = new_default.get("display_name") or new_default["name"]
                response = ai_providers_page.select_tier_model(
                    ai_providers_page.llms_default_selector_combobox, new_default_value
                )
                assert response.status == 200, f"Expected 200 setting Default model, got {response.status}"
                assert response.json() == {"result": "success"}, (
                    f"Unexpected save response body: {response.json()}"
                )
                expect(ai_providers_page.llms_default_selector_combobox).to_have_text(
                    new_default_label, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 5 — Verify the newly-selected model's card gains a 'Default' badge"):
                expect(ai_providers_page.card_tier_badge(new_default_label, "Default")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Verify the previously-Default model's card no longer shows the 'Default' badge"
            ):
                expect(ai_providers_page.card_tier_badge(original_default_label, "Default")).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 6b (ELITEA-2414) — The Default selection survives a full page reload"):
                # ELITEA-2414's own subject. This control has NO Save button —
                # selecting an option fires the POST immediately — so every
                # in-session assertion above cannot tell "persisted" from
                # "optimistically rendered". A cold re-read is the only proof.
                # Placed before Step 7's chat navigation and the Step 9a/9b tier
                # work, so the reload observes the Default change alone.
                reload_response = ai_providers_page.reload_and_capture_llm_response()
                assert reload_response.status == 200, (
                    f"Expected the LLM-scoped models request after reload to return 200, "
                    f"got {reload_response.status}"
                )
                reloaded = reload_response.json()
                # The product's own cold response is the oracle for what actually
                # persisted, independent of the DOM (AFS § Network Behavior).
                assert reloaded.get("default_model_name") == new_default["name"], (
                    f"After reload the persisted Default is {reloaded.get('default_model_name')!r}, "
                    f"expected the model selected before the reload, {new_default['name']!r}"
                )
                # Accordion content UNMOUNTS on collapse, so the tier selectors
                # would simply be absent (AFS § Automation Hints).
                expect(ai_providers_page.llms_section_header).to_have_attribute(
                    "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(ai_providers_page.llms_default_selector_combobox).to_have_text(
                    new_default_label, timeout=UI_ELEMENT_TIMEOUT
                )
                # Axis 2 — selector text and card badge render from the same
                # response but through different components: a persisted value
                # that fails to re-derive the badge is a real regression the
                # selector alone would hide.
                expect(ai_providers_page.card_tier_badge(new_default_label, "Default")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                # Axis 2 — a persist that ADDS rather than REPLACES: the previous
                # Default must not come back carrying the badge too. Asserted per
                # card rather than via the page-wide `all_default_badges` count,
                # which also counts other sections' Default badges and so goes
                # false-red whenever stale `expandSection` route state leaves
                # another accordion open (AFS ELITEA-2414 § Gap assertions
                # sanctions this substitution; digest § Quirk records the hazard).
                # NB a model may hold two tiers at once, so the assertion targets
                # the "Default" badge specifically, never "no badges at all".
                expect(ai_providers_page.card_tier_badge(original_default_label, "Default")).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                # Axis 2 — the three tiers share one POST endpoint discriminated
                # only by a `section` field, so a regression writing the wrong
                # section would move a tier this case never touched.
                if original_high_label and captured_high_text:
                    expect(ai_providers_page.llms_high_tier_selector_combobox).to_have_text(
                        captured_high_text.strip(), timeout=UI_ELEMENT_TIMEOUT
                    )
                if original_low_label and captured_low_text:
                    expect(ai_providers_page.llms_low_tier_selector_combobox).to_have_text(
                        captured_low_text.strip(), timeout=UI_ELEMENT_TIMEOUT
                    )

            with allure.step("Step 7 — Navigate to a brand-new (not-yet-sent) chat conversation"):
                chat_page.navigate_to_chat()

            with allure.step("Step 8 — Verify the selected Default model is used when starting a chat"):
                selected_model = chat_page.get_selected_model()
                assert selected_model == new_default_label, (
                    f"Expected the new-chat model selector to show the newly-set Default "
                    f"model {new_default_label!r}, got {selected_model!r}"
                )

            with allure.step(
                "Step 9a — High-tier: repeat selector+badge mechanics (per AFS Case-text drift, "
                "no new-chat model claim for this tier)"
            ):
                ai_providers_page.navigate()
                expect(ai_providers_page.llms_high_tier_selector_combobox).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                new_high = pick_alternative_llm_model(items, original_high["value"], tier_field="high_tier")
                new_high_value = f"{new_high['name']}<<>>{new_high['project_id']}"
                new_high_label = new_high.get("display_name") or new_high["name"]
                response = ai_providers_page.select_tier_model(
                    ai_providers_page.llms_high_tier_selector_combobox, new_high_value
                )
                assert response.status == 200, f"Expected 200 setting High-tier model, got {response.status}"
                assert response.json() == {"result": "success"}, (
                    f"Unexpected save response body: {response.json()}"
                )
                expect(ai_providers_page.llms_high_tier_selector_combobox).to_have_text(
                    new_high_label, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(ai_providers_page.card_tier_badge(new_high_label, "High-Tier")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                if original_high_label:
                    expect(ai_providers_page.card_tier_badge(original_high_label, "High-Tier")).to_have_count(
                        0, timeout=UI_ELEMENT_TIMEOUT
                    )

            with allure.step(
                "Step 9b — Low-tier: repeat selector+badge mechanics (per AFS Case-text drift, "
                "no new-chat model claim for this tier)"
            ):
                new_low = pick_alternative_llm_model(items, original_low["value"], tier_field="low_tier")
                new_low_value = f"{new_low['name']}<<>>{new_low['project_id']}"
                new_low_label = new_low.get("display_name") or new_low["name"]
                response = ai_providers_page.select_tier_model(
                    ai_providers_page.llms_low_tier_selector_combobox, new_low_value
                )
                assert response.status == 200, f"Expected 200 setting Low-tier model, got {response.status}"
                assert response.json() == {"result": "success"}, (
                    f"Unexpected save response body: {response.json()}"
                )
                expect(ai_providers_page.llms_low_tier_selector_combobox).to_have_text(
                    new_low_label, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(ai_providers_page.card_tier_badge(new_low_label, "Low-Tier")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                if original_low_label:
                    expect(ai_providers_page.card_tier_badge(original_low_label, "Low-Tier")).to_have_count(
                        0, timeout=UI_ELEMENT_TIMEOUT
                    )
        finally:
            with allure.step("Cleanup — restore original Default/High-tier/Low-tier LLM tier values"):
                try:
                    ai_providers_page.navigate()
                except Exception as exc:
                    logger.warning("Cleanup: failed to navigate back to AI Providers page: %s", exc)

                for tier_name, combobox, original in (
                    ("Default", ai_providers_page.llms_default_selector_combobox, original_default),
                    ("High-tier", ai_providers_page.llms_high_tier_selector_combobox, original_high),
                    ("Low-tier", ai_providers_page.llms_low_tier_selector_combobox, original_low),
                ):
                    if not original["value"]:
                        logger.warning(
                            "Cleanup: %s tier started UNSET on the shared project and the MUI "
                            "dropdown offers no clear/blank option -- cannot restore to unset via "
                            "the UI (AFS Cleanup). Left at whatever this test set it to.",
                            tier_name,
                        )
                        continue
                    try:
                        response = ai_providers_page.select_tier_model(combobox, original["value"])
                        if response.status != 200:
                            logger.warning(
                                "Cleanup: restoring %s tier to %r returned status %s (expected 200)",
                                tier_name, original["value"], response.status,
                            )
                    except Exception as exc:
                        logger.warning(
                            "Cleanup: failed to restore %s tier to %r: %s", tier_name, original["value"], exc
                        )

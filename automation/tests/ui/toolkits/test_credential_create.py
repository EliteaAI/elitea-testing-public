"""Test for Credential — Create (GitHub, Token auth) via sidebar "+" button.

Verifies the full credential-creation happy path: navigating to the
Credentials list, opening the creation form via the sidebar "+" button,
selecting the GitHub credential type, filling in the Display Name and a
Token-auth Access Token, saving, and confirming the new credential appears
in the list with the correct name and type badge.

Test case: ELITEA-1962
AFS: test-specs/toolkits-credentials/l1_create-credential_ELITEA-1962.md

Precondition (live-discovered, not in the original case text): a
zero-credential project auto-redirects ``/credentials/all`` straight to
``/credentials/create-credential`` (``CredentialsList.jsx``), so a throwaway
seed credential is created via API first — matching the seed pattern already
used by ``test_credential_pin_unpin.py``.
"""

import logging
import re
import time

import allure
import pytest
from playwright.sync_api import expect

from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credentials_list_page import CredentialsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]

SAVE_RESPONSE_TIMEOUT = 15_000


def _is_known_291_warning(msg) -> bool:
    """Filter the pre-existing, already-filed CredentialTypeSelector.jsx /
    GroupedCategory.jsx "missing key prop" dev warning
    (elitea-testing-public#291) — same filter established by
    test_credential_search_by_name.py, reused here since this test also
    renders the type-selector grid (Step 2).
    """
    text = msg.text
    return (
        'unique "key" prop' in text
        or ("validateDOMNesting" in text and "<p>" in text)
        or ("validateDOMNesting" in text and "%s" in text)
    )


class TestCredentialCreate:
    """ELITEA-1962 — Create a GitHub credential (Token auth) via the sidebar "+" button."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1962_create-credential.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_create_github_credential_via_sidebar_button(self, page, credential_api):
        """Create a GitHub credential with Token auth via the sidebar "+" button
        and verify it appears in the list with the correct name and type badge."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        ts = int(time.time())
        seed_name = f"autotest_seed_{ts}"[:32]
        display_name = f"autotest_credential_{ts}"
        seed_id = None
        credential_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_291_warning(msg):
                console_messages.append(msg)

        try:
            with allure.step(
                "Precondition — Seed one throwaway GitHub credential via API so the "
                "project has >=1 credential (a zero-credential project auto-redirects "
                "away from the list page, per CredentialsList.jsx)"
            ):
                seed = credential_api.create_github_credential(
                    display_name=seed_name,
                    base_url=settings.github_base_url,
                    token="unused-token-never-validated-by-this-case",
                )
                seed_id = seed["id"]
                assert seed_id, "Expected a numeric id for the seed credential"
                logger.info("Created seed credential id=%s name=%s", seed_id, seed_name)

            list_page = CredentialsListPage(page)
            create_page = CredentialCreatePage(page)

            with allure.step("Step 1 — Navigate to the Credentials section from the sidebar"):
                list_page.navigate()
                page.on("console", _on_console)

                assert list_page.entity_card.first.is_visible(), (
                    "Expected at least one credential card (the seed) on the Credentials list page"
                )
                assert list_page.create_button.is_visible(), (
                    "Expected the sidebar '+' create button to be visible on the Credentials list"
                )

            with allure.step('Step 2 — Click the "+" button in the sidebar header'):
                list_page.create_button.click()
                page.wait_for_url(
                    re.compile(r".*/credentials/create-credential(\?.*)?$"),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                )
                assert "viewMode=owner" in page.url, (
                    f"Expected 'viewMode=owner' in the type-selector URL, got {page.url}"
                )
                expect(create_page.type_card("github")).to_be_visible()

            with allure.step('Step 3 — Select credential type "Github"'):
                create_page.click_type_card("github")
                assert "/credentials/create-credential/github" in page.url, (
                    f"Expected the URL to become /credentials/create-credential/github, got {page.url}"
                )
                assert create_page.display_name_input.is_visible(), (
                    "Expected the GitHub-specific create form (Display Name field) to render"
                )
                assert create_page.save_button.is_visible(), (
                    "Expected the Save button to render on the GitHub create form"
                )

            with allure.step(f"Step 4 — Fill in Display Name: {display_name!r}"):
                create_page.set_display_name(display_name)
                assert create_page.display_name_input.input_value() == display_name, (
                    f"Display Name field should show {display_name!r} after filling"
                )
                # ID field live-mirrors the Display Name (ELITEA-1972 pattern) — no
                # lowercase/underscore transform needed since display_name is already
                # in that shape.
                assert create_page.id_input.input_value() == display_name, (
                    f"ID field should live-mirror the Display Name as {display_name!r}, "
                    f"got {create_page.id_input.input_value()!r}"
                )
                assert create_page.is_save_enabled(), (
                    "Save should become enabled once Display Name is filled "
                    "(Base Url ships pre-filled, Anonymous is the default auth)"
                )

            with allure.step('Step 5 — Select "Token" radio button as the auth method'):
                create_page.select_auth_method("token")
                assert create_page.auth_radio("token").is_checked(), (
                    "The 'Token' auth radio should be checked after clicking it"
                )
                expect(create_page.access_token_input).to_be_visible()

            with allure.step("Step 6 — Fill in the Access Token value"):
                create_page.set_access_token(settings.git_hub_token)
                assert create_page.access_token_input.get_attribute("type") == "password", (
                    "Access Token field should be masked (type=password)"
                )
                # Length-only check — never assert/interpolate the real token value,
                # so it can't leak into an assertion-failure message or log (AFS Test
                # Data: never type or log the real GIT_HUB_TOKEN value).
                typed_length = len(create_page.access_token_input.input_value())
                assert typed_length == len(settings.git_hub_token), (
                    f"Access Token field should contain the full token "
                    f"({len(settings.git_hub_token)} chars), got {typed_length} chars"
                )

            with allure.step("Step 7 — Click Save"):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as create_response_info:
                    create_page.save_button.click()
                create_response = create_response_info.value
                assert create_response.status == 200, (
                    f"Expected 200 from the credential-create POST, got {create_response.status}"
                )
                create_body = create_response.json()
                credential_id = create_body.get("id")
                assert credential_id, "Expected a numeric id in the create response"
                assert create_body.get("label") == display_name, (
                    f"Expected created credential label {display_name!r}, got {create_body.get('label')!r}"
                )
                assert create_body.get("type") == "github", (
                    f"Expected created credential type 'github', got {create_body.get('type')!r}"
                )
                assert create_body.get("elitea_title") == display_name, (
                    f"Expected created credential elitea_title {display_name!r}, "
                    f"got {create_body.get('elitea_title')!r}"
                )
                page.wait_for_url(
                    re.compile(r".*/credentials/all/?(\?.*)?$"), timeout=SAVE_RESPONSE_TIMEOUT
                )

            with allure.step(
                "Step 8 — Verify the credential appears in the list with the correct "
                "name and Github type badge"
            ):
                # Save redirects to a list that already includes the new card
                # (created_at desc ordering) — no further navigate()/re-fetch needed,
                # per the AFS's Network Behavior section.
                matching_cards = list_page.entity_card_name.filter(has_text=display_name)
                expect(matching_cards).to_have_count(1)
                rendered_name = matching_cards.first.text_content() or ""
                assert rendered_name == display_name, (
                    f"Expected the card name to exactly match the created display name "
                    f"{display_name!r}, got {rendered_name!r}"
                )
                # Case's literal Pass/Fail wording ("autotest_credential is listed") —
                # prefix check rather than exact-equals, since this suite timestamps
                # every display name to avoid cross-run collisions (established
                # pattern across every sibling test_credential_*.py).
                assert rendered_name.startswith("autotest_credential"), (
                    f"Rendered card name should start with 'autotest_credential' "
                    f"(the case's literal Pass/Fail wording), got {rendered_name!r}"
                )
                badge_text = list_page.get_type_badge(display_name)
                assert badge_text == "Github", (
                    f"Expected the credential's type badge to read 'Github', got {badge_text!r}"
                )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — delete the case's own credential and the seed credential"):
                if credential_id is not None:
                    credential_api.delete_credential(int(credential_id))
                    logger.info("Deleted credential id=%s", credential_id)
                if seed_id is not None:
                    credential_api.delete_credential(seed_id)
                    logger.info("Deleted seed credential id=%s", seed_id)

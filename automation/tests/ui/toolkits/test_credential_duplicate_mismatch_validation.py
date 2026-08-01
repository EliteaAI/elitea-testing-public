"""Test for Credential — Duplicate/Mismatch Validation.

Verifies the system rejects creating a second credential with a
Display-Name collision (the ID field live-mirrors Display Name, so the
collision fires on ``elitea_title``), surfaces the exact backend error text,
and that saving with an empty required field is blocked.

Known defect (github.com/EliteaAI/elitea-testing-public#1004): once "Token"
auth is selected on the GitHub create form, the Access Token field is NOT
enforced as required — Save stays enabled and the backend persists a
credential with ``access_token: null``. Asserted with ``expect.soft()`` per
the sanctioned-RED merge-gate exception (deterministic, single-cause, linked
to an OPEN defect) — this test stays honestly RED for that one cause until
the product fix ships.

Test case: ELITEA-1978
AFS: test-specs/toolkits-credentials/l1_credential-duplicate-mismatch-validation_ELITEA-1978.md
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]

SAVE_RESPONSE_TIMEOUT = 15_000


class TestCredentialDuplicateMismatchValidation:
    """ELITEA-1978 — Duplicate credential name rejected; empty required fields validated."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "toolkits-credentials/ELITEA-1978_credential-duplicate-mismatch-validation.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1004", "Known defect #1004")
    @pytest.mark.p1
    def test_credential_duplicate_and_empty_required_field_validation(self, page, credential_api):
        """Duplicate elitea_title is rejected with the exact backend message;
        empty Display Name blocks Save; empty Access Token does NOT (known defect #1004)."""
        if not settings.git_hub_token:
            pytest.skip("GIT_HUB_TOKEN not set in .env.test - required for credential test data")

        # Display Name / ID mirror is capped client-side at MAX_NAME_LENGTH=32
        # chars (EliteaUI src/common/constants.js) — a 6-digit suffix keeps
        # the full name under that cap so the UI-typed value never truncates
        # against the API-seeded elitea_title (a truncation mismatch here
        # would silently break the duplicate-collision repro).
        ts = str(int(time.time() * 1000))[-6:]
        duplicate_name = f"autotest_duplicate_cred_{ts}"
        seed_id = None
        empty_token_credential_id = None

        try:
            with allure.step(f"Step 1 — Create a seed credential named {duplicate_name!r}"):
                seed = credential_api.create_github_credential(
                    display_name=duplicate_name,
                    base_url=settings.github_base_url,
                    token=settings.git_hub_token,
                    elitea_title=duplicate_name,
                )
                seed_id = seed["id"]
                assert seed_id, "Expected a numeric id for the seed credential"

            create_page = CredentialCreatePage(page)

            with allure.step(
                "Step 2 — Navigate to a fresh create-credential form, fill Display Name "
                "with the SAME name, select Token auth, fill Access Token"
            ):
                create_page.navigate_to_type("github")
                create_page.set_display_name(duplicate_name)
                assert create_page.id_input.input_value() == duplicate_name, (
                    f"ID field should live-mirror the Display Name as {duplicate_name!r} — "
                    f"this is WHY the collision fires on elitea_title, not a separate 'name' "
                    f"field, got {create_page.id_input.input_value()!r}"
                )
                create_page.select_auth_method("token")
                create_page.set_access_token(settings.git_hub_token)

            with allure.step("Step 3 — Click Save"):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as dup_response_info:
                    create_page.save_button.click()
                dup_response = dup_response_info.value
                assert dup_response.status == 400, (
                    f"Expected 400 for the duplicate elitea_title, got {dup_response.status}"
                )
                dup_body = dup_response.json()
                expected_error = f"Credential with ID '{duplicate_name}' already exists"
                assert dup_body.get("error") == expected_error, (
                    f"Expected error {expected_error!r}, got {dup_body.get('error')!r}"
                )
                assert dup_body.get("field") == "elitea_title", (
                    f"Expected the error's field to be 'elitea_title', got {dup_body.get('field')!r}"
                )

            with allure.step(
                "Step 4 — Verify the error is visible to the user; form does not navigate away"
            ):
                expect(create_page.api_error_message).to_be_visible()
                assert expected_error in (create_page.api_error_message.text_content() or ""), (
                    f"Expected the on-page error text to contain {expected_error!r}, "
                    f"got {create_page.api_error_message.text_content()!r}"
                )
                assert "/credentials/create-credential/github" in page.url, (
                    f"Expected the form to stay on the create page after the 400, got {page.url}"
                )

            with allure.step(
                "Step 5 — Start a fresh form, fill Display Name only (baseline, non-soft): "
                "Save becomes enabled"
            ):
                fresh_name = f"autotest_dup_baseline_{ts}"
                create_page.navigate_to_type("github")
                create_page.set_display_name(fresh_name)
                expect(create_page.save_button).to_be_enabled()

            with allure.step(
                "Step 6 — Select Token auth, leave Access Token EMPTY: Save should be "
                "disabled (Known defect: #1004 — Save incorrectly stays enabled)"
            ):
                create_page.select_auth_method("token")
                expect.soft(create_page.save_button).to_be_disabled()

                # The regression is real and reported, not swallowed: prove the
                # empty-Token save actually succeeds server-side today (Axis 2 —
                # separately, hard-asserted so the defect's shape stays visible
                # even once the soft assertion above is the only thing failing).
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as empty_token_response_info:
                    create_page.save_button.click()
                empty_token_response = empty_token_response_info.value
                assert empty_token_response.status == 200, (
                    f"Known defect #1004: expected the empty-Token save to succeed "
                    f"(200) today, got {empty_token_response.status} — if this now "
                    f"fails, #1004 may have shipped a fix; re-check the soft "
                    f"assertion above too"
                )
                empty_token_body = empty_token_response.json()
                empty_token_credential_id = empty_token_body.get("id")
                assert empty_token_body.get("data", {}).get("access_token") is None, (
                    f"Known defect #1004: expected the persisted credential's "
                    f"access_token to be null, got "
                    f"{empty_token_body.get('data', {}).get('access_token')!r}"
                )

            with allure.step(
                "Verify no second duplicate-name record was created (list-absence check)"
            ):
                all_credentials = credential_api.list_all_credentials()
                matching = [c for c in all_credentials if c.get("elitea_title") == duplicate_name]
                assert len(matching) == 1, (
                    f"Expected exactly 1 credential with elitea_title={duplicate_name!r} "
                    f"(the seed), found {len(matching)}: {matching}"
                )
                assert matching[0]["id"] == seed_id, (
                    f"Expected the single matching credential to be the seed "
                    f"(id={seed_id}), got id={matching[0]['id']}"
                )

        finally:
            with allure.step("Cleanup — delete the seed credential and the empty-Token credential"):
                if seed_id is not None:
                    credential_api.delete_credential(seed_id)
                    logger.info("Deleted seed credential id=%s", seed_id)
                if empty_token_credential_id is not None:
                    credential_api.delete_credential(int(empty_token_credential_id))
                    logger.info("Deleted empty-Token credential id=%s", empty_token_credential_id)

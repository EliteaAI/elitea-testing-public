"""Test for Credential — Duplicate/Mismatch Validation.

Verifies two independent behaviors of the Create-Credential form (GitHub
type): (1) attempting to Save a credential whose Display Name collides with
an already-existing one is rejected, with the backend's literal error
message surfaced to the user and no duplicate record created; (2) the
general "empty required field blocks Save" mechanism holds at baseline
(every field empty).

Known defect (github.com/EliteaAI/elitea-testing-public#1004): the case's
own named example for (2) — selecting "Token" auth and leaving the
resulting "Access Token" field empty — does NOT block Save. Root cause:
``validateRequiredFields()`` (``EliteaUI/src/[fsd]/features/toolkits/lib/
helpers/toolBase.helpers.js``) only iterates the credential type's static
``schema.required`` array; ``access_token`` is necessarily absent from
GitHub's base required set (only one of Access Token / Username+Password /
App private key is actually needed, depending on which auth radio is
selected) and nothing adds a conditional required-check for the
currently-selected auth method. The backend independently accepts the
empty value too, persisting a listed-but-non-functional credential
(``status_ok: false``). Asserted as the correct (buggy) live behavior via
``expect.soft()`` (Save-enabled state) and a ``soft_failures`` list +
``pytest.fail()`` (raw values from the persisted-record GET — Playwright's
``expect.soft()`` only supports Page/Locator/APIResponse, same idiom
already established by ``test_support_assistant_smoke.py`` /
``test_fork_agent_to_different_project.py``) per this project's no-masking
policy — stays RED until #1004 is fixed. This is a distinct manifestation
of the same underlying gap as #526 (Display Name never being in
``schema.required`` at all, see
``test_credential_required_fields_validation.py``) — same root helper,
different field/scenario, filed separately per this repo's strict-per-bug
policy.

Test case: ELITEA-1978
AFS: test-specs/toolkits-credentials/l2_credential-duplicate-mismatch-validation_ELITEA-1978.md
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.credential_create_page import CredentialCreatePage
from pages.credentials_list_page import CredentialsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression]

SAVE_RESPONSE_TIMEOUT = 15_000


def _is_known_291_warning(msg) -> bool:
    """Filter the pre-existing, already-filed CredentialTypeSelector.jsx /
    GroupedCategory.jsx "missing key prop" dev warning
    (elitea-testing-public#291) — same filter established by
    test_credential_create.py / test_credential_search_by_name.py.
    """
    text = msg.text
    return (
        'unique "key" prop' in text
        or ("validateDOMNesting" in text and "<p>" in text)
        or ("validateDOMNesting" in text and "%s" in text)
    )


def _is_known_518_warning(msg) -> bool:
    """Filter the pre-existing, already-filed, OPEN CredentialsList.jsx
    double-``onRefetch()`` crash (elitea-testing-public#518) — this test's
    successful Save clicks (Steps 3 and 9) redirect to ``/credentials/all``,
    the same landing page this crash reproduces on (~60-75%), per the
    identical filter established by test_credential_create.py.
    """
    text = msg.text
    return (
        "Cannot refetch a query that has not been started yet" in text
        or ("above error occurred" in text and "<CredentialsList>" in text)
    )


def _is_known_554_warning(msg) -> bool:
    """Filter the pre-existing, already-filed elitea-testing-public#554 — an
    RTK-Query timing race in ``EliteaUI/src/api/toolkits.js``'s
    ``toolkitTypes`` endpoint, live-confirmed reproducible on any
    create-credential-form render; this test navigates to that form four
    times. Same filter established by test_credential_create.py /
    test_credential_search_by_name.py.
    """
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _is_expected_negative_path_network_log(msg) -> bool:
    """Filter the browser's own automatic network-layer log for the
    INTENTIONALLY-triggered 400s this test provokes (Step 6's duplicate-name
    rejection, Step 9's known-defect-#1004 empty-Access-Token acceptance is
    a 200 so this doesn't apply there) — e.g. "Failed to load resource: the
    server responded with a status of 400 (Bad Request) @ ...". Not an
    application-level error; same filter/rationale already established by
    test_artifacts_duplicate_bucket_name.py for its own intentionally-
    triggered 400.
    """
    return "Failed to load resource" in msg.text


class TestCredentialDuplicateMismatchValidation:
    """ELITEA-1978 — Duplicate Display Name rejection + empty-required-field gating."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1978_credential-duplicate-mismatch-validation.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1004", "Known defect #1004")
    @pytest.mark.p1
    def test_credential_duplicate_mismatch_validation(self, page, credential_api):
        """Duplicate Display Name is rejected with the exact backend error
        message and no duplicate record is created; empty required fields
        block Save at baseline, except the auth-conditional Access Token
        field (Known defect: #1004)."""
        ts = int(time.time())
        # Display Name has a 32-char field limit (same constraint
        # test_credential_create.py's seed_name works around) — slice so the
        # timestamp suffix doesn't silently truncate mid-digit.
        duplicate_name = f"autotest_duplicate_cred_{ts}"[:32]
        empty_token_name = f"autotest_reqfields_emptytoken_{ts}"[:32]

        first_credential_id = None
        second_credential_id = None

        create_page = CredentialCreatePage(page)
        list_page = CredentialsListPage(page)
        soft_failures = []

        console_messages = []

        def _on_console(msg):
            if (
                msg.type in ("error", "warning")
                and not _is_known_291_warning(msg)
                and not _is_known_518_warning(msg)
                and not _is_known_554_warning(msg)
                and not _is_expected_negative_path_network_log(msg)
            ):
                console_messages.append(msg)

        try:
            with allure.step("Step 1 — Navigate to the credential creation form (Github type)"):
                create_page.navigate_to_type("github")
                expect(create_page.display_name_input).to_have_value("")
                expect(create_page.save_button).to_be_disabled()
                page.on("console", _on_console)

            with allure.step(f"Step 2 — Fill Display Name: {duplicate_name!r}"):
                create_page.set_display_name(duplicate_name)
                expect(create_page.display_name_input).to_have_value(duplicate_name)
                expect(create_page.save_button).to_be_enabled()

            with allure.step("Step 3 — Click Save (first, successful creation)"):
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
                first_credential_id = create_body.get("id")
                assert first_credential_id, "Expected a numeric id in the create response"
                assert create_body.get("label") == duplicate_name, (
                    f"Expected created credential label {duplicate_name!r}, got {create_body.get('label')!r}"
                )

                page.wait_for_url(lambda url: "/credentials/all" in url, timeout=SAVE_RESPONSE_TIMEOUT)
                matching_cards = list_page.entity_card_name.filter(has_text=duplicate_name)
                expect(matching_cards).to_have_count(1)

            with allure.step("Step 4 — Navigate to the credential creation form again (fresh instance)"):
                create_page.navigate_to_type("github")
                expect(create_page.display_name_input).to_have_value("")
                expect(create_page.save_button).to_be_disabled()

            with allure.step(f"Step 5 — Fill Display Name with the SAME value: {duplicate_name!r}"):
                create_page.set_display_name(duplicate_name)
                expect(create_page.display_name_input).to_have_value(duplicate_name)
                # Client performs no ahead-of-time duplicate-name check — Save
                # enables regardless (matches the case's own Step 2 expected
                # result, "Credential creation form is submitted").
                expect(create_page.save_button).to_be_enabled()

            with allure.step("Step 6 — Click Save (rejected — duplicate Display Name)"):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as dup_response_info:
                    create_page.save_button.click()
                dup_response = dup_response_info.value
                # Exact status not part of the case's Pass/Fail criteria (the
                # surfaced message is) — per this AFS's Network Behavior note.
                assert dup_response.status != 200, (
                    f"Duplicate Display Name Save should be rejected, got {dup_response.status}"
                )

                # UI stays on the create form — no redirect on rejection.
                assert "/credentials/create-credential/github" in page.url, (
                    f"Expected to stay on the create form after a rejected duplicate Save, got {page.url}"
                )

                expected_error = f"Credential with ID '{duplicate_name}' already exists"
                expect(create_page.api_error_message).to_contain_text(expected_error)

                # AFS correction (live-verified this run, see amendment note
                # in the AFS file): the ID field becomes EDITABLE after the
                # duplicate-name rejection, not "stays disabled" as the AFS
                # originally claimed. Ground-truthed via a direct API probe
                # (bypassing the UI entirely) of the same duplicate-name
                # POST: the backend's error body is
                # {"error": "...", "field": "elitea_title"} — which DOES
                # match CredentialsTabBar.jsx's doSave() gate
                # (`result.error?.data?.field === 'elitea_title'`), firing
                # onEnableEditTitle() and flipping `enableEditEliteaTitle`
                # true, which un-disables the elitea_title field
                # (ToolBase.jsx: `disabled = ... || (k === 'elitea_title' &&
                # !enableEditEliteaTitle)`).
                assert not create_page.id_input.is_disabled(), (
                    "The ID field should become editable after the duplicate-name rejection "
                    "(backend error field == 'elitea_title' enables editing)"
                )

                # Exactly one credential with this Display Name exists
                # afterward — the duplicate attempt did not create a second
                # record (case's own Fail criteria names this explicitly).
                all_credentials = credential_api.list_all_credentials()
                matches = [c for c in all_credentials if c.get("label") == duplicate_name]
                assert len(matches) == 1, (
                    f"Expected exactly 1 credential named {duplicate_name!r}, found {len(matches)}"
                )

            with allure.step(
                "Step 7 — Navigate to the credential creation form again; leave all fields empty"
            ):
                create_page.navigate_to_type("github")
                expect(create_page.display_name_input).to_have_value("")
                # Baseline mechanism: with every field at its initial/empty
                # state, Save is disabled (already proven end-to-end by the
                # MERGED ELITEA-1975 spec; re-confirmed here as this case's
                # own Preconditions to Step 8's isolated defect).
                expect(create_page.save_button).to_be_disabled()

            with allure.step(
                f"Step 8 — Fill Display Name {empty_token_name!r}, select Token auth, leave "
                "Access Token empty (Known defect: #1004)"
            ):
                create_page.set_display_name(empty_token_name)
                create_page.select_auth_method("token")
                expect(create_page.auth_radio("token")).to_be_checked()
                expect(create_page.access_token_input).to_be_visible()

                # Known defect: #1004 — an empty, auth-conditional Access
                # Token field is not validated as required
                # (validateRequiredFields() only reads the static
                # schema.required list); Save should stay disabled per the
                # case's own Step 6 wording, but does not. Asserting the
                # live (buggy) behavior as correct, per
                # .agents/testing.md's Merge gate "Analysis-time entry".
                # (The case's own "no asterisk on the label" observation is
                # the SAME underlying defect — source-traced to the same
                # `required` boolean that gates Save — and is a DECLARED,
                # justified gap, not independently asserted here: no
                # sanctioned shape exists to place a testid on the asterisk
                # (it's a literal character in a JSX label STRING, not its
                # own DOM node, inside SecretField.jsx — a component shared
                # by every secret/token field app-wide). See AFS "Row 6
                # disposition note" for the full narrowing rationale; the
                # Save-gating behavior below is the asserted, functionally
                # decisive signal for this defect.)
                expect.soft(create_page.save_button).to_be_disabled()

            with allure.step(
                "Step 9 — Click Save with Access Token still empty (Known defect: #1004, "
                "functional dimension)"
            ):
                with page.expect_response(
                    lambda r: (
                        f"/configurations/configurations/{settings.elitea_project_id}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=SAVE_RESPONSE_TIMEOUT,
                ) as empty_token_response_info:
                    create_page.save_button.click()
                empty_token_response = empty_token_response_info.value

                # Known defect: #1004 — raw response/JSON values, not a
                # Locator/Page/APIResponse, so expect.soft() doesn't apply
                # directly (Playwright Python limitation) — aggregated via
                # the pytest-native soft-assertion equivalent (soft_failures
                # + a single trailing pytest.fail()), same idiom already
                # established by test_support_assistant_smoke.py /
                # test_fork_agent_to_different_project.py.
                if empty_token_response.status != 200:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1004: "
                        f"expected the backend to also accept (200) the empty Access Token, "
                        f"got {empty_token_response.status}"
                    )
                else:
                    second_credential_id = empty_token_response.json().get("id")
                    assert second_credential_id, "Expected a numeric id in the create response"

                    persisted = credential_api.get_credential(int(second_credential_id))
                    persisted_access_token = persisted.get("data", {}).get("access_token")
                    persisted_status_ok = persisted.get("status_ok")
                    # AFS says the persisted access_token reads back as ""
                    # (the analyst's own run); live-verified this run it's
                    # actually `None` (key omitted rather than stored empty)
                    # — same underlying defect (a falsy/absent value was
                    # accepted and persisted), just a JSON-shape difference
                    # from the AFS's exact wording, not a different finding.
                    if persisted_access_token:
                        soft_failures.append(
                            "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1004: "
                            f"expected the persisted access_token to be empty/absent, got {persisted_access_token!r}"
                        )
                    if persisted_status_ok is not False:
                        soft_failures.append(
                            "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1004: "
                            f"expected status_ok False for the non-functional credential, "
                            f"got {persisted_status_ok!r}"
                        )

            with allure.step("Side-channel check — no console errors/warnings across the full flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

            if soft_failures:
                pytest.fail(
                    "Known defect(s) detected (test still completed all steps):\n"
                    + "\n".join(soft_failures)
                )

        finally:
            with allure.step("Cleanup — delete both credentials created during this run"):
                if first_credential_id is not None:
                    credential_api.delete_credential(int(first_credential_id))
                    logger.info("Deleted credential id=%s", first_credential_id)
                if second_credential_id is not None:
                    credential_api.delete_credential(int(second_credential_id))
                    logger.info("Deleted credential id=%s", second_credential_id)

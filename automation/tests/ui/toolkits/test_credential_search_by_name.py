"""Test for Search Credentials by Name.

Verifies the Credentials list's search box (shared ``SearchBar`` component):
partial-name and full-prefix matches return the correct filtered set, a
no-match query shows the empty state, and clearing the search box restores
the full list.

Search is explicit-activation (Enter or the send icon), never live-filter-
as-you-type — confirmed live via ``EliteaUI/src/components/SearchBar.jsx``
(``onChange`` only updates local state; the actual
``dispatch(actions.setQuery(...))`` fires exclusively from ``onSearch()``,
wired to ``onKeyDown``/Enter or the send icon's ``onClick``).

Known defect (github.com/EliteaAI/elitea-testing-public#551): clearing the
search box after a **zero-results** search redirects to
``/credentials/create-credential`` instead of restoring the list. Root cause
(``CredentialsList.jsx``'s "redirect an empty project to Create Credential"
``useEffect`` guard: ``!hasQuery && total === 0``) — ``onClear()`` flips
``hasQuery`` to ``false`` synchronously while ``total`` is still the stale
``0`` from the just-cleared zero-results search until the unfiltered list
re-fetch completes, a one-render race that fires the empty-*project* redirect
for a merely empty-*filtered-view* project. Scoped to the zero-results path
only — clearing after a non-empty-result search works correctly (asserted as
a control check below). Asserted with ``expect.soft()`` per this project's
no-masking policy — the assertion stays RED until #551 is fixed.

Test case: ELITEA-1965
AFS: test-specs/toolkits-credentials/l2_search-credentials-by-name_ELITEA-1965.md
"""

import logging
import re
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.credential_create_page import CredentialCreatePage
from pages.credentials_list_page import CredentialsListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p2, pytest.mark.regression]

SEARCH_ALPHA = "alpha"
SEARCH_PREFIX = "autotest_cred"
SEARCH_NO_MATCH = "nonexistent_xyz"
CREATE_RESPONSE_TIMEOUT = 15_000


class TestCredentialSearchByName:
    """ELITEA-1965 — Credentials list search box filters by name."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1965_search-credentials-by-name.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/551", "Known defect #551")
    def test_search_credentials_by_name(self, page, credential_api):
        """Search filters credentials server-side; clearing restores the list
        (known defect: not after a zero-results search — #551)."""
        ts = str(int(time.time()))
        name_alpha = f"autotest_cred_alpha_{ts}"
        name_beta = f"autotest_cred_beta_{ts}"
        name_gamma = f"autotest_cred_gamma_{ts}"
        seeded_names = {name_alpha, name_beta, name_gamma}
        seeded_ids: list[int] = []

        # Console listener — same pre-existing-warning filter as
        # test_mcp_edit_toggle_enable_caching.py / test_skill_tag_filter.py:
        # Step 1's repeated create-credential navigations render the
        # /credentials/create-credential type-selector grid
        # (CredentialTypeSelector.jsx / GroupedCategory.jsx), which emits a
        # pre-existing React "missing key prop" dev warning already tracked
        # as EliteaAI/elitea-testing-public#291 — filtering it out (rather
        # than merely delaying listener registration) avoids a race with
        # React's async warning-logging timing, so a real regression in this
        # case's own search flow isn't masked by an unrelated, already-filed
        # warning.
        def _is_known_291_warning(msg) -> bool:
            text = msg.text
            return (
                'unique "key" prop' in text
                or ("validateDOMNesting" in text and "<p>" in text)
                or ("validateDOMNesting" in text and "%s" in text)
            )

        def _is_known_554_warning(msg) -> bool:
            # Newly discovered during this implementation, filed as
            # elitea-testing-public#554: an RTK-Query timing race in
            # EliteaUI/src/api/toolkits.js's `toolkitTypes` endpoint fires
            # before `useSelectedProjectId()` resolves, building the URL
            # with an empty projectId segment (".../toolkits/prompt_lib/")
            # which 404s. Intermittent (client-side race, not deterministic),
            # unrelated to Credentials search — the "TYPES" filter panel
            # renders correctly once the query re-fires with a real id.
            # Filtered like #291 (background noise unrelated to this case's
            # own flow) rather than soft-tracked (which would imply it's a
            # symptom of the flow under test).
            location_url = (msg.location or {}).get("url", "")
            return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url

        def _on_console(msg):
            if (
                msg.type in ("error", "warning")
                and not _is_known_291_warning(msg)
                and not _is_known_554_warning(msg)
            ):
                console_messages.append(msg)

        console_messages = []
        page.on("console", _on_console)

        try:
            with allure.step("Step 1 — Create three credentials with distinct/overlapping-prefix names"):
                create_page = CredentialCreatePage(page)
                for name in (name_alpha, name_beta, name_gamma):
                    create_page.navigate_to_type("github")
                    create_page.set_display_name(name)
                    with page.expect_response(
                        lambda r: "/configurations/configurations/" in r.url and r.request.method == "POST",
                        timeout=CREATE_RESPONSE_TIMEOUT,
                    ) as create_response_info:
                        create_page.save_button.click()
                    create_body = create_response_info.value.json()
                    seeded_ids.append(create_body["id"])
                    create_page.wait_for_network()

                list_page = CredentialsListPage(page)
                list_page.navigate()
                visible_names = set(list_page.get_display_name_order())
                assert seeded_names <= visible_names, (
                    f"Expected all three seeded credentials {seeded_names} to appear as cards, "
                    f"got {visible_names}"
                )

            with allure.step("Step 2 — Navigate to /credentials/all: page loads, search box present and empty"):
                list_page.navigate()
                baseline_names = set(list_page.get_display_name_order())
                assert seeded_names <= baseline_names, (
                    f"Expected the 3 seeded credentials to still be present on a fresh list load, "
                    f"got {baseline_names}"
                )
                expect(list_page.search_input).to_have_value("")

            with allure.step(
                "Step 3 — Type 'alpha' and press Enter: only autotest_cred_alpha is displayed"
            ):
                search_response = list_page.search(SEARCH_ALPHA)
                assert search_response.status == 200, (
                    f"Expected 200 from the filtered configurations GET, got {search_response.status}"
                )
                # Auto-retrying count assertion — the response resolving does not
                # guarantee the React re-render has committed yet.
                expect(list_page.entity_card_name).to_have_count(1)
                filtered_names = set(list_page.get_display_name_order())
                assert filtered_names == {name_alpha}, (
                    f"Expected only {name_alpha!r} after searching 'alpha', got {filtered_names}"
                )

            with allure.step(
                "Step 4 — Clear and type 'autotest_cred': all three seeded credentials shown, "
                "unrelated pre-existing credentials excluded"
            ):
                list_page.clear_search()
                search_response = list_page.search(SEARCH_PREFIX)
                assert search_response.status == 200, (
                    f"Expected 200 from the filtered configurations GET, got {search_response.status}"
                )
                expect(list_page.entity_card_name).to_have_count(len(seeded_names))
                filtered_names = set(list_page.get_display_name_order())
                assert filtered_names == seeded_names, (
                    f"Expected exactly the 3 seeded credentials {seeded_names} after searching "
                    f"'autotest_cred', got {filtered_names} (pre-existing credentials must be excluded)"
                )

            with allure.step(
                "Step 5 — Clear and type 'nonexistent_xyz': empty state renders, total=0"
            ):
                list_page.clear_search()
                search_response = list_page.search(SEARCH_NO_MATCH)
                search_body = search_response.json()
                assert search_response.status == 200, (
                    f"Expected 200 from the no-match configurations GET, got {search_response.status}"
                )
                assert search_body.get("total") == 0, (
                    f"Expected total=0 for a no-match search, got {search_body.get('total')}"
                )
                expect(list_page.search_empty_state).to_be_visible()

            with allure.step(
                "Step 6 — Click the search box's Clear (X) icon after the zero-results search: "
                "the full list should be restored and the URL should stay /credentials/all "
                "(Known defect: #551 — redirects to /credentials/create-credential instead)"
            ):
                list_page.clear_search()
                # Known defect: #551 — clearing a zero-results search redirects away from
                # /credentials/all instead of restoring the list. Soft assertions so the
                # control check below still runs; stays RED until #551 ships a fix, per
                # .agents/testing.md's no-masking policy. Asserting the full baseline COUNT
                # (not just "a card is visible") — the filtered zero-results view has 0 cards,
                # so a naive "any card visible" check would already distinguish restored vs
                # not, but matching the exact baseline count also catches a partial restore.
                expect.soft(page).to_have_url(re.compile(r".*/credentials/all$"))
                expect.soft(list_page.entity_card_name).to_have_count(len(baseline_names))
                if "/credentials/all" in page.url and list_page.entity_card_name.count() == len(
                    baseline_names
                ):
                    restored_names = set(list_page.get_display_name_order())
                    assert seeded_names <= restored_names, (
                        f"Expected the full list (including the 3 seeded credentials) to be "
                        f"restored after Clear, got {restored_names}"
                    )

            with allure.step(
                "Control check (Axis 2) — clearing after a NON-empty-result search restores the "
                "list correctly (defect #551 is scoped to the zero-results path only)"
            ):
                # Recover to a clean /credentials/all regardless of whether the known defect
                # fired above — a real client-side navigation resets the search Redux slice.
                list_page.navigate()
                list_page.search(SEARCH_ALPHA)
                expect(list_page.entity_card_name).to_have_count(1)
                filtered_names = set(list_page.get_display_name_order())
                assert filtered_names == {name_alpha}, (
                    f"Expected only {name_alpha!r} after re-searching 'alpha', got {filtered_names}"
                )

                list_page.clear_search()
                assert "/credentials/all" in page.url, (
                    "Clearing after a non-empty-result search must NOT navigate away "
                    f"from /credentials/all, got {page.url}"
                )
                # Auto-retrying count assertion against the Step 2 baseline — not just
                # "a card is visible" (the still-filtered "alpha" view already has one).
                expect(list_page.entity_card_name).to_have_count(len(baseline_names))
                restored_names = set(list_page.get_display_name_order())
                assert seeded_names <= restored_names, (
                    f"Expected the full list restored after clearing a non-empty-result search, "
                    f"got {restored_names}"
                )

            with allure.step("Side-channel check — no console errors/warnings across the flow"):
                assert not console_messages, (
                    f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
                )

        finally:
            with allure.step("Cleanup — delete the three seeded credentials"):
                for credential_id in seeded_ids:
                    try:
                        credential_api.delete_credential(credential_id)
                        logger.info("Deleted credential id=%s", credential_id)
                    except Exception as exc:  # noqa: BLE001 — best-effort cleanup, log and continue
                        logger.warning("Failed to delete credential id=%s: %s", credential_id, exc)

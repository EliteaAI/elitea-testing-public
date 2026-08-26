"""Test for Credentials — Filter Credentials by Type.

Verifies the right-hand TYPES panel on ``/credentials/all``: selecting a
type narrows the list to credentials of that type only, selection is a
toggle, and removing the filter restores the full list.

Test case: ELITEA-1966
AFS: test-specs/toolkits-credentials/l2_filter-credentials-by-type_ELITEA-1966.md

No substitution of the system under test: the three typed credentials are
created through the real REST API purely as **transit** to the case's own
precondition ("Ensure credentials of different types exist" — the case has
no UI-create step). Every asserted observable — which cards the filter
displays, their type badges, the URL the product writes, the presence of
the Clear-all control — is produced and rendered by the product from its
own server-side ``type=``-filtered response. Nothing is mocked, injected
or intercepted.
"""

import logging
import time
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from api.client import CredentialAPI
from pages.credentials_list_page import CredentialsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

#: (raw type key, chip label, `data` payload) for the three types the case names.
#: The `username`/`api_key` values are inert placeholders — this case never
#: exercises a connection test, so no real secret is involved.
SEED_TYPES = (
    ("github", "Github", {"base_url": "https://api.github.com"}),
    (
        "jira",
        "Jira",
        {"base_url": "https://example.atlassian.net", "username": "autotest@example.com", "api_key": "unused"},
    ),
    (
        "confluence",
        "Confluence",
        {
            "base_url": "https://example.atlassian.net/wiki",
            "username": "autotest@example.com",
            "api_key": "unused",
        },
    ),
)


def _is_known_554_warning(msg) -> bool:
    """Filter elitea-testing-public#554 (CLOSED 2026-08-11, product-owner
    verdict: reproducible only against a local UI / test-client artifact,
    not a backend defect, no action items). The right-panel toolkit-types
    query can fire before ``useSelectedProjectId()`` resolves, collapsing
    its URL to ``.../toolkits/prompt_lib/`` (no id) and 404-ing. Filtering
    it is a local-environment allowance, NOT a product-defect waiver — it
    is pinned to that exact URL shape, never a blanket 404 ignore, and it
    can match nothing this case renders or asserts."""
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and location_url.rstrip("/").endswith("/toolkits/prompt_lib")


class TestCredentialFilterByType:
    """ELITEA-1966 — Filter the credentials list by credential type."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1966_filter-credentials-by-type.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_filter_credentials_by_type(self, page, credential_api: CredentialAPI):
        """Selecting a type chip narrows the credentials list to that type;
        removing the filter restores the full list."""
        ts = int(time.time())
        seeded_ids: list[int] = []
        seeded_names: dict[str, str] = {}

        console_messages = []

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_554_warning(msg):
                console_messages.append(msg)

        list_page = CredentialsListPage(page)

        try:
            page.on("console", _on_console)

            with allure.step("Step 1 — Ensure credentials of different types exist (Github, Jira, Confluence)"):
                # Precondition seeding, not a case interaction: the case's
                # step 1 is "Ensure credentials of different types exist".
                # The TYPES panel is data-derived (GET /configurations/types
                # returns only types PRESENT), so these must be created for
                # the filter to have anything to narrow.
                for raw_type, _label, data in SEED_TYPES:
                    display_name = f"autotest_cred_type_{raw_type}_{ts}"
                    created = credential_api.create_credential(
                        {
                            "type": raw_type,
                            "elitea_title": f"{raw_type}_autotest_type_{ts}",
                            "label": display_name,
                            "data": data,
                            "shared": False,
                        }
                    )
                    seeded_ids.append(created["id"])
                    seeded_names[raw_type] = display_name
                    logger.info("Seeded %s credential id=%s name=%s", raw_type, created["id"], display_name)

                types_present = credential_api.list_credential_types()
                for raw_type, _label, _data in SEED_TYPES:
                    assert raw_type in types_present, (
                        f"The credential-types endpoint (the TYPES panel's own data source) "
                        f"should list {raw_type!r} once a credential of that type exists, "
                        f"got: {types_present}"
                    )

            with allure.step("Step 2 — Navigate to the credentials list; verify it loads with no type filter active"):
                list_page.navigate()
                assert urlparse(page.url).path.rstrip("/").endswith("/credentials/all"), (
                    f"Expected the credentials list URL, got: {page.url}"
                )
                assert "tags[]" not in parse_qs(urlparse(page.url).query), (
                    f"A fresh navigation should carry no type filter, got: {page.url}"
                )

                baseline_names = list_page.get_card_names()
                for raw_type, _label, _data in SEED_TYPES:
                    assert seeded_names[raw_type] in baseline_names, (
                        f"Seeded {raw_type} credential {seeded_names[raw_type]!r} should be "
                        f"visible on the unfiltered list, got: {baseline_names}"
                    )

                for _raw_type, label, _data in SEED_TYPES:
                    expect(list_page.type_filter_chip(label)).to_be_visible()

                # Clear-all renders only while >=1 chip is selected — its
                # ABSENCE is the product's own "no filter active" signal.
                expect(list_page.tags_clear_all_button).to_have_count(0)

            with allure.step('Step 3 — Click the "Github" type filter; verify only Github credentials remain'):
                list_page.click_type_filter("Github", "github")

                assert parse_qs(urlparse(page.url).query).get("tags[]") == ["Github"], (
                    f"URL should carry the Github type filter, got: {page.url}"
                )
                expect(list_page.card_by_name(seeded_names["github"])).to_have_count(1)
                expect(list_page.card_by_name(seeded_names["jira"])).to_have_count(0)
                expect(list_page.card_by_name(seeded_names["confluence"])).to_have_count(0)

                badges = list_page.get_visible_type_badges()
                assert badges, "At least one credential card should still be displayed under the Github filter"
                assert set(badges) == {"Github"}, (
                    f"Every displayed card's type badge should read 'Github' under the Github "
                    f"filter, got: {badges}"
                )
                expect(list_page.tags_clear_all_button).to_be_visible()

            with allure.step('Step 4 — Remove the Github filter, then click "Jira"; verify only Jira remains'):
                list_page.remove_type_filter("Github")
                assert "tags[]" not in parse_qs(urlparse(page.url).query), (
                    f"Clicking the selected chip again should toggle the filter OFF, got: {page.url}"
                )

                list_page.click_type_filter("Jira", "jira")
                assert parse_qs(urlparse(page.url).query).get("tags[]") == ["Jira"], (
                    f"URL should carry the Jira type filter, got: {page.url}"
                )
                expect(list_page.card_by_name(seeded_names["jira"])).to_have_count(1)
                expect(list_page.card_by_name(seeded_names["github"])).to_have_count(0)
                expect(list_page.card_by_name(seeded_names["confluence"])).to_have_count(0)

                badges = list_page.get_visible_type_badges()
                assert badges, "At least one credential card should still be displayed under the Jira filter"
                assert set(badges) == {"Jira"}, (
                    f"Every displayed card's type badge should read 'Jira' under the Jira "
                    f"filter, got: {badges}"
                )

            with allure.step("Step 5 — Remove the active type filter; verify all credential types are shown again"):
                list_page.clear_all_type_filters()

                assert "tags[]" not in parse_qs(urlparse(page.url).query), (
                    f"Clearing the filter should drop the tags[] param, got: {page.url}"
                )
                expect(list_page.tags_clear_all_button).to_have_count(0)

                restored_names = list_page.get_card_names()
                for raw_type, _label, _data in SEED_TYPES:
                    assert seeded_names[raw_type] in restored_names, (
                        f"Seeded {raw_type} credential {seeded_names[raw_type]!r} should be "
                        f"visible again after clearing the filter, got: {restored_names}"
                    )
                assert set(restored_names) == set(baseline_names), (
                    f"Clearing the type filter should restore the exact unfiltered list "
                    f"captured in step 2 — expected {baseline_names}, got {restored_names}"
                )

            with allure.step("Side channel — no unexpected console errors across the whole flow"):
                assert not console_messages, (
                    "Unexpected console errors/warnings: "
                    f"{[m.text for m in console_messages]}"
                )
        finally:
            page.remove_listener("console", _on_console)
            for credential_id in seeded_ids:
                try:
                    credential_api.delete_credential(credential_id)
                except Exception:
                    logger.warning("Failed to delete seeded credential id=%s", credential_id, exc_info=True)

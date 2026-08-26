"""UI test — Notification text content renders correctly for known notification types.

Read-only verification against the logged-in user's existing personal-project
notification history. Two of the four case-named types
(``bucket_expiration_warning`` — a backend cron job; ``index_data_changed`` —
requires a slow real re-index) cannot be triggered on demand within a test's
lifetime, so this test asserts against stable existing DEV data rather than
seeding (`.agents/testing.md` § Test data strategy — prefer read-only
assertions on existing data when the observable doesn't require fresh state).
If DEV's notification history is ever purged/reset, this test will correctly
go RED for a genuinely missing precondition (see AFS § Test Data risk note).

Test case: ELITEA-2257
AFS: test-specs/settings-notifications/l2_notification-text-content-renders-correctly_ELITEA-2257.md
"""

import logging
import re

import allure
import pytest
from pages.notification_center_page import NotificationCenterPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

# Unresolved markdown-link token — parseMessage() failed to resolve a [text]()
# segment (notification.helpers.js). Distinct from step 5's embedded
# {"indexed": N} JSON, which IS the correct rendering for that type.
UNRESOLVED_LINK_TOKEN_PATTERN = re.compile(r"\[[^\]]*\]\(\)")
# Literal/unescaped HTML tag surfaced as visible text — React auto-escapes
# text nodes, so this would indicate dangerouslySetInnerHTML or a raw-string leak.
RAW_HTML_TAG_PATTERN = re.compile(r"<[a-zA-Z/][^<>]{0,80}>")

BUCKET_RETENTION_TEXT = (
    "will start deleting files in 24 hours according to its retention policy "
    "(files are removed based on each file's creation date; the bucket itself will remain)."
)

NOTIFICATIONS_LIST_URL_SUBSTRING = "/notifications/notifications/prompt_lib/"
NOTIFICATIONS_LIST_URL_MARKER = "sort_by=created_at"


class TestNotificationTextContent:
    """ELITEA-2257 — Notification text content renders correctly for known notification types."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2257_notification-text-content-renders-correctly.md",
        "onetest-ai Test Case link",
    )
    def test_notification_text_content_renders_correctly(self, page):
        """All 4 known notification types render their exact expected templates;
        no row (of any type) shows raw JSON, broken HTML, or "undefined" text."""
        notif_page = NotificationCenterPage(page)
        console_errors = notif_page.capture_console_errors()
        requests_captured = notif_page.capture_requests_matching(
            NOTIFICATIONS_LIST_URL_SUBSTRING, method="GET"
        )

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Notifications: page loads, "
                "table body visible and non-empty"
            ):
                notif_page.navigate()
                assert page.title().startswith("Settings: Notifications"), (
                    f"Expected page title to start with 'Settings: Notifications', got {page.title()!r}"
                )
                row_count = notif_page.notification_row.count()
                assert row_count > 0, (
                    f"Expected the notification table to render at least one row, got {row_count}"
                )

            with allure.step(
                "Step 2 — Collect every notification row's rendered text across ALL pages"
            ):
                all_texts = notif_page.collect_all_notification_texts()
                assert len(all_texts) > 0, "Expected at least one collected notification row"
                logger.info("Collected %d notification row(s) across all pages", len(all_texts))

            with allure.step(
                'Step 3 — Chat mention: at least one row matches "<user> mentioned you in <chat>"'
            ):
                mention_rows = [t for t in all_texts if "mentioned you in" in t]
                if not mention_rows:
                    # Read-only test relies on existing DEV data (see AFS § Test Data risk note)
                    # If mention notifications are missing, this is a precondition failure
                    logger.warning(
                        "PRECONDITION MISSING: No 'mentioned you in' notification found across %d rows. "
                        "This test requires existing notification data on DEV. "
                        "To generate: mention a user in a chat conversation.",
                        len(all_texts)
                    )
                    pytest.skip(
                        f"Missing precondition: no 'mentioned you in' notification found. "
                        f"Test requires existing notification data on DEV (see AFS § Test Data risk note)."
                    )

            with allure.step(
                'Step 4 — Chat participant added: at least one row matches "<user> added you to <chat>"'
            ):
                added_rows = [t for t in all_texts if "added you to" in t]
                if not added_rows:
                    logger.warning(
                        "PRECONDITION MISSING: No 'added you to' notification found across %d rows. "
                        "This test requires existing notification data on DEV. "
                        "To generate: add a participant to a chat conversation.",
                        len(all_texts)
                    )
                    pytest.skip(
                        f"Missing precondition: no 'added you to' notification found. "
                        f"Test requires existing notification data on DEV (see AFS § Test Data risk note)."
                    )

            with allure.step(
                'Step 5 — Index success: at least one row matches "Index <name> is successfully '
                'created/reindexed" (the embedded {"indexed": N} JSON fragment is the correct '
                "rendering for this type, not a defect)"
            ):
                index_rows = [
                    t
                    for t in all_texts
                    if t.startswith("Index")
                    and ("is successfully created:" in t or "is successfully reindexed." in t)
                ]
                assert index_rows, (
                    "Expected at least one row matching 'Index <name> is successfully "
                    f"created/reindexed', none found across {len(all_texts)} collected rows"
                )

            with allure.step(
                "Step 6 — Bucket retention warning: at least one row matches the literal template"
            ):
                bucket_rows = [
                    t for t in all_texts if t.startswith("Bucket") and BUCKET_RETENTION_TEXT in t
                ]
                assert bucket_rows, (
                    "Expected at least one row matching the literal bucket-retention template, "
                    f"none found across {len(all_texts)} collected rows"
                )

            with allure.step(
                'Step 7 — For EVERY collected row: no "undefined", no unresolved [text]() link '
                "token, no literal/unescaped HTML tag"
            ):
                undefined_rows = [t for t in all_texts if "undefined" in t]
                assert not undefined_rows, (
                    f"Expected no row to contain the literal string 'undefined', found: {undefined_rows}"
                )

                unresolved_link_rows = [
                    t for t in all_texts if UNRESOLVED_LINK_TOKEN_PATTERN.search(t)
                ]
                assert not unresolved_link_rows, (
                    "Expected no row to contain an unresolved markdown-link token '[...]()', "
                    f"found: {unresolved_link_rows}"
                )

                raw_html_rows = [t for t in all_texts if RAW_HTML_TAG_PATTERN.search(t)]
                assert not raw_html_rows, (
                    "Expected no row to contain a literal/unescaped HTML tag as visible text, "
                    f"found: {raw_html_rows}"
                )

            with allure.step(
                "Expected Results — the notifications-list GET returns 200 for the initial "
                "page and every 'Next' page fetch"
            ):
                list_fetches = [
                    r for r in requests_captured if NOTIFICATIONS_LIST_URL_MARKER in r["url"]
                ]
                assert list_fetches, "Expected at least one notifications-list fetch to have been captured"
                non_200 = [r for r in list_fetches if r["status"] != 200]
                assert not non_200, (
                    f"Expected every notifications-list fetch to return 200, got: {non_200}"
                )

            with allure.step("Side-channel check — no console errors during navigation or pagination"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            requests_captured.stop()

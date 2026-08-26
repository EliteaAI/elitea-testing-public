"""UI test — Mark selected notifications as read and unread using checkboxes.

Read-only-by-construction: the test discovers two unread notifications from
the logged-in user's real notification history dynamically (via the list
fetch response) rather than seeding or hardcoding notification ids, and its
two bulk-mark actions are self-reverting — the test marks the same two
notifications read then unread again, so the account ends the run in the
same state it started in (`.agents/testing.md` § Test data strategy).

Test case: ELITEA-2259
AFS: test-specs/settings-notifications/l2_mark-selected-notifications-read-unread_ELITEA-2259.md

Case-text clarification (not a defect, filed as
EliteaAI/elitea-testing-public#1166): the case's steps 3/8 refer to separate
"Mark as read"/"Mark as unread" buttons; the live product has ONE toolbar
toggle button whose accessible name flips depending on the current
selection's read state — asserted here via that live accessible name, not
the case's literal (and, for this surface, inapplicable) button text.
"""

import logging

import allure
import pytest
from pages.notification_center_page import NotificationCenterPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_MARK_READ_TOAST = "Notifications marked as read"
EXPECTED_MARK_UNREAD_TOAST = "Notifications marked as unread"
MARK_AS_READ_LABEL = "Mark selected as read"
MARK_AS_UNREAD_LABEL = "Mark selected as unread"
TOAST_TIMEOUT = 10_000
MIN_UNREAD_NEEDED = 2


def _rows_by_id(rows: list[dict]) -> dict:
    """Map a list of ``{"id": ..., "is_seen": ..., ...}`` rows to ``{id: is_seen}``."""
    return {row["id"]: row["is_seen"] for row in rows}


def _assert_other_rows_unchanged(baseline: dict, refetched_rows: list[dict], target_ids: set) -> None:
    """Assert every row NOT in *target_ids* kept the same ``is_seen`` value
    it had in *baseline* (no collateral mutation from the bulk action)."""
    refetched = _rows_by_id(refetched_rows)
    for row_id, was_seen in baseline.items():
        if row_id in target_ids:
            continue
        now_seen = refetched.get(row_id)
        assert now_seen == was_seen, (
            f"Row {row_id} changed unexpectedly: was is_seen={was_seen}, now is_seen={now_seen}"
        )


class TestNotificationMarkReadUnread:
    """ELITEA-2259 — Mark selected notifications as read and unread using checkboxes."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2259_mark-selected-notifications-read-unread.md",
        "onetest-ai Test Case link",
    )
    def test_mark_selected_notifications_read_and_unread(self, page):
        """Two dynamically-discovered unread notifications toggle
        unread -> read -> unread again via the bulk checkbox + toolbar
        toggle button, each transition confirmed both immediately (via the
        post-PUT refetch) and after a full page reload (persistence), with
        no collateral change to any other notification."""
        notif_page = NotificationCenterPage(page)
        console_errors = notif_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Notifications: page loads, "
                "table body visible and non-empty"
            ):
                initial_rows = notif_page.navigate_and_get_rows()
                assert page.title().startswith("Settings: Notifications"), (
                    f"Expected page title to start with 'Settings: Notifications', got {page.title()!r}"
                )
                row_count = notif_page.notification_row.count()
                assert row_count > 0, (
                    f"Expected the notification table to render at least one row, got {row_count}"
                )

            with allure.step(
                "Step 2 — From the list-fetch response, select the first 2 unread "
                "(is_seen=false) rows and record the current page's full baseline"
            ):
                baseline = _rows_by_id(initial_rows)
                unread_ids = [row["id"] for row in initial_rows if row["is_seen"] is False]
                assert len(unread_ids) >= MIN_UNREAD_NEEDED, (
                    f"Insufficient unread notifications: found {len(unread_ids)}, need at least "
                    f"{MIN_UNREAD_NEEDED}. This account's notification history may have been reset."
                )
                target_ids = unread_ids[:MIN_UNREAD_NEEDED]
                target_id_set = set(target_ids)
                logger.info("Selected target unread notification ids: %s", target_ids)

            with allure.step(
                "Step 3 — Check the checkbox on the two selected (unread) notifications: "
                "both become checked, toolbar toggle button enables with label "
                "'Mark selected as read'"
            ):
                for notification_id in target_ids:
                    notif_page.check_notification_checkbox(notification_id)
                for notification_id in target_ids:
                    assert notif_page.is_notification_checkbox_checked(notification_id), (
                        f"Expected checkbox for notification {notification_id} to be checked"
                    )
                assert notif_page.is_mark_toggle_enabled(), (
                    "Expected the mark-toggle button to be enabled once two rows are selected"
                )
                assert notif_page.get_mark_toggle_label() == MARK_AS_READ_LABEL, (
                    f"Expected mark-toggle label {MARK_AS_READ_LABEL!r} while unread rows are "
                    f"selected, got {notif_page.get_mark_toggle_label()!r}"
                )

            with allure.step(
                "Step 4 — Click the mark-toggle button ('Mark selected as read'): PUT "
                "resolves 200, success toast appears, selection clears and the button "
                "reverts to disabled"
            ):
                after_mark_read_rows = notif_page.click_mark_toggle()
                expect(notif_page.success_toast_message).to_have_text(
                    EXPECTED_MARK_READ_TOAST, timeout=TOAST_TIMEOUT
                )
                for notification_id in target_ids:
                    assert not notif_page.is_notification_checkbox_checked(notification_id), (
                        f"Expected checkbox for notification {notification_id} to be unchecked "
                        "after a successful bulk mark-as-read"
                    )
                assert not notif_page.is_mark_toggle_enabled(), (
                    "Expected the mark-toggle button to revert to disabled after selection clears"
                )

            with allure.step(
                "Step 5 — From the refetch response: both selected notifications are now "
                "is_seen=true; every other row on the page is unchanged"
            ):
                after_mark_read = _rows_by_id(after_mark_read_rows)
                for notification_id in target_ids:
                    assert after_mark_read.get(notification_id) is True, (
                        f"Expected notification {notification_id} to be is_seen=true after "
                        f"mark-as-read, got {after_mark_read.get(notification_id)!r}"
                    )
                _assert_other_rows_unchanged(baseline, after_mark_read_rows, target_id_set)

            with allure.step(
                "Step 6 — Reload the page: both notifications remain is_seen=true (persisted)"
            ):
                after_reload_1_rows = notif_page.reload_and_get_rows()
                after_reload_1 = _rows_by_id(after_reload_1_rows)
                for notification_id in target_ids:
                    assert after_reload_1.get(notification_id) is True, (
                        f"Expected notification {notification_id} to still be is_seen=true "
                        f"after reload, got {after_reload_1.get(notification_id)!r}"
                    )

            with allure.step(
                "Step 7 — Check the checkbox on the SAME two notifications (now read) again: "
                "both become checked, toolbar toggle button's label is now "
                "'Mark selected as unread'"
            ):
                for notification_id in target_ids:
                    notif_page.check_notification_checkbox(notification_id)
                for notification_id in target_ids:
                    assert notif_page.is_notification_checkbox_checked(notification_id), (
                        f"Expected checkbox for notification {notification_id} to be checked"
                    )
                assert notif_page.is_mark_toggle_enabled(), (
                    "Expected the mark-toggle button to be enabled once two rows are selected"
                )
                assert notif_page.get_mark_toggle_label() == MARK_AS_UNREAD_LABEL, (
                    f"Expected mark-toggle label {MARK_AS_UNREAD_LABEL!r} while read rows are "
                    f"selected, got {notif_page.get_mark_toggle_label()!r}"
                )

            with allure.step(
                "Step 8 — Click the mark-toggle button ('Mark selected as unread'): PUT "
                "resolves 200, success toast appears, selection clears and the button "
                "reverts to disabled"
            ):
                after_mark_unread_rows = notif_page.click_mark_toggle()
                expect(notif_page.success_toast_message).to_have_text(
                    EXPECTED_MARK_UNREAD_TOAST, timeout=TOAST_TIMEOUT
                )
                for notification_id in target_ids:
                    assert not notif_page.is_notification_checkbox_checked(notification_id), (
                        f"Expected checkbox for notification {notification_id} to be unchecked "
                        "after a successful bulk mark-as-unread"
                    )
                assert not notif_page.is_mark_toggle_enabled(), (
                    "Expected the mark-toggle button to revert to disabled after selection clears"
                )

            with allure.step(
                "Step 9 — From the refetch response: both selected notifications are now "
                "is_seen=false again; every other row on the page is unchanged"
            ):
                after_mark_unread = _rows_by_id(after_mark_unread_rows)
                for notification_id in target_ids:
                    assert after_mark_unread.get(notification_id) is False, (
                        f"Expected notification {notification_id} to be is_seen=false after "
                        f"mark-as-unread, got {after_mark_unread.get(notification_id)!r}"
                    )
                _assert_other_rows_unchanged(baseline, after_mark_unread_rows, target_id_set)

            with allure.step(
                "Step 10 — Reload the page again: both notifications remain is_seen=false "
                "(Expected Final State — matches the case's own stated end state)"
            ):
                after_reload_2_rows = notif_page.reload_and_get_rows()
                after_reload_2 = _rows_by_id(after_reload_2_rows)
                for notification_id in target_ids:
                    assert after_reload_2.get(notification_id) is False, (
                        f"Expected notification {notification_id} to still be is_seen=false "
                        f"after the final reload, got {after_reload_2.get(notification_id)!r}"
                    )

            with allure.step("Side-channel check — no console errors during the whole flow"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()

"""UI test — Unread notifications are visually distinct from read notifications.

The read/unread distinction on this surface is a computed COLOUR, not an
attribute: ``NotificationTable.jsx`` renders the date cell with
``color={row.is_seen ? 'text.primary' : 'text.secondary'}`` and
``NotificationListItemMessage.jsx`` does the same for the message text. This
test reads those colours off the rendered elements (the browser computes them
from the product's own theme) and asserts the DIFFERENCE — never a literal rgb
string, because the values are theme tokens that a palette or light/dark change
would legitimately move while the contract still holds.

Test case: ELITEA-2258
AFS: test-specs/settings-notifications/l2_unread-vs-read-visual-distinction_ELITEA-2258.md

Substitution declaration
------------------------
ZERO substitution. No route mock, no fabricated response, no injected state, no
API seeding, no monkeypatching. The one ``.evaluate()`` in the flow lives in
``NotificationCenterPage.get_row_message_color`` / ``get_row_date_color`` and is
a ``window.getComputedStyle(el).color`` READ of a value the PRODUCT computed —
the only way to observe a computed colour, and the same shape
``agent_form_page.py`` already uses (`.agents/testing.md` § Fidelity policy).
Marking the subject notification read is transit performed through the
product's own toolbar control, firing the product's own ``PUT``; the case's own
observable (the colour difference) is still produced entirely by the product.

Case-text drift — this test asserts the LIVE contract
-----------------------------------------------------
The case's step 4 says "Click the notification row or open the linked entity"
and its step 6 expects that click to have marked the notification read. Live,
clicking a row does nothing: ``GridTableRow`` has no row-level ``onClick``
beyond checkbox selection, and the message ``<Link>`` is a plain
``target="_blank"`` anchor with no mark-seen handler. The only in-product
read/unread transitions in the table context are the toolbar toggle and the
sidebar popover's per-row hover button. Filed as clarification
EliteaAI/elitea-testing-public#1784; per the reverse-masking guard this test
asserts the live contract (the click issues no mark ``PUT`` and changes
nothing) and produces the read state through the toolbar toggle instead.

Test data
---------
Self-reverting: the test mutates exactly one existing notification's read state
(unread -> read) and restores it in a ``finally`` block, so the account ends the
run as it started. No notification id, total or colour is ever hardcoded — the
subjects are discovered from the product's own list response, which is real,
growing DEV history shared with every other notification spec
(`.agents/testing.md` § ``#1082`` shared-test-user class).

Markers:
    - ui: requires browser
    - admin: notification-centre suite (matches its sibling specs)
    - p2: priority (AFS metadata l2 — case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from pages.notification_center_page import NotificationCenterPage
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

MARK_AS_READ_LABEL = "Mark selected as read"
MIN_UNREAD_NEEDED = 2


class TestNotificationUnreadReadVisualDistinction:
    """ELITEA-2258 — Unread notifications are visually distinct from read ones."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2258_unread-vs-read-visual-distinction.md",
        "onetest-ai Test Case link",
    )
    def test_unread_notifications_are_visually_distinct_from_read(self, page):
        """Two dynamically-discovered unread notifications render identical
        colours; marking one of them read through the product's toolbar toggle
        changes that row's message and date colours, leaves its still-unread
        sibling untouched, and a plain row click changes neither state nor
        styling."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page)
        subject_id = None
        cleanup_error = None

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> Notifications: page loads, table "
                "body visible and non-empty"
            ):
                rows = notif_page.navigate_and_get_rows()
                assert page.title().startswith("Settings: Notifications"), (
                    f"Expected page title to start with 'Settings: Notifications', got {page.title()!r}"
                )
                assert len(rows) > 0, (
                    "Expected the notification list fetch to return at least one row, got none"
                )
                rendered_count = notif_page.notification_row.count()
                assert rendered_count > 0, (
                    f"Expected the notification table to render at least one row, got {rendered_count}"
                )

            with allure.step(
                "Step 2 — Identify unread notifications from the product's own list "
                "response: pick a subject and an untouched control"
            ):
                unread_ids = [row["id"] for row in rows if row["is_seen"] is False]
                assert len(unread_ids) >= MIN_UNREAD_NEEDED, (
                    f"Insufficient unread notifications on page 1: found {len(unread_ids)}, need at "
                    f"least {MIN_UNREAD_NEEDED} (one subject + one untouched control). This "
                    "account's notification history may have been reset or fully read."
                )
                subject_id, control_id = unread_ids[0], unread_ids[1]
                logger.info("Subject notification %s, control notification %s", subject_id, control_id)

            with allure.step(
                "Step 3 — Capture the UNREAD baseline colours of both rows: two unread "
                "rows are styled alike"
            ):
                subject_msg_unread = notif_page.get_row_message_color(subject_id)
                subject_date_unread = notif_page.get_row_date_color(subject_id)
                control_msg_unread = notif_page.get_row_message_color(control_id)
                control_date_unread = notif_page.get_row_date_color(control_id)
                logger.info(
                    "Unread baseline — subject msg=%s date=%s / control msg=%s date=%s",
                    subject_msg_unread,
                    subject_date_unread,
                    control_msg_unread,
                    control_date_unread,
                )
                assert subject_msg_unread == control_msg_unread, (
                    "Two unread notifications rendered different message colours: subject "
                    f"{subject_msg_unread!r} vs control {control_msg_unread!r}"
                )
                assert subject_date_unread == control_date_unread, (
                    "Two unread notifications rendered different date colours: subject "
                    f"{subject_date_unread!r} vs control {control_date_unread!r}"
                )

            with allure.step(
                "Step 4 — Click the notification row: LIVE contract — the click does NOT "
                "mark it read (no bulk-mark PUT, colours unchanged, is_seen still false)"
            ):
                no_mutation = notif_page.click_row_expecting_no_mark_mutation(subject_id)
                assert no_mutation, (
                    "Clicking the notification row issued a bulk-mark PUT. The live product "
                    "has no row-level mark-seen handler (clarification "
                    "EliteaAI/elitea-testing-public#1784); if the product gained one, this "
                    "test and the case text both need updating."
                )
                assert notif_page.get_row_message_color(subject_id) == subject_msg_unread, (
                    "The clicked row's message colour changed even though no mark-seen request fired"
                )
                assert notif_page.get_row_date_color(subject_id) == subject_date_unread, (
                    "The clicked row's date colour changed even though no mark-seen request fired"
                )
                after_click = {row["id"]: row["is_seen"] for row in notif_page.reload_and_get_rows()}
                assert after_click.get(subject_id) is False, (
                    f"Expected notification {subject_id} to still be unread after a row click, "
                    f"got is_seen={after_click.get(subject_id)!r}"
                )

            with allure.step(
                "Step 5 — Produce the read state through the product's real control: "
                "select the subject row and click the toolbar 'Mark selected as read' toggle"
            ):
                notif_page.check_notification_checkbox(subject_id)
                toggle_label = notif_page.get_mark_toggle_label()
                assert toggle_label == MARK_AS_READ_LABEL, (
                    f"Expected the toolbar toggle to read {MARK_AS_READ_LABEL!r} while an unread "
                    f"row is selected (the product's own confirmation that it is unread), got "
                    f"{toggle_label!r}"
                )
                after_mark = {row["id"]: row["is_seen"] for row in notif_page.click_mark_toggle()}
                assert after_mark.get(subject_id) is True, (
                    f"Expected notification {subject_id} to be is_seen=true after mark-as-read, "
                    f"got {after_mark.get(subject_id)!r}"
                )
                assert after_mark.get(control_id) is False, (
                    f"Expected the control notification {control_id} to stay unread, got "
                    f"is_seen={after_mark.get(control_id)!r}"
                )

            with allure.step(
                "Step 6 — The previously-unread notification now renders in read state: its "
                "own styling changed, it differs from a live unread sibling, and that "
                "sibling is untouched"
            ):
                notif_page.wait_for_row_colors_to_change(
                    subject_id, subject_msg_unread, subject_date_unread
                )
                subject_msg_read = notif_page.get_row_message_color(subject_id)
                subject_date_read = notif_page.get_row_date_color(subject_id)
                control_msg_after = notif_page.get_row_message_color(control_id)
                control_date_after = notif_page.get_row_date_color(control_id)
                logger.info(
                    "Read state — subject msg=%s date=%s / control msg=%s date=%s",
                    subject_msg_read,
                    subject_date_read,
                    control_msg_after,
                    control_date_after,
                )

                assert subject_msg_read != subject_msg_unread, (
                    "The subject row's message colour did not change when it became read: "
                    f"still {subject_msg_read!r}"
                )
                assert subject_date_read != subject_date_unread, (
                    "The subject row's date colour did not change when it became read: "
                    f"still {subject_date_read!r}"
                )

                assert subject_msg_read != control_msg_unread, (
                    "A read notification's message colour is indistinguishable from an unread "
                    f"one rendered in the same table: both {subject_msg_read!r}"
                )
                assert subject_date_read != control_date_unread, (
                    "A read notification's date colour is indistinguishable from an unread one "
                    f"rendered in the same table: both {subject_date_read!r}"
                )

                assert control_msg_after == control_msg_unread, (
                    "The untouched unread row's message colour changed too — the distinction is "
                    f"a table-wide restyle, not per-row: {control_msg_unread!r} -> {control_msg_after!r}"
                )
                assert control_date_after == control_date_unread, (
                    "The untouched unread row's date colour changed too — the distinction is a "
                    f"table-wide restyle, not per-row: {control_date_unread!r} -> {control_date_after!r}"
                )

            with allure.step("Step 7 — No unexpected console errors across the whole flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            with allure.step(
                "Cleanup — restore the subject notification to its original unread state"
            ):
                try:
                    notif_page.restore_notification_unread(subject_id)
                except Exception as exc:  # noqa: BLE001 - reported below, never masks the test's own failure
                    cleanup_error = exc
                    logger.exception("Cleanup failed to restore notification %s to unread", subject_id)

        assert cleanup_error is None, (
            f"Test assertions passed but cleanup failed to restore notification {subject_id} "
            f"to unread — the shared account is left dirty: {cleanup_error!r}"
        )

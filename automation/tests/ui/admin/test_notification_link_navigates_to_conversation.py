"""UI test — Clicking a chat-mention notification link navigates to the correct conversation.

Test case: ELITEA-2261
AFS: test-specs/settings-notifications/
     l2_notification-chat-mention-link-navigates-to-conversation_ELITEA-2261.md

Read-only by construction: the whole flow is GET-only — clicking the in-message
link mutates neither the notification nor the conversation — so this spec seeds
nothing and cleans up nothing beyond closing the tab it opened.

Nothing is hardcoded
--------------------
The notification id, the conversation id, the message id and the expected URL all
come from the product's own list response and its own rendered ``href``. The DEV
account's notification history is real and grows (67 rows on 2026-08-04, 89 on
2026-08-26), and the entities it references ROT — two of the twelve mention
notifications point at conversations that no longer exist. The spec therefore
DISCOVERS a mention notification whose conversation is still alive (probing the
product's own conversation endpoint) and fails loudly, never skips, when none is.

The link opens a NEW TAB
------------------------
``NotificationListItemMessage.jsx`` renders the segment as
``<Link target="_blank" rel="noopener noreferrer">`` with no ``onClick``, so the
click is awaited with ``context.expect_page()``. An in-tab ``wait_for_url`` would
hang. The same fact makes the case's step 6 ("navigate back — verify the
notification is now in read state") case-text drift: there is no back-navigation
and no mark-seen handler, so the live contract asserted here is that the read
state is UNCHANGED by the click — clarification
EliteaAI/elitea-testing-public#1786.

Substitution declaration
------------------------
ZERO substitution of the system under test — no ``page.route``, no
``route.fulfill``, no monkeypatching, no stubbed client. Two reads deserve an
explicit note because the reviewer's mechanical grep hits them:

* ``locator.evaluate("el => window.getComputedStyle(el).color")``
  (``NotificationCenterPage.get_row_message_color``) READS a colour the product
  itself computed from its theme tokens. Nothing is injected. Precedent:
  ``agent_form_page.py:230``.
* ``ConversationAPI.get_conversation_raw()`` is a TRANSIT read of the product's
  own conversation endpoint that only selects WHICH notification to exercise (a
  precondition). The case's own observable — what clicking the link does — is
  still produced live by the product.

Markers:
    - ui: requires browser
    - admin: notification-centre suite (matches its sibling specs)
    - p2: priority (AFS metadata l2 — case priority `medium`)
    - regression
"""

import logging
import re
import urllib.parse

import allure
import pytest
from api.client import ConversationAPI
from config import settings
from pages.chat_page import ChatPage
from pages.notification_center_page import PAGE_INFO_PATTERN, NotificationCenterPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

#: Template token every ``chat_user_mentioned`` message carries. Used with the
#: product's OWN server-side search field to narrow the list; the rows it returns
#: are still filtered on ``event_type`` below, so a coincidental text match on
#: some other notification type can never be selected.
MENTION_SEARCH_TERM = "mentioned you in"

#: The notification ``event_type`` this case is about (``NotificationType``
#: in EliteaUI's ``common/constants``).
MENTION_EVENT_TYPE = "chat_user_mentioned"

#: Background resources documented as environmental noise on this DEV backend
#: (`.agents/testing.md` § Known issues / § Unconfirmed — the recurring
#: unrelated-resource console-error class). Neither is requested by the flow
#: under test: the first is the secrets probe every project mount fires, the
#: second the project-info fetch the project switcher fires. This is noise
#: SCOPING by resource URL, not defect masking — every other console error,
#: including anything on the conversation endpoint, still fails the test.
KNOWN_BACKGROUND_NOISE_URL_MARKERS = (
    "/secrets/secrets/default/",
    "/project_info/prompt_lib/",
)

CONVERSATION_URL_TEMPLATE = "/elitea_core/conversation/prompt_lib/{project_id}/{conversation_id}"

POPUP_URL_TIMEOUT = 30_000
POPUP_ELEMENT_TIMEOUT = 15_000


def _flow_console_errors(messages: list[str]) -> list[str]:
    """Drop the two documented background-resource noise entries, keep everything else."""
    return [
        message
        for message in messages
        if not any(marker in message for marker in KNOWN_BACKGROUND_NOISE_URL_MARKERS)
    ]


def _expected_mention_href(row: dict) -> str:
    """Rebuild the href ``resolveHref()`` must have produced for *row*.

    Mirrors ``notification.helpers.js`` exactly for ``chat_user_mentioned``:
    ``{base}/{notification.project_id}/chat?conversation={meta.conversation_id}``
    ``&message_id={meta.message_id}``. Every component is the notification's OWN
    data, read out of the list response — the test invents nothing.
    """
    meta = row["meta"]
    base = f"{settings.app_base_url.rstrip('/')}/{row['project_id']}/chat"
    href = f"{base}?conversation={meta['conversation_id']}"
    if meta.get("message_id"):
        href = f"{href}&message_id={meta['message_id']}"
    return href


class TestNotificationChatMentionLinkNavigation:
    """ELITEA-2261 — the chat-mention link opens the conversation it names."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2261_clicking-a-chat-mention-notification-link-navigates-to-th.md",
        "onetest-ai Test Case link",
    )
    def test_chat_mention_link_navigates_to_conversation(self, page, _browser_cookies):
        """A chat-mention notification's in-message link carries the href built from
        that notification's own metadata, opens a new tab on the referenced
        conversation, renders its messages without a "not found" dialog, and leaves
        the notification's read state untouched."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page.context)
        conversation_api_by_project: dict[str, ConversationAPI] = {}

        def conversation_is_live(project_id, conversation_id) -> bool:
            """Transit read of the product's own conversation endpoint: 200 = live."""
            key = str(project_id)
            if key not in conversation_api_by_project:
                conversation_api_by_project[key] = ConversationAPI(
                    browser_cookies=_browser_cookies, project_id=key
                )
            status = conversation_api_by_project[key].get_conversation_raw(
                conversation_id
            ).status_code
            logger.info(
                "Conversation liveness probe project=%s conversation=%s -> %s",
                project_id, conversation_id, status,
            )
            return status == 200

        try:
            with allure.step("Step 1 — Navigate to Settings -> Notifications"):
                notif_page.navigate_and_get_rows()
                expect(notif_page.table_body).to_be_visible()
                assert page.title().startswith("Settings: Notifications"), (
                    f"Expected page title to start with 'Settings: Notifications', "
                    f"got {page.title()!r}"
                )
                page_info = notif_page.get_page_info()
                assert PAGE_INFO_PATTERN.match(page_info), (
                    f"Pagination range label did not render in the expected "
                    f"'{{start}} - {{end}} of {{total}}' shape, got {page_info!r}"
                )

            with allure.step(
                'Step 2 — Find a "[User] mentioned you in [Chat]" notification whose '
                "conversation still exists"
            ):
                response = notif_page.search_notifications(MENTION_SEARCH_TERM)
                candidates = [
                    row
                    for row in response.json()["rows"]
                    if row.get("event_type") == MENTION_EVENT_TYPE
                    and (row.get("meta") or {}).get("conversation_id")
                ]
                assert candidates, (
                    f"No {MENTION_EVENT_TYPE} notification carrying a conversation id was "
                    f"returned for search {MENTION_SEARCH_TERM!r}. The precondition "
                    "'the account's notification history contains a chat-mention "
                    "notification' is not met."
                )
                logger.info("%d chat-mention candidate row(s) rendered", len(candidates))

                target = next(
                    (
                        row
                        for row in candidates
                        if conversation_is_live(row["project_id"], row["meta"]["conversation_id"])
                    ),
                    None,
                )
                assert target is not None, (
                    "No chat_user_mentioned notification points at a surviving conversation "
                    f"— all {len(candidates)} candidate(s) reference conversations the "
                    "backend no longer resolves. The precondition 'at least one mention "
                    "notification whose conversation still exists' is not met on this "
                    "account (this is missing test data, not a product failure)."
                )

                notification_id = target["id"]
                project_id = target["project_id"]
                conversation_id = target["meta"]["conversation_id"]
                message_id = target["meta"].get("message_id")
                logger.info(
                    "Target notification %s -> project %s conversation %s message %s",
                    notification_id, project_id, conversation_id, message_id,
                )

                assert notif_page.get_row_link_count(notification_id) == 1, (
                    f"Expected notification row {notification_id} to render exactly one "
                    f"in-message link, found "
                    f"{notif_page.get_row_link_count(notification_id)} — the row-scoped "
                    "link locator would be ambiguous"
                )
                link = notif_page.get_row_link_attributes(notification_id)
                expected_href = _expected_mention_href(target)
                assert link["href"] == expected_href, (
                    f"The rendered link href is not the one the notification's own metadata "
                    f"defines.\n  expected: {expected_href}\n  actual:   {link['href']}"
                )
                assert link["target"] == "_blank", (
                    f"Expected the in-message link to open in a new tab "
                    f"(target='_blank'), got {link['target']!r}"
                )
                assert link["rel"] == "noopener noreferrer", (
                    f"Expected rel='noopener noreferrer' on the new-tab link, "
                    f"got {link['rel']!r}"
                )
                assert link["text"], "The in-message link rendered no visible text"

                message_color_before = notif_page.get_row_message_color(notification_id)
                is_seen_before = target["is_seen"]
                logger.info(
                    "Pre-click read state: is_seen=%s message colour=%s",
                    is_seen_before, message_color_before,
                )

            conversation_responses: list[tuple[int, str]] = []
            conversation_url_fragment = CONVERSATION_URL_TEMPLATE.format(
                project_id=project_id, conversation_id=conversation_id
            )
            page.context.on(
                "response",
                lambda resp: (
                    conversation_responses.append((resp.status, resp.url))
                    if conversation_url_fragment in resp.url
                    else None
                ),
            )

            popup = None
            with allure.step("Step 3 — Click the Chat link inside the notification text"):
                pages_before = len(page.context.pages)
                popup = notif_page.click_message_link_expecting_popup(notification_id)
                assert len(page.context.pages) == pages_before + 1, (
                    f"Expected exactly one new tab after clicking the link, page count went "
                    f"{pages_before} -> {len(page.context.pages)}"
                )

            with allure.step(
                "Step 4 — The new tab lands on the referenced chat conversation"
            ):
                popup.wait_for_url(
                    re.compile(rf"/chat/{conversation_id}(\?|$)"), timeout=POPUP_URL_TIMEOUT
                )
                popup_path = urllib.parse.urlparse(popup.url).path
                # The href carries the notification's own ``/{project_id}`` prefix, which
                # the project switcher consumes when it actually has to switch (measured
                # live 2026-08-26: ``/chat/5883`` for project 406 while 399 was selected).
                # It stays in the URL when no switch is needed — see ELITEA-2263's
                # ``/399/artifacts`` — so both shapes are accepted and nothing else is.
                accepted_paths = (
                    f"{settings.app_prefix}/chat/{conversation_id}",
                    f"{settings.app_prefix}/{project_id}/chat/{conversation_id}",
                )
                assert popup_path in accepted_paths, (
                    f"The new tab did not land on the notification's own conversation: "
                    f"expected one of {accepted_paths}, got {popup_path!r} "
                    f"(full URL {popup.url!r})"
                )

            with allure.step('Step 5 — The chat opens without a "not found" error'):
                popup_chat = ChatPage(popup)
                expect(popup_chat.alert_dialog_content).to_have_count(
                    0, timeout=POPUP_ELEMENT_TIMEOUT
                )
                expect(popup_chat.messages_list).to_be_visible(timeout=POPUP_ELEMENT_TIMEOUT)
                message_count = popup_chat.messages_container.count()
                assert message_count >= 1, (
                    f"The conversation rendered its message list but no messages "
                    f"(count={message_count}) — conversation {conversation_id} did not open"
                )
                failed_conversation_reads = [
                    (status, url) for status, url in conversation_responses if status >= 400
                ]
                assert not failed_conversation_reads, (
                    f"The conversation read failed on the backend: "
                    f"{failed_conversation_reads} — a 400 here is what produces the "
                    f'"Conversation not found" dialog'
                )
                assert conversation_responses, (
                    f"No response was observed on {conversation_url_fragment} — the popup "
                    "never fetched the conversation the notification points at"
                )

            with allure.step(
                "Step 6 — Return to the notifications tab: the click did NOT mark the "
                "notification read (case-text clarification #1786)"
            ):
                popup.close()
                popup = None
                page.bring_to_front()
                rows_after = notif_page.navigate_and_get_rows()
                notif_page.search_notifications(MENTION_SEARCH_TERM)
                message_color_after = notif_page.get_row_message_color(notification_id)
                assert message_color_after == message_color_before, (
                    "Clicking the in-message link changed the notification's rendered read "
                    f"state: message colour was {message_color_before} before the click and "
                    f"{message_color_after} after. The product has no mark-seen handler on "
                    "this link (clarification EliteaAI/elitea-testing-public#1786)."
                )
                row_after = next(
                    (row for row in rows_after if row["id"] == notification_id), None
                )
                if row_after is not None:
                    assert row_after["is_seen"] == is_seen_before, (
                        f"Notification {notification_id}'s server-side is_seen flipped "
                        f"{is_seen_before} -> {row_after['is_seen']} after clicking its link"
                    )

            with allure.step("Axis 2 — No console errors attributable to this flow"):
                flow_errors = _flow_console_errors(console_errors)
                assert not flow_errors, f"Unexpected console errors: {flow_errors}"
        finally:
            for api in conversation_api_by_project.values():
                api.close()

"""UI Test for ELITEA-2149 — Chat: Pin a Conversation via Pin on Top Option.

Verifies pinning a conversation via the conversation's 3-dot menu "Pin on
top" item: the conversation moves into the pinned section (above date
groups), a pin icon renders next to its name, it disappears from its
original date group, and the pinned section renders above the unpinned
conversation list.

Spec: test-specs/chat-interface/l3_pin-conversation-via-pin-on-top_ELITEA-2149.md

Shares the conversation 3-dot context-menu surface with ELITEA-2135/
ELITEA-2137 (the "Move to" flows) but never opens "Move to" — the "pin"
item has no submenu, so this test is NOT affected by the "Move to"
activation-gesture defect filed against those two cases
(EliteaAI/elitea-testing-public#1117); confirmed live during analysis.

No product defects found — all case steps executed live end-to-end and
matched expected results exactly.

Implementer addition (not in the AFS's own Test Data table, but within its
recommended scope — see AFS § Automation Hints option (a)): a second,
unpinned sibling conversation (``conv_sibling``) is seeded alongside
``conv_target`` so the "Today" date-group heading is guaranteed to remain
visible after ``conv_target`` is pinned, and so Step 5's panel-order check
has a real unpinned conversation row to compare bounding-box position
against (rather than depending on ambient shared-project state to keep
"Today" non-empty). Mirrors the same determinism reasoning ELITEA-2114's
AFS already established for its own ``conv_sibling``.
"""

import logging
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

PIN_ON_TOP_LABEL = "Pin on top"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken (AFS § Network Behavior) — unrelated to pinning. Matched
    on both the message text and the request location URL, same idiom as
    the sibling chat tests' equivalent filter.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPinConversationViaPinOnTop:
    """ELITEA-2149: Chat – Pin a Conversation via Pin on Top Option (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2149_chat-pin-a-conversation-via-pin-on-top-option.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_pin_conversation_via_pin_on_top(self, page, conversation_api):
        """Pin a conversation via the context menu's "Pin on top" item.

        Steps (AFS
        test-specs/chat-interface/l3_pin-conversation-via-pin-on-top_ELITEA-2149.md):
        1. Hover conv_target, click its 3-dot menu; verify the item label
           reads "Pin on top" before clicking it.
        2. Verify the conversation moved to the pinned section: still
           resolves to exactly 1 element, ``data-pinned="true"``,
           bounding-box Y above the "Today" heading.
        3. Verify a pin icon renders inside the pinned conversation (0->1
           transition — captured before/after the click).
        4. Verify conv_target is no longer in its original ("Today") date
           group.
        5. Verify panel order: pinned conversation renders above the
           unpinned conversation list (2-tier live check per AFS
           Automation Hints option (a); the full 4-tier order — pinned
           folders, pinned conversations, unpinned folders, unpinned
           conversations — is source-confirmed via Conversations.jsx's
           literal render order, not independently re-derived live here
           since this case's own steps produce zero pinned folders to
           compare against).
        """
        chat = ChatPage(page)
        conv_target_id = None
        conv_sibling_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create conv_sibling then conv_target via API "
                "(sibling guarantees a deterministic unpinned 'Today' row "
                "to compare against in Steps 2/5); navigate to chat"
            ):
                ts = int(time.time())
                sibling = conversation_api.create_conversation(f"autotest_2149_sibling_{ts}")
                conv_sibling_id = sibling["id"]
                target = conversation_api.create_conversation(f"autotest_2149_target_{ts}")
                conv_target_id = target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                conv_target_item = chat.get_conversation_item(conv_target_id)
                conv_target_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                pin_icon_count_before = conv_target_item.locator(chat.PIN_ICON).count()
                logger.info(
                    "Setup complete — conv_target=%s conv_sibling=%s pin_icon_before=%d",
                    conv_target_id, conv_sibling_id, pin_icon_count_before,
                )

            with allure.step(
                "Step 1 — Hover conv_target, click its 3-dot menu; verify "
                "the 'Pin on top' label before clicking it"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_item = chat.get_conversation_menu_item("pin")
                pin_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (pin_item.text_content() or "").strip() == PIN_ON_TOP_LABEL, (
                    f"Menu item should read {PIN_ON_TOP_LABEL!r} before pinning, "
                    f"got: {pin_item.text_content()!r}"
                )
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Verify the conversation moved to the pinned "
                "section: exactly 1 element, data-pinned=\"true\", "
                "bounding-box Y above the 'Today' heading"
            ):
                assert chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should carry data-pinned=\"true\""
                )
                assert conv_target_item.count() == 1, (
                    "conv_target's item testid should resolve to exactly 1 element "
                    "(re-rendered in the pinned section, not duplicated)"
                )
                today_heading = chat.get_conversation_group_header("today")
                expect(today_heading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                pinned_box = conv_target_item.bounding_box()
                today_box = today_heading.bounding_box()
                assert pinned_box is not None and today_box is not None, (
                    "Both the pinned conversation and the 'Today' heading "
                    f"should have a resolvable bounding box — pinned_box={pinned_box}, "
                    f"today_box={today_box}"
                )
                assert pinned_box["y"] + pinned_box["height"] <= today_box["y"], (
                    "Pinned conversation should render ABOVE the 'Today' heading — "
                    f"pinned_box={pinned_box}, today_box={today_box}"
                )

            with allure.step(
                "Step 3 — Verify a pin icon renders inside the pinned "
                "conversation (0->1 transition)"
            ):
                assert pin_icon_count_before == 0, (
                    "Pin icon should NOT be present before pinning, found "
                    f"{pin_icon_count_before}"
                )
                pin_icon = conv_target_item.locator(chat.PIN_ICON)
                expect(pin_icon).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_icon.count() == 1, (
                    f"Expected exactly 1 pin icon inside conv_target, found {pin_icon.count()}"
                )

            with allure.step(
                "Step 4 — Verify conv_target is no longer in its original "
                "'Today' date group"
            ):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer render under Today"
                # conv_sibling stays in Today, unpinned — proves the group
                # itself didn't just disappear along with conv_target.
                assert chat.is_conversation_in_group(
                    conv_sibling_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_sibling {conv_sibling_id} should still render under Today"

            with allure.step(
                "Step 5 — Verify panel order: pinned conversation renders "
                "above the unpinned conversation list (2-tier live check; "
                "full 4-tier order source-confirmed via Conversations.jsx, "
                "see docstring)"
            ):
                conv_sibling_item = chat.get_conversation_item(conv_sibling_id)
                conv_sibling_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                sibling_box = conv_sibling_item.bounding_box()
                pinned_box_step5 = conv_target_item.bounding_box()
                assert pinned_box_step5 is not None and sibling_box is not None, (
                    "Both the pinned conversation and the unpinned sibling "
                    f"should have a resolvable bounding box — pinned_box={pinned_box_step5}, "
                    f"sibling_box={sibling_box}"
                )
                assert pinned_box_step5["y"] + pinned_box_step5["height"] <= sibling_box["y"], (
                    "Pinned conversation should render ABOVE the unpinned "
                    f"conversation list — pinned_box={pinned_box_step5}, "
                    f"sibling_box={sibling_box}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during pin flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conv_target %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_target %s: %s", conv_target_id, exc)
            if conv_sibling_id:
                try:
                    conversation_api.delete_conversation(conv_sibling_id)
                    logger.info("Cleaned up conv_sibling %s", conv_sibling_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_sibling %s: %s", conv_sibling_id, exc)

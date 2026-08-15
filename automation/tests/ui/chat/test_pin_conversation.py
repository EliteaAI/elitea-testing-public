"""UI Tests for ELITEA-2149 / ELITEA-2150 — Chat: Pin / Unpin a Conversation.

ELITEA-2149 verifies pinning a conversation via the conversation's 3-dot menu
"Pin on top" item: the conversation moves into the pinned section (above date
groups), a pin icon renders next to its name, it disappears from its
original date group, and the pinned section renders above the unpinned
conversation list.

ELITEA-2150 verifies the inverse flow: unpinning an already-pinned
conversation via the SAME menu item (now labelled "Unpin") removes it from
the pinned section, hides the pin icon, and returns it to its date group.

Specs:
- test-specs/chat-interface/l3_pin-conversation-via-pin-on-top_ELITEA-2149.md
- test-specs/chat-interface/lextend_unpin-a-pinned-conversation_ELITEA-2150.md

Shares the conversation 3-dot context-menu surface with ELITEA-2135/
ELITEA-2137 (the "Move to" flows) but never opens "Move to" — the "pin"
item has no submenu, so this test is NOT affected by the "Move to"
activation-gesture defect filed against those two cases
(EliteaAI/elitea-testing-public#1117); confirmed live during analysis.

No product defects found — all case steps (both ELITEA-2149 and ELITEA-2150)
executed live end-to-end and matched expected results exactly.

Implementer addition (not in the AFS's own Test Data table, but within its
recommended scope — see AFS § Automation Hints option (a)): a second,
unpinned sibling conversation (``conv_sibling``) is seeded alongside
``conv_target`` so the "Today" date-group heading is guaranteed to remain
visible after ``conv_target`` is pinned, and so Step 5's panel-order check
has a real unpinned conversation row to compare bounding-box position
against (rather than depending on ambient shared-project state to keep
"Today" non-empty). Mirrors the same determinism reasoning ELITEA-2114's
AFS already established for its own ``conv_sibling``.

ELITEA-2150's own test (``TestUnpinConversationViaContextMenu``) pins
``conv_target`` via the UI as a SETUP action (not a case step) — reusing
the same already-covered "Pin on top" flow ELITEA-2149's own test proves
correct — to reach the "at least one pinned conversation exists"
precondition, then exercises the real case steps (unpin, verify removal).
A pinned conversation's row carries the same ``aria-disabled="true"``
draggable-wrapper ancestor already documented for pinned folders
(``isDragDisabled={isPinned}``) — ``open_conversation_context_menu()``'s
existing ``force=True`` click already bypasses it; see
test-specs/chat-interface/_surface.md's Pin conversation section for the
live-confirmed DOM-chain detail.

ELITEA-2157/2158 (added chat-remaining-w09, ``TestPinDisabledInFolderThenMovedAndPinned``):
a family AFS covering the OTHER side of the same
``disabled: !isPinned && !!conversation.folder_id`` rule — "Pin on top" is
present-but-DISABLED for a conversation still inside a folder, and becomes
enabled once "Move to" > "Back to the list" moves it out, at which point
pinning it exercises the same already-covered ELITEA-2149 mechanism. See
test-specs/chat-interface/
l3_pin-disabled-in-folder-then-moved-and-pinned_ELITEA-2157_2158.md.
"""

import logging
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

PIN_ON_TOP_LABEL = "Pin on top"
UNPIN_LABEL = "Unpin"


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
                pin_icon_count_before = chat.get_pin_icon(conv_target_id).count()
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
                pin_icon = chat.get_pin_icon(conv_target_id)
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


class TestUnpinConversationViaContextMenu:
    """ELITEA-2150: Chat – Unpin a Pinned Conversation (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2150_chat-unpin-a-pinned-conversation.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_unpin_conversation_via_context_menu(self, page, conversation_api):
        """Unpin an already-pinned conversation via the context menu's "Unpin" item.

        Steps (AFS
        test-specs/chat-interface/lextend_unpin-a-pinned-conversation_ELITEA-2150.md):
        1. Hover conv_target (already pinned via UI setup), click its 3-dot
           menu; verify the item label reads "Unpin" before clicking it.
        2. Verify the conversation is removed from the pinned section:
           still resolves to exactly 1 element, data-pinned flips to
           "false".
        3. Verify the pin icon is no longer displayed (1->0 transition —
           captured before/after the click).
        4. Verify conv_target reappears in its "Today" date group;
           conv_sibling (never pinned) stays in "Today" too, proving the
           group itself wasn't disturbed.
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
                "Setup — create conv_sibling then conv_target via API, "
                "navigate to chat, and pin conv_target via the UI (already-"
                "covered ELITEA-2149 flow) to reach the 'at least one "
                "pinned conversation exists' precondition"
            ):
                ts = int(time.time())
                sibling = conversation_api.create_conversation(f"autotest_2150_sibling_{ts}")
                conv_sibling_id = sibling["id"]
                target = conversation_api.create_conversation(f"autotest_2150_target_{ts}")
                conv_target_id = target["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                conv_target_item = chat.get_conversation_item(conv_target_id)
                conv_target_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_item_pre = chat.get_conversation_menu_item("pin")
                pin_item_pre.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (pin_item_pre.text_content() or "").strip() == PIN_ON_TOP_LABEL, (
                    f"Menu item should read {PIN_ON_TOP_LABEL!r} before pinning, "
                    f"got: {pin_item_pre.text_content()!r}"
                )
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Setup: conv_target {conv_target_id} should be pinned "
                    "(data-pinned=\"true\") before the unpin case steps run"
                )
                pin_icon_count_before_unpin = chat.get_pin_icon(conv_target_id).count()
                logger.info(
                    "Setup complete — conv_target=%s (pinned) conv_sibling=%s pin_icon_before_unpin=%d",
                    conv_target_id, conv_sibling_id, pin_icon_count_before_unpin,
                )

            with allure.step(
                "Step 1 — Hover conv_target, click its 3-dot menu; verify "
                "the 'Unpin' label before clicking it"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                unpin_item = chat.get_conversation_menu_item("pin")
                unpin_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (unpin_item.text_content() or "").strip() == UNPIN_LABEL, (
                    f"Menu item should read {UNPIN_LABEL!r} for an already-pinned "
                    f"conversation, got: {unpin_item.text_content()!r}"
                )
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Verify the conversation is removed from the "
                "pinned section: exactly 1 element, data-pinned=\"false\""
            ):
                assert not chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should no longer carry data-pinned=\"true\""
                )
                assert conv_target_item.count() == 1, (
                    "conv_target's item testid should resolve to exactly 1 element "
                    "(re-rendered back into the date-grouped list, not duplicated)"
                )

            with allure.step(
                "Step 3 — Verify the pin icon is no longer displayed "
                "(1->0 transition)"
            ):
                assert pin_icon_count_before_unpin == 1, (
                    "Pin icon should have been present before unpinning, found "
                    f"{pin_icon_count_before_unpin}"
                )
                pin_icon = chat.get_pin_icon(conv_target_id)
                expect(pin_icon).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify conv_target reappears in its 'Today' date "
                "group; conv_sibling stays in 'Today' too"
            ):
                assert chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should be back under Today after unpin"
                assert chat.is_conversation_in_group(
                    conv_sibling_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_sibling {conv_sibling_id} should still render under Today"

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during unpin flow: "
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


class TestChatPanelOrderingPinnedFoldersAndConversations:
    """ELITEA-2151: Chat – Pinned Conversation Appears Above Unpinned Folders
    and Conversations (l2, medium).

    Extends this file's pin surface with the full 4-tier panel-order check
    ELITEA-2149's own AFS explicitly deferred (§ Automation Hints option (b)):
    ELITEA-2149's Step 5 only ever proves 2 of the 4 tiers (pinned
    conversation above the "Today" heading / an unpinned sibling), because
    that case's own steps never produce a pinned FOLDER to compare against.
    This test seeds one pinned folder alongside a pinned conversation (plus
    one unpinned folder and one unpinned conversation) and asserts all 4
    tiers — pinned folders, pinned conversations, unpinned folders, unpinned
    conversations — via bounding-box Y-position, per
    ``Conversations.jsx``'s source-confirmed render order
    (``renderFoldersSection({isPinned: true})`` -> ``<PinnedConversations>``
    -> ``renderFoldersSection({isPinned: false})`` ->
    ``<DroppableGroupedArea><GroupedConversations>``).

    Spec: test-specs/chat-interface/lextend_pinned-conversation-panel-ordering_ELITEA-2151.md

    Zero new page-object work — reuses ``pin_folder_via_menu()``,
    ``is_folder_pinned()``, ``get_folder_item()`` (folder side, ELITEA-2121/
    2130) and ``open_conversation_context_menu()``, ``get_conversation_menu_item()``,
    ``click_conversation_menu_item()``, ``is_conversation_pinned()``,
    ``get_conversation_item()`` (conversation side, ELITEA-2114/2149) —
    every handle this test needs already exists on this surface.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2151_chat-pinned-conversation-appears-above-unpinned-folders-and-conversations.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_pinned_folder_and_conversation_render_above_unpinned_panel_order(
        self, page, conversation_api,
    ):
        """Full 4-tier panel order: pinned folders, pinned conversations,
        unpinned folders, unpinned conversations.

        Steps (AFS
        test-specs/chat-interface/lextend_pinned-conversation-panel-ordering_ELITEA-2151.md):
        1. Pin a folder via its dot-menu's "Pin on top" item, and pin a
           conversation via its own 3-dot menu's "Pin on top" item; verify
           both carry ``data-pinned="true"``.
        2. Verify the full left-panel order top to bottom: pinned folder,
           pinned conversation, unpinned folder, unpinned conversation
           (3 adjacent-tier bounding-box Y comparisons spanning all 4 tiers).
        3. Verify no pinned item (folder or conversation) renders below any
           unpinned item (folder or conversation) — the 2 non-adjacent
           "skip" pairs the adjacent chain in step 2 only proves
           transitively, asserted directly here per the case's own wording.
        """
        chat = ChatPage(page)
        folder_pinned_id = None
        folder_unpinned_id = None
        conv_target_id = None
        conv_unpinned_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — seed folder_pinned, folder_unpinned, conv_target "
                "(to be pinned), conv_unpinned via API; navigate to chat"
            ):
                ts = int(time.time())
                folder_pinned = conversation_api.create_folder(f"autotest_2151_pinned_folder_{ts}")
                folder_pinned_id = folder_pinned["id"]
                folder_unpinned = conversation_api.create_folder(f"autotest_2151_unpinned_folder_{ts}")
                folder_unpinned_id = folder_unpinned["id"]
                target = conversation_api.create_conversation(f"autotest_2151_target_{ts}")
                conv_target_id = target["id"]
                unpinned_conv = conversation_api.create_conversation(f"autotest_2151_unpinned_{ts}")
                conv_unpinned_id = unpinned_conv["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                chat.get_folder_item(folder_pinned_id).wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT,
                )
                chat.get_folder_item(folder_unpinned_id).wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT,
                )
                conv_target_item = chat.get_conversation_item(conv_target_id)
                conv_target_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                conv_unpinned_item = chat.get_conversation_item(conv_unpinned_id)
                conv_unpinned_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

                assert not chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded folder {folder_pinned_id} should not start pinned"
                )
                assert not chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded conversation {conv_target_id} should not start pinned"
                )
                logger.info(
                    "Setup complete — folder_pinned=%s folder_unpinned=%s "
                    "conv_target=%s conv_unpinned=%s",
                    folder_pinned_id, folder_unpinned_id, conv_target_id, conv_unpinned_id,
                )

            with allure.step(
                "Step 1 — Pin folder_pinned via its dot-menu, then pin "
                "conv_target via its 3-dot menu's 'Pin on top'; verify both "
                "carry data-pinned=\"true\""
            ):
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as pin_folder_response_info:
                    chat.pin_folder_via_menu(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_folder_response = pin_folder_response_info.value
                assert pin_folder_response.status == 200, (
                    f"Pin folder PATCH should resolve 200, got {pin_folder_response.status} "
                    f"for {pin_folder_response.url}"
                )
                assert chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Folder {folder_pinned_id} should carry data-pinned=\"true\" after pinning"
                )

                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_item = chat.get_conversation_menu_item("pin")
                pin_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (pin_item.text_content() or "").strip() == PIN_ON_TOP_LABEL, (
                    f"Menu item should read {PIN_ON_TOP_LABEL!r} before pinning, "
                    f"got: {pin_item.text_content()!r}"
                )
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Conversation {conv_target_id} should carry data-pinned=\"true\" after pinning"
                )

            with allure.step(
                "Step 2 — Verify the full left-panel order top to bottom: "
                "pinned folder, pinned conversation, unpinned folder, "
                "unpinned conversation (bounding-box Y-position, all 4 tiers)"
            ):
                folder_pinned_box = chat.get_folder_item(folder_pinned_id).bounding_box()
                conv_target_box = conv_target_item.bounding_box()
                folder_unpinned_box = chat.get_folder_item(folder_unpinned_id).bounding_box()
                conv_unpinned_box = conv_unpinned_item.bounding_box()

                assert all(
                    box is not None
                    for box in (
                        folder_pinned_box, conv_target_box, folder_unpinned_box, conv_unpinned_box,
                    )
                ), (
                    "All 4 tiers' representative elements should have a resolvable bounding "
                    f"box — folder_pinned={folder_pinned_box}, conv_target={conv_target_box}, "
                    f"folder_unpinned={folder_unpinned_box}, conv_unpinned={conv_unpinned_box}"
                )

                assert folder_pinned_box["y"] + folder_pinned_box["height"] <= conv_target_box["y"], (
                    "Pinned folder should render ABOVE the pinned conversation — "
                    f"folder_pinned_box={folder_pinned_box}, conv_target_box={conv_target_box}"
                )
                assert conv_target_box["y"] + conv_target_box["height"] <= folder_unpinned_box["y"], (
                    "Pinned conversation should render ABOVE the unpinned folder — "
                    f"conv_target_box={conv_target_box}, folder_unpinned_box={folder_unpinned_box}"
                )
                assert folder_unpinned_box["y"] + folder_unpinned_box["height"] <= conv_unpinned_box["y"], (
                    "Unpinned folder should render ABOVE the unpinned conversation list — "
                    f"folder_unpinned_box={folder_unpinned_box}, conv_unpinned_box={conv_unpinned_box}"
                )

            with allure.step(
                "Step 3 — Verify no pinned item (folder or conversation) "
                "renders below any unpinned item (folder or conversation)"
            ):
                assert folder_pinned_box["y"] + folder_pinned_box["height"] <= folder_unpinned_box["y"], (
                    "Pinned folder should render ABOVE the unpinned folder — "
                    f"folder_pinned_box={folder_pinned_box}, folder_unpinned_box={folder_unpinned_box}"
                )
                assert folder_pinned_box["y"] + folder_pinned_box["height"] <= conv_unpinned_box["y"], (
                    "Pinned folder should render ABOVE the unpinned conversation — "
                    f"folder_pinned_box={folder_pinned_box}, conv_unpinned_box={conv_unpinned_box}"
                )
                assert conv_target_box["y"] + conv_target_box["height"] <= conv_unpinned_box["y"], (
                    "Pinned conversation should render ABOVE the unpinned conversation — "
                    f"conv_target_box={conv_target_box}, conv_unpinned_box={conv_unpinned_box}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during panel-order flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conv_target %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_target %s: %s", conv_target_id, exc)
            if conv_unpinned_id:
                try:
                    conversation_api.delete_conversation(conv_unpinned_id)
                    logger.info("Cleaned up conv_unpinned %s", conv_unpinned_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_unpinned %s: %s", conv_unpinned_id, exc)
            if folder_pinned_id:
                try:
                    conversation_api.delete_folder(folder_pinned_id)
                    logger.info("Cleaned up folder_pinned %s", folder_pinned_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_pinned %s: %s", folder_pinned_id, exc)
            if folder_unpinned_id:
                try:
                    conversation_api.delete_folder(folder_unpinned_id)
                    logger.info("Cleaned up folder_unpinned %s", folder_unpinned_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_unpinned %s: %s", folder_unpinned_id, exc)


class TestPinDisabledInFolderThenMovedAndPinned:
    """ELITEA-2157/2158: Pin on Top Disabled Inside a Folder, Enabled After
    Moving Out (family AFS, l3, medium).

    ELITEA-2158's own Step 1 ("verify 'Pin on top' is greyed out for a
    conversation inside a folder") IS ELITEA-2157's entire subject. One
    continuous live flow on a single seeded conversation honestly satisfies
    both cases' full Pass/Fail criteria — see the AFS's own family_afs
    reasoning (test-specs/chat-interface/
    l3_pin-disabled-in-folder-then-moved-and-pinned_ELITEA-2157_2158.md).
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2157_chat-conversation-inside-a-folder-cannot-be-pinned-separately.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2158_chat-pin-conversation-inside-folder-by-moving-it-out-first.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_pin_disabled_in_folder_then_moved_and_pinned(self, page, conversation_api):
        """Pin on top is disabled for an in-folder conversation; a forced
        click has no effect; moving it out via 'Move to' > 'Back to the
        list' enables Pin on top, and clicking it pins the conversation.

        Steps (AFS
        test-specs/chat-interface/
        l3_pin-disabled-in-folder-then-moved-and-pinned_ELITEA-2157_2158.md):
        1. Expand folder containing conv_target; verify it's inside.
        2. Hover conv_target, click its 3-dot menu; verify the 6-item
           in-folder menu set mounts (one more than the flat-list 5-item
           set — Duplicate is present when inside a folder).
        3. Verify 'Pin on top' is disabled (ELITEA-2157 steps 1-2).
        4. Attempt a forced click on the disabled item; verify no pin
           mutation request fires (ELITEA-2157 step 3).
        5. Verify conv_target is still inside the folder and never pinned
           (ELITEA-2157 step 4).
        6. Open 'Move to' submenu, click 'Back to the list'; verify the
           PUT resolves 200 with folder_id: null and the success toast
           (ELITEA-2158 step 2).
        7. Verify conv_target now renders in the 'Today' date group.
        8. Re-open the 3-dot menu; verify 'Pin on top' is now enabled
           (ELITEA-2158 steps 3-4).
        9. Click 'Pin on top'; verify conv_target moves into the pinned
           section with a pin icon (ELITEA-2158 step 5, same mechanism
           ELITEA-2149's already-covered test asserts).

        A second, unpinned sibling conversation (``conv_sibling``) is
        seeded so the 'Today' date-group heading is guaranteed to remain
        visible after ``conv_target`` is pinned (same determinism
        reasoning ELITEA-2149's/ELITEA-2114's AFSes already establish for
        their own siblings).
        """
        chat = ChatPage(page)
        conv_target_id = None
        conv_sibling_id = None
        folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder + conv_sibling + conv_target via "
                "API; move conv_target into folder via API; navigate to chat"
            ):
                ts = int(time.time())
                folder = conversation_api.create_folder(f"autotest_2157_folder_{ts}")
                folder_id = folder["id"]
                sibling = conversation_api.create_conversation(f"autotest_2157_sibling_{ts}")
                conv_sibling_id = sibling["id"]
                target = conversation_api.create_conversation(f"autotest_2157_target_{ts}")
                conv_target_id = target["id"]
                conversation_api.move_conversation_to_folder(conv_target_id, folder_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Expand the folder containing conv_target; "
                "verify it's inside"
            ):
                chat.expand_folder(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_id), (
                    f"folder {folder_id} should carry data-expanded=\"true\" "
                    "after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"conv_target {conv_target_id} should be inside folder {folder_id}"

            with allure.step(
                "Step 2 — Hover conv_target, click its 3-dot menu; verify "
                "the 6-item in-folder menu set mounts"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_open_conversation_menu_item_count() == 6, (
                    "An in-folder conversation's context menu should render 6 items "
                    "(Rename, Move to, Playback, Duplicate, Pin on top, Delete) — "
                    f"got {chat.get_open_conversation_menu_item_count()}"
                )

            with allure.step(
                "Step 3 — Verify 'Pin on top' is disabled for the "
                "in-folder conversation (ELITEA-2157 steps 1-2)"
            ):
                pin_item = chat.get_conversation_menu_item("pin")
                expect(pin_item).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_item.get_attribute("aria-disabled") == "true", (
                    "'Pin on top' should be disabled (aria-disabled=\"true\") for a "
                    "conversation inside a folder"
                )

            with allure.step(
                "Step 4 — Attempt a forced click on the disabled 'Pin on "
                "top' item; verify no pin mutation request fires "
                "(ELITEA-2157 step 3)"
            ):
                pin_request_fired = True
                try:
                    with page.expect_response(
                        lambda r: "/pin/prompt_lib/" in r.url and str(conv_target_id) in r.url,
                        timeout=3_000,
                    ):
                        pin_item.click(force=True)
                    pin_request_fired = True
                except PlaywrightTimeoutError:
                    pin_request_fired = False
                assert not pin_request_fired, (
                    "Clicking the disabled 'Pin on top' item should not fire a "
                    "pin mutation request"
                )
                # MUI's ButtonBase never fires the disabled item's onClick, so
                # the menu's own close-on-select trigger never runs either —
                # the context menu stays open. Close it explicitly (Escape,
                # same established pattern as ChatPage's own dialog-dismiss
                # methods) before any further hover, or the still-open
                # popover's invisible backdrop intercepts it.
                page.keyboard.press("Escape")
                expect(page.locator(chat.FOLDER_CONTEXT_MENU_POPOVER)).to_be_hidden(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 5 — Verify conv_target is still inside the folder "
                "and was never pinned (ELITEA-2157 step 4)"
            ):
                assert chat.is_conversation_in_folder(
                    folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), f"conv_target {conv_target_id} should still be inside folder {folder_id}"
                assert not chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should not carry data-pinned=\"true\" "
                    "after a no-op click on the disabled item"
                )
                assert chat.get_pin_icon(conv_target_id).count() == 0, (
                    "conv_target should show no pin icon after a no-op click on the "
                    "disabled 'Pin on top' item"
                )

            with allure.step(
                "Step 6 — Open 'Move to' submenu, click 'Back to the "
                "list'; verify the PUT resolves 200 with folder_id: null "
                "and the success toast (ELITEA-2158 step 2)"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.move_to_back_to_list_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.select_move_to_back_to_list(timeout=UI_ELEMENT_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Back-to-the-list PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") is None, (
                    "Response body 'folder_id' should be null after moving back to "
                    f"the list, got: {move_body!r}"
                )
                expect(chat.toast_message).to_have_text(
                    "Chat moved to ungrouped area successfully", timeout=UI_ELEMENT_TIMEOUT
                )
                # The "Move to" submenu's parent Menu popover (shared DotMenu
                # component, same element for every conversation/folder menu
                # — pre-existing FOLDER_CONTEXT_MENU_POPOVER constant, first
                # live caller here per canon #511) must fully unmount before
                # re-hovering conv_target below — its invisible MuiBackdrop
                # otherwise intercepts the hover while still closing.
                expect(page.locator(chat.FOLDER_CONTEXT_MENU_POPOVER)).to_be_hidden(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 7 — Verify conv_target now renders in the 'Today' "
                "date group"
            ):
                assert chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should render under Today after the move"

            with allure.step(
                "Step 8 — Hover conv_target (now un-foldered), re-open "
                "its 3-dot menu; verify 'Pin on top' is now enabled "
                "(ELITEA-2158 steps 3-4)"
            ):
                chat.open_conversation_context_menu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_item_enabled = chat.get_conversation_menu_item("pin")
                expect(pin_item_enabled).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_item_enabled.get_attribute("aria-disabled") != "true", (
                    "'Pin on top' should no longer be disabled once conv_target is "
                    "out of the folder"
                )
                assert (pin_item_enabled.text_content() or "").strip() == PIN_ON_TOP_LABEL, (
                    f"Menu item should read {PIN_ON_TOP_LABEL!r} before pinning, got: "
                    f"{pin_item_enabled.text_content()!r}"
                )

            with allure.step(
                "Step 9 — Click 'Pin on top'; verify conv_target moves "
                "into the pinned section with a pin icon (ELITEA-2158 "
                "step 5)"
            ):
                pin_icon_count_before = chat.get_pin_icon(conv_target_id).count()
                chat.click_conversation_menu_item("pin", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_pinned(conv_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"conv_target {conv_target_id} should carry data-pinned=\"true\" "
                    "after clicking 'Pin on top'"
                )
                assert pin_icon_count_before == 0, (
                    "Pin icon should NOT be present before pinning, found "
                    f"{pin_icon_count_before}"
                )
                pin_icon = chat.get_pin_icon(conv_target_id)
                expect(pin_icon).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert pin_icon.count() == 1, (
                    f"Expected exactly 1 pin icon inside conv_target, found {pin_icon.count()}"
                )
                today_heading = chat.get_conversation_group_header("today")
                expect(today_heading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                conv_target_item = chat.get_conversation_item(conv_target_id)
                pinned_box = conv_target_item.bounding_box()
                today_box = today_heading.bounding_box()
                assert pinned_box is not None and today_box is not None, (
                    "Both the pinned conversation and the 'Today' heading should "
                    f"have a resolvable bounding box — pinned_box={pinned_box}, "
                    f"today_box={today_box}"
                )
                assert pinned_box["y"] + pinned_box["height"] <= today_box["y"], (
                    "Pinned conversation should render ABOVE the 'Today' heading — "
                    f"pinned_box={pinned_box}, today_box={today_box}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during pin-disabled-then-move-and-pin "
                    f"flow: {[m.text for m in console_messages]!r}"
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
            if folder_id:
                try:
                    chat.delete_folder_via_menu(folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder %s", folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)

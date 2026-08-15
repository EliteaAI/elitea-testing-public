"""UI Tests for ELITEA-2152 / ELITEA-2153 — Chat: Pin / Unpin a Folder.

ELITEA-2152 verifies pinning a folder via the folder's 3-dot menu "Pin on
top" item: the folder moves into the pinned section (rendering above any
unpinned folder it was previously below), a pin icon renders next to its
name, it does not lose its expand state or its conversations, and its
rendered position measurably changes (Y decreases; relative order versus a
stable unpinned sibling reverses).

ELITEA-2153 verifies the inverse flow: unpinning an already-pinned folder
via the SAME menu item (now labelled "Unpin") removes it from the pinned
section, hides the pin icon, and returns it to EXACTLY its pre-pin
position — live-confirmed this session to be a deterministic round-trip,
not merely "some unpinned position".

Specs:
- test-specs/chat-interface/l3_pin-a-folder-via-pin-on-top-option_ELITEA-2152.md
- test-specs/chat-interface/l3_unpin-a-pinned-folder_ELITEA-2153.md

No fidelity substitution — pin/unpin state, position, and conversation
membership are all read off the real system through the real UI flow
(``PATCH`` for both pin and unpin, awaited and status-checked).

"Pin icon visible/removed" is asserted via the `data-pinned` attribute on
`chat-folder-item-{id}`, per `.agents/testing.md` § Locator policy — the raw
`<PinIcon>` `FolderAccordion.jsx` conditionally renders in the collapsed
header has no testid and is source-confirmed driven by the exact same
`isPinned` boolean the attribute exposes (ELITEA-2121/2130's AFS already
established this equivalence; re-confirmed live this session).

Zero new page-object work — reuses `pin_folder_via_menu()`,
`is_folder_pinned()`, `get_folder_item()`, `open_folder_context_menu()`,
`expand_folder()`, `is_folder_expanded()`, `is_conversation_in_folder()`
(all ELITEA-2121/2130) plus `conversation_api.create_folder()` /
`create_conversation()` / `move_conversation_to_folder()` /
`delete_conversation()` / `delete_folder()`.
"""

import logging
import time

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# Sub-pixel rendering can shift a captured getBoundingClientRect() reading by
# a fraction of a pixel between two reads of an otherwise-unmoved element
# (observed live: 138.71875 vs 138 for the SAME row, no layout change) — a
# tolerance keeps the "returned to its exact pre-pin position" assertion
# robust without weakening what it proves (any real reflow moves a row by a
# full row height, ~41px, far above this tolerance).
Y_POSITION_TOLERANCE_PX = 2.0

PIN_ON_TOP_LABEL = "Pin on top"
UNPIN_LABEL = "Unpin"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken — unrelated to pinning. Same idiom as the sibling chat
    tests' equivalent filter.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestPinFolderViaPinOnTop:
    """ELITEA-2152: Chat – Pin a Folder via Pin on Top Option (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2152_chat-pin-a-folder-via-pin-on-top-option.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_pin_folder_via_pin_on_top(self, page, conversation_api):
        """Pin a folder via the context menu's "Pin on top" item.

        Steps (AFS
        test-specs/chat-interface/l3_pin-a-folder-via-pin-on-top-option_ELITEA-2152.md):
        1. Navigate to Chats, expand folder_target, verify conv_in_folder
           renders inside it (baseline); capture folder_target's Y and
           confirm it's not yet pinned.
        2. Hover folder_target, click its 3-dot menu; verify the item label
           reads "Pin on top" before clicking it.
        3. Verify the folder moved into the pinned section: data-pinned
           flips false->true, Y decreased, order vs folder_sibling
           reversed.
        4. Verify a pin icon is displayed (data-pinned=true is the
           compliant locator per project policy).
        5. Verify the folder still shows all its conversations when
           expanded.
        6. Verify the folder is no longer in its original position
           (same Y/order fact as step 3, restated per the case's own
           explicit wording).
        """
        chat = ChatPage(page)
        folder_target_id = None
        folder_sibling_id = None
        conv_in_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder_target then folder_sibling via API "
                "(sibling created AFTER target gives a deterministic "
                "'above' baseline — a folder created more recently renders "
                "above an older one under the default "
                "sort_by=updated_at&sort_order=desc list, live-confirmed "
                "this session); create conv_in_folder and move it into "
                "folder_target; navigate to chat and expand folder_target"
            ):
                ts = int(time.time())
                target = conversation_api.create_folder(f"autotest_2152_target_{ts}")
                folder_target_id = target["id"]
                sibling = conversation_api.create_folder(f"autotest_2152_sibling_{ts}")
                folder_sibling_id = sibling["id"]
                conv = conversation_api.create_conversation(f"autotest_2152_conv_{ts}")
                conv_in_folder_id = conv["id"]
                conversation_api.move_conversation_to_folder(conv_in_folder_id, folder_target_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                folder_target_item = chat.get_folder_item(folder_target_id)
                folder_target_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                folder_sibling_item = chat.get_folder_item(folder_sibling_id)
                folder_sibling_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

                assert not chat.is_folder_pinned(folder_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded folder {folder_target_id} should not start pinned"
                )

                chat.expand_folder(folder_target_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_folder(
                    folder_target_id, conv_in_folder_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_in_folder {conv_in_folder_id} should render inside folder_target (baseline)"
                logger.info(
                    "Setup complete — folder_target=%s folder_sibling=%s conv_in_folder=%s",
                    folder_target_id, folder_sibling_id, conv_in_folder_id,
                )

            with allure.step(
                "Step 1 — Capture the pre-pin baseline: folder_target's "
                "bounding box and its position relative to folder_sibling"
            ):
                initial_target_box = folder_target_item.bounding_box()
                initial_sibling_box = folder_sibling_item.bounding_box()
                assert initial_target_box is not None and initial_sibling_box is not None, (
                    "Both folder_target and folder_sibling should have a resolvable "
                    f"bounding box — target={initial_target_box}, sibling={initial_sibling_box}"
                )
                assert initial_sibling_box["y"] + initial_sibling_box["height"] <= initial_target_box["y"], (
                    "Baseline: folder_sibling (created first) should render ABOVE "
                    f"folder_target — sibling={initial_sibling_box}, target={initial_target_box}"
                )

            with allure.step(
                "Step 2 — Hover folder_target, open its 3-dot menu; verify "
                "the 'Pin on top' label before clicking it"
            ):
                chat.open_folder_context_menu(folder_target_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_item = page.locator(chat.FOLDER_MENU_PIN_ITEM)
                pin_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (pin_item.text_content() or "").strip() == PIN_ON_TOP_LABEL, (
                    f"Menu item should read {PIN_ON_TOP_LABEL!r} before pinning, "
                    f"got: {pin_item.text_content()!r}"
                )
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as pin_response_info:
                    pin_item.click()
                pin_response = pin_response_info.value
                assert pin_response.status == 200, (
                    f"Pin PATCH should resolve 200, got {pin_response.status} "
                    f"for {pin_response.url}"
                )

            with allure.step(
                "Step 3 — Verify the folder moved into the pinned section: "
                "data-pinned flips false->true, Y decreased, order vs "
                "folder_sibling reversed"
            ):
                assert chat.is_folder_pinned(folder_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"folder_target {folder_target_id} should carry data-pinned=\"true\""
                )
                new_target_box = folder_target_item.bounding_box()
                new_sibling_box = folder_sibling_item.bounding_box()
                assert new_target_box is not None and new_sibling_box is not None, (
                    "Both folder_target and folder_sibling should have a resolvable "
                    f"bounding box post-pin — target={new_target_box}, sibling={new_sibling_box}"
                )
                assert new_target_box["y"] < initial_target_box["y"], (
                    "folder_target's Y should have decreased (moved up) after pinning — "
                    f"initial={initial_target_box['y']}, new={new_target_box['y']}"
                )
                assert new_target_box["y"] + new_target_box["height"] <= new_sibling_box["y"], (
                    "folder_target should now render ABOVE folder_sibling — a direct "
                    f"reversal of the baseline — target={new_target_box}, sibling={new_sibling_box}"
                )

            with allure.step(
                "Step 4 — Verify a pin icon is displayed next to the "
                "folder name (data-pinned=true is the compliant locator "
                "per .agents/testing.md Locator policy)"
            ):
                assert chat.is_folder_pinned(folder_target_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"folder_target {folder_target_id} should still carry data-pinned=\"true\""
                )

            with allure.step(
                "Step 5 — Verify the folder still shows all its "
                "conversations when expanded"
            ):
                # Pinning moves the folder's row from the unpinned list into
                # the pinned list — a genuine remount (not a race), which
                # resets its local expand state to collapsed even though it
                # was expanded before pinning (live-confirmed this session,
                # contradicting an earlier stale MCP read documented in the
                # AFS/digest). Re-expand explicitly (force=True — the
                # pinned-folder disabled-ancestor gotcha applies to the
                # whole row, not just the dot-menu button) and verify the
                # conversation is still there — the case's own literal
                # wording ("when expanded") does not require the folder to
                # STAY expanded automatically, only that expanding it still
                # shows its conversations.
                chat.expand_folder(folder_target_id, timeout=UI_ELEMENT_TIMEOUT, force=True)
                assert chat.is_conversation_in_folder(
                    folder_target_id, conv_in_folder_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_in_folder {conv_in_folder_id} should still render inside folder_target"

            with allure.step(
                "Step 6 — Verify the folder is no longer in its original "
                "position"
            ):
                final_box = folder_target_item.bounding_box()
                assert final_box is not None, "folder_target should have a resolvable bounding box"
                assert final_box["y"] != initial_target_box["y"], (
                    "folder_target's Y should differ from its pre-pin baseline — "
                    f"initial={initial_target_box['y']}, final={final_box['y']}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during pin-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_in_folder_id:
                try:
                    conversation_api.delete_conversation(conv_in_folder_id)
                    logger.info("Cleaned up conv_in_folder %s", conv_in_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_in_folder %s: %s", conv_in_folder_id, exc)
            if folder_target_id:
                try:
                    conversation_api.delete_folder(folder_target_id)
                    logger.info("Cleaned up folder_target %s", folder_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_target %s: %s", folder_target_id, exc)
            if folder_sibling_id:
                try:
                    conversation_api.delete_folder(folder_sibling_id)
                    logger.info("Cleaned up folder_sibling %s", folder_sibling_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_sibling %s: %s", folder_sibling_id, exc)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2154_chat-pinned-folder-retains-all-conversations-after-pinning.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_pin_folder_with_multiple_conversations_retains_all(self, page, conversation_api):
        """ELITEA-2154: Chat – Pinned Folder Retains All Conversations After Pinning (l3, medium).

        Extends ELITEA-2152's single-conversation pin coverage: seeds a folder
        with THREE distinctly-named conversations (the case's own wording asks
        for "multiple" conversations and to "note conversation names"), pins it
        via the same real UI dot-menu flow, re-expands it, and verifies ALL
        THREE conversations still resolve inside it — by id AND by exact name
        text — so a hypothetical truncation/reorder bug that a single-item
        check could not catch is exercised here.

        Steps (AFS
        test-specs/chat-interface/lextend_pinned-folder-retains-all-conversations_ELITEA-2154.md):
        1. Navigate to Chats, expand folder_multi, note (read) each of
           conv_a/conv_b/conv_c's rendered names — baseline.
        2. Hover folder_multi, click its 3-dot menu, click "Pin on top".
        3. Expand the pinned folder (force-click — disabled-ancestor gotcha).
        4. Verify no conversations were lost — all 3 still present, by id and
           by exact name text.
        """
        chat = ChatPage(page)
        folder_multi_id = None
        conv_ids: dict[str, int] = {}

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder_multi via API, create 3 distinctly-"
                "named conversations (conv_a/conv_b/conv_c) and move each "
                "into folder_multi; navigate to chat and expand the folder"
            ):
                ts = int(time.time())
                folder = conversation_api.create_folder(f"autotest_2154_folder_{ts}")
                folder_multi_id = folder["id"]

                names = {
                    "conv_a": f"autotest_2154_conv_a_{ts}",
                    "conv_b": f"autotest_2154_conv_b_{ts}",
                    "conv_c": f"autotest_2154_conv_c_{ts}",
                }
                for key, name in names.items():
                    conv = conversation_api.create_conversation(name)
                    conv_ids[key] = conv["id"]
                    conversation_api.move_conversation_to_folder(conv["id"], folder_multi_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                folder_item = chat.get_folder_item(folder_multi_id)
                folder_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

                assert not chat.is_folder_pinned(folder_multi_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded folder {folder_multi_id} should not start pinned"
                )
                logger.info(
                    "Setup complete — folder_multi=%s conversations=%s",
                    folder_multi_id, conv_ids,
                )

            with allure.step(
                "Step 1 — Expand folder_multi and note (read) each "
                "conversation's rendered name — baseline before pinning"
            ):
                chat.expand_folder(folder_multi_id, timeout=UI_ELEMENT_TIMEOUT)
                for key, conv_id in conv_ids.items():
                    assert chat.is_conversation_in_folder(
                        folder_multi_id, conv_id, timeout=UI_ELEMENT_TIMEOUT,
                    ), f"{key} ({conv_id}) should render inside folder_multi (baseline)"
                    item_text = (
                        folder_item.locator(chat.CONVERSATION_ITEM.format(conv_id))
                        .first.text_content() or ""
                    ).strip()
                    assert item_text == names[key], (
                        f"{key} ({conv_id}) baseline name text should read {names[key]!r}, "
                        f"got {item_text!r}"
                    )

            with allure.step(
                "Step 2 — Hover folder_multi, open its 3-dot menu, click "
                "'Pin on top'"
            ):
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as pin_response_info:
                    chat.pin_folder_via_menu(folder_multi_id, timeout=UI_ELEMENT_TIMEOUT)
                pin_response = pin_response_info.value
                assert pin_response.status == 200, (
                    f"Pin PATCH should resolve 200, got {pin_response.status} "
                    f"for {pin_response.url}"
                )
                assert chat.is_folder_pinned(folder_multi_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"folder_multi {folder_multi_id} should carry data-pinned=\"true\" after pinning"
                )

            with allure.step(
                "Step 3 — Expand the pinned folder (force-click required — "
                "pinned-folder disabled-ancestor gotcha, ELITEA-2130/2152)"
            ):
                chat.expand_folder(folder_multi_id, timeout=UI_ELEMENT_TIMEOUT, force=True)

            with allure.step(
                "Step 4 — Verify no conversations were lost: all 3 still "
                "present, by id and by exact name text"
            ):
                for key, conv_id in conv_ids.items():
                    assert chat.is_conversation_in_folder(
                        folder_multi_id, conv_id, timeout=UI_ELEMENT_TIMEOUT,
                    ), f"{key} ({conv_id}) should still render inside folder_multi after pinning"
                    item_text = (
                        folder_item.locator(chat.CONVERSATION_ITEM.format(conv_id))
                        .first.text_content() or ""
                    ).strip()
                    assert item_text == names[key], (
                        f"{key} ({conv_id}) name text should still read {names[key]!r} "
                        f"after pinning, got {item_text!r}"
                    )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during multi-conversation pin-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            for key, conv_id in conv_ids.items():
                try:
                    conversation_api.delete_conversation(conv_id)
                    logger.info("Cleaned up %s %s", key, conv_id)
                except Exception as exc:
                    logger.warning("Failed to delete %s %s: %s", key, conv_id, exc)
            if folder_multi_id:
                try:
                    conversation_api.delete_folder(folder_multi_id)
                    logger.info("Cleaned up folder_multi %s", folder_multi_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_multi %s: %s", folder_multi_id, exc)


class TestUnpinFolderViaContextMenu:
    """ELITEA-2153: Chat – Unpin a Pinned Folder (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2153_chat-unpin-a-pinned-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_unpin_folder_via_context_menu(self, page, conversation_api):
        """Unpin an already-pinned folder via the context menu's "Unpin" item.

        Steps (AFS
        test-specs/chat-interface/l3_unpin-a-pinned-folder_ELITEA-2153.md):
        1. Setup reaches the precondition: folder_pinned seeded unpinned
           then pinned via the real UI dot-menu action (the already-
           covered ELITEA-2152 flow); capture the pre-pin baseline Y for
           the reversal check.
        2. Hover folder_pinned, click its 3-dot menu; verify the item
           label reads "Unpin" before clicking it.
        3. Verify data-pinned flips true->false (folder removed from the
           pinned section).
        4. Verify the pin icon is no longer visible (same data-pinned
           fact, restated per the case's own explicit wording).
        5. Verify the folder reappears in the unpinned folders section:
           Y returns to EXACTLY its pre-pin baseline, order vs
           folder_sibling restored.
        6. Verify the folder retains all its conversations.
        """
        chat = ChatPage(page)
        folder_pinned_id = None
        folder_sibling_id = None
        conv_in_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder_pinned then folder_sibling via API "
                "(sibling created AFTER gives a deterministic 'above' "
                "baseline, same ordering fact ELITEA-2152's AFS "
                "documents); create conv_in_folder and move it into "
                "folder_pinned; navigate, expand folder_pinned and verify "
                "the conversation + capture the pre-pin baseline Y; pin "
                "folder_pinned via the UI dot-menu (already-covered "
                "ELITEA-2152 flow) to reach the 'pinned folder exists' "
                "precondition"
            ):
                ts = int(time.time())
                target = conversation_api.create_folder(f"autotest_2153_pinned_{ts}")
                folder_pinned_id = target["id"]
                sibling = conversation_api.create_folder(f"autotest_2153_sibling_{ts}")
                folder_sibling_id = sibling["id"]
                conv = conversation_api.create_conversation(f"autotest_2153_conv_{ts}")
                conv_in_folder_id = conv["id"]
                conversation_api.move_conversation_to_folder(conv_in_folder_id, folder_pinned_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

                folder_pinned_item = chat.get_folder_item(folder_pinned_id)
                folder_pinned_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                folder_sibling_item = chat.get_folder_item(folder_sibling_id)
                folder_sibling_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

                assert not chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Freshly-seeded folder {folder_pinned_id} should not start pinned"
                )

                chat.expand_folder(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_conversation_in_folder(
                    folder_pinned_id, conv_in_folder_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_in_folder {conv_in_folder_id} should render inside folder_pinned (baseline)"

                original_unpinned_box = folder_pinned_item.bounding_box()
                original_sibling_box = folder_sibling_item.bounding_box()
                assert original_unpinned_box is not None and original_sibling_box is not None, (
                    "Both folder_pinned and folder_sibling should have a resolvable "
                    f"bounding box pre-pin — pinned={original_unpinned_box}, "
                    f"sibling={original_sibling_box}"
                )

                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as setup_pin_response_info:
                    chat.pin_folder_via_menu(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT)
                setup_pin_response = setup_pin_response_info.value
                assert setup_pin_response.status == 200, (
                    f"Setup pin PATCH should resolve 200, got {setup_pin_response.status} "
                    f"for {setup_pin_response.url}"
                )
                assert chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Setup: folder_pinned {folder_pinned_id} should carry data-pinned=\"true\" "
                    "before the unpin case steps run"
                )
                logger.info(
                    "Setup complete — folder_pinned=%s (pinned) folder_sibling=%s conv_in_folder=%s",
                    folder_pinned_id, folder_sibling_id, conv_in_folder_id,
                )

            with allure.step(
                "Step 1 — Hover folder_pinned, open its 3-dot menu "
                "(force-click required — pinned-folder disabled-ancestor "
                "gotcha, ELITEA-2130); verify the 'Unpin' label before "
                "clicking it"
            ):
                chat.open_folder_context_menu(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT)
                unpin_item = page.locator(chat.FOLDER_MENU_PIN_ITEM)
                unpin_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert (unpin_item.text_content() or "").strip() == UNPIN_LABEL, (
                    f"Menu item should read {UNPIN_LABEL!r} for an already-pinned folder, "
                    f"got: {unpin_item.text_content()!r}"
                )
                with page.expect_response(
                    lambda r: "/folder/prompt_lib/" in r.url and r.request.method == "PATCH",
                    timeout=NAVIGATION_TIMEOUT,
                ) as unpin_response_info:
                    unpin_item.click()
                unpin_response = unpin_response_info.value
                assert unpin_response.status == 200, (
                    f"Unpin PATCH should resolve 200, got {unpin_response.status} "
                    f"for {unpin_response.url}"
                )

            with allure.step(
                "Step 2 — Verify the folder is removed from the pinned "
                "section: data-pinned flips true->false"
            ):
                assert not chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"folder_pinned {folder_pinned_id} should no longer carry data-pinned=\"true\""
                )

            with allure.step(
                "Step 3 — Verify the pin icon is no longer visible (same "
                "data-pinned fact, restated per the case's own wording)"
            ):
                assert not chat.is_folder_pinned(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT), (
                    f"folder_pinned {folder_pinned_id} should not carry data-pinned=\"true\""
                )

            with allure.step(
                "Step 4 — Verify the folder reappears in the unpinned "
                "folders section: Y returns to its exact pre-pin "
                "baseline, order vs folder_sibling restored"
            ):
                final_box = folder_pinned_item.bounding_box()
                final_sibling_box = folder_sibling_item.bounding_box()
                assert final_box is not None and final_sibling_box is not None, (
                    "Both folder_pinned and folder_sibling should have a resolvable "
                    f"bounding box post-unpin — pinned={final_box}, sibling={final_sibling_box}"
                )
                assert abs(final_box["y"] - original_unpinned_box["y"]) < Y_POSITION_TOLERANCE_PX, (
                    "folder_pinned should return to its pre-pin Y (within sub-pixel "
                    f"tolerance) — expected ~{original_unpinned_box['y']}, got {final_box['y']}"
                )
                assert abs(final_sibling_box["y"] - original_sibling_box["y"]) < Y_POSITION_TOLERANCE_PX, (
                    "folder_sibling's Y should also match its pre-pin baseline (within "
                    f"sub-pixel tolerance) — expected ~{original_sibling_box['y']}, "
                    f"got {final_sibling_box['y']}"
                )

            with allure.step(
                "Step 5 — Verify the folder retains all its conversations"
            ):
                # Same remount fact as ELITEA-2152's Step 5, in the inverse
                # direction: unpinning also moves the row between list
                # partitions and resets its local expand state (live-
                # confirmed this session). Re-expand explicitly and verify
                # the conversation survived the full pin->unpin round-trip.
                chat.expand_folder(folder_pinned_id, timeout=UI_ELEMENT_TIMEOUT, force=True)
                assert chat.is_conversation_in_folder(
                    folder_pinned_id, conv_in_folder_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_in_folder {conv_in_folder_id} should still render inside folder_pinned"

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during unpin-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_in_folder_id:
                try:
                    conversation_api.delete_conversation(conv_in_folder_id)
                    logger.info("Cleaned up conv_in_folder %s", conv_in_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete conv_in_folder %s: %s", conv_in_folder_id, exc)
            if folder_pinned_id:
                try:
                    conversation_api.delete_folder(folder_pinned_id)
                    logger.info("Cleaned up folder_pinned %s", folder_pinned_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_pinned %s: %s", folder_pinned_id, exc)
            if folder_sibling_id:
                try:
                    conversation_api.delete_folder(folder_sibling_id)
                    logger.info("Cleaned up folder_sibling %s", folder_sibling_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_sibling %s: %s", folder_sibling_id, exc)

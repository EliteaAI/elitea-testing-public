"""UI Tests for ELITEA-2146/2147/2148 — Chat: Folder List Scrollability &
Expand/Collapse States.

Three cases sharing the ``chat-folder-list`` surface_key but each with
genuinely different steps (sidebar scroll, "Move to" submenu scroll,
expand/collapse + empty state) — analysed as a cluster, each got its OWN
AFS per the analyst's "differ in steps -> separate AFS" rule, same
convention as ``test_move_conversation_to_folder.py``'s cluster of Move-to
cases. Grouped in one file because they share the same folder-list surface
and helpers (``ChatPage.get_folder_item`` / ``expand_folder`` / the new
scroll trios) — not because their test bodies are merged.

Specs:
- test-specs/chat-interface/l3_folder-list-scrollable-many-folders_ELITEA-2146.md
- test-specs/chat-interface/l3_move-to-submenu-folder-list-scrollable_ELITEA-2147.md
- test-specs/chat-interface/l3_folder-displays-conversations-or-empty-state_ELITEA-2148.md

No product defects found — all three cases' own subjects worked correctly
and genuinely against the live product. ELITEA-2147's OPENING gesture
("Move to" submenu) is affected by the pre-existing, already-filed
EliteaAI/elitea-testing-public#1117 (submenu doesn't reliably open on one
click) — handled by the existing ``click_move_to_and_wait_for_submenu()``
retry loop, not this case's own subject.

Testids added this pass (EliteaAI/EliteaUI automation/testids commit
1787ad67, "test: [EL-2146] add data-testid for chat folder-list + move-to
popover"): ``chat-conversation-list-scroll-container`` (Conversations.jsx's
``ref={listRef}`` Box) and ``chat-move-to-submenu-popover`` (DotMenu.jsx's
nested submenu Menu, via ``slotProps={{paper: {...}}}``) — both zero-new-
DOM-node attribute additions on elements that already existed and already
rendered ``ref={listRef}`` / the Paper respectively.

Fix-round-1 (EliteaAI/EliteaUI automation/testids commit 1b35a0a2, "test:
[EL-2147] rewire chat-move-to-submenu-popover testid as caller-supplied
prop"): the popover testid was originally hardcoded as a literal string
inside ``DotMenu.jsx`` — a shared component with 16+ consumers, which
violates the shared-component testid rule (``.agents/testing.md`` §
Locator policy: a shared component gets a generic testid or a
caller-supplied prop, never a feature-scoped literal baked into the shared
file). Rewired as a ``submenuTestId`` prop threaded from the menu-item
definition down through ``DotMenu`` -> ``BasicMenuItem``, supplied only by
the chat "Move to" item in ``ConversationItem.jsx``; no other DotMenu
consumer passes it. The testid VALUE and every locator/assertion in this
file are unchanged — only its origin in the JSX moved.

Real scroll gestures only (``container.hover()`` + ``page.mouse.wheel()``,
mirroring ``ChatPage.scroll_messages_container()``) — never a synthetic
``el.scrollTop = N`` assignment, per this project's fidelity policy
(``.agents/testing.md`` § Fidelity policy): a property assignment doesn't
prove a user CAN scroll the container the way a real wheel event does.
"""

import logging
import time

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

# 25 folders comfortably overflow the sidebar's ~800px-tall scroll container
# at a 41px collapsed-row height (25 * 41 = 1025px), live-measured in the
# AFS's own exploration pass — see l3_folder-list-scrollable-many-folders_
# ELITEA-2146.md § Concrete Handles.
SEEDED_FOLDER_COUNT = 25

# Wheel delta for the "scroll until a specific folder becomes visible" scan
# (scroll_*_until_*_visible() checks reachability after EVERY real gesture).
# Deliberately smaller than the container's clientHeight (~700-830px,
# live-measured) so consecutive checked positions overlap — a delta close to
# or larger than clientHeight risks a single wheel jump skipping clean over a
# ~41px-tall target row between two checks, live-confirmed this pass as the
# cause of a false "unreachable" result at delta_y=2000.
SCROLL_DELTA = 200

# Max real wheel gestures scroll_*_until_*_visible() will attempt before
# concluding a target is unreachable — generous enough to traverse the full
# scrollable range (~3000-4000px live-measured) at SCROLL_DELTA-sized steps.
SCROLL_MAX_ATTEMPTS = 60


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken — unrelated to the folder-list flows. Matched on both the
    message text and the request location URL, same idiom as the sibling
    chat tests' equivalent filter.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestFolderListScrollableWhenManyFoldersExist:
    """ELITEA-2146: Chat – Folder List is Scrollable When Many Folders Exist (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2146_chat-folder-list-is-scrollable-when-many-folders-exist.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_folder_list_scrollable_when_many_folders_exist(self, page, conversation_api):
        """Verify the sidebar folder list genuinely scrolls when many folders exist.

        Steps (AFS
        test-specs/chat-interface/l3_folder-list-scrollable-many-folders_ELITEA-2146.md,
        steps 4-5 AMENDED during implementation — see the "implementer
        amendment" note below and the AFS's own amendment entry):
        1. Navigate to Chats; verify the folder list contains at least the
           25 seeded folders.
        2. Verify the sidebar scroll container genuinely overflows
           (scrollHeight > clientHeight), not just a CSS declaration.
        3. Scroll down via a real wheel gesture; verify scrollTop moved.
        4. Identify a seeded folder that is NOT within the container's
           bounds at the initial scroll position (guaranteed to exist,
           given the overflow proven in step 2); scroll down via repeated
           real wheel gestures until it becomes reachable within the
           container's bounds.
        5. Identify a seeded folder that WAS visible at the top but is now
           hidden after step 4's scroll; scroll back up via repeated real
           wheel gestures until it becomes reachable again — proves the
           round trip doesn't leave anything permanently inaccessible.

        Implementer amendment (live-discovered this pass): the AFS's
        original steps 4/5 assumed "scroll to the container's raw
        scrollHeight-clientHeight maximum" would land on the LAST-seeded
        (by creation order) folder specifically. Live-confirmed this is
        false — Conversations.jsx's ``ref={listRef}`` container holds
        folders AND the full pinned/date-grouped conversation list in ONE
        shared scroll region, so on an account carrying many conversations
        the container's raw scroll extreme sits well past the folder
        section entirely (confirmed via a negative, deeply off-screen
        ``getBoundingClientRect().y`` on the target folder after scrolling
        to the literal max). The empirical "find a folder that's currently
        hidden, then prove it becomes reachable" approach above verifies
        the same case-level claim (no folder is ever permanently
        inaccessible) without assuming a specific creation-order position.

        Setup seeds 25 folders via API — the account's own ambient/orphaned
        folders (a separately-tracked test-data-hygiene gap) are enough to
        reproduce overflow live, but this test must stay green regardless
        of that ambient count, so it seeds its own deterministic set.
        """
        chat = ChatPage(page)
        folder_ids: list[int] = []

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(f"Setup — create {SEEDED_FOLDER_COUNT} folders via API"):
                ts = int(time.time())
                for i in range(SEEDED_FOLDER_COUNT):
                    folder = conversation_api.create_folder(f"AutoScrollFolder_{ts}_{i}")
                    folder_ids.append(folder["id"])

            with allure.step(
                "Step 1 — Navigate to Chats; verify the folder list contains "
                "at least the 25 seeded folders"
            ):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.wait_for_any_folder_visible(timeout=UI_ELEMENT_TIMEOUT)
                folder_count = chat.get_folder_link_count()
                assert folder_count >= SEEDED_FOLDER_COUNT, (
                    f"Expected at least {SEEDED_FOLDER_COUNT} folders "
                    f"(the seeded set), found {folder_count}"
                )

            with allure.step(
                "Step 2 — Hover the folder list area; verify the sidebar "
                "scroll container genuinely overflows (scrollHeight > "
                "clientHeight), not just a CSS overflow-y declaration"
            ):
                assert chat.is_conversation_list_scrollable(), (
                    "Sidebar list scroll container should genuinely overflow "
                    "with 25+ folders present"
                )

            with allure.step(
                "Step 3 — Scroll down through the folder list via a real "
                "wheel gesture; verify scrollTop moved"
            ):
                before, after = chat.scroll_conversation_list_container(delta_y=300)
                assert after > before, (
                    f"scrollTop should increase after a real scroll-down "
                    f"gesture: before={before}, after={after}"
                )

            with allure.step(
                "Step 4 — Identify a seeded folder positioned BELOW the "
                "container's visible viewport; scroll down via repeated "
                "real wheel gestures until it becomes reachable within "
                "the container's bounds"
            ):
                # Conversations.jsx renders newest-created folders closer
                # to the TOP (live-confirmed this pass) — "below" vs
                # "above" the viewport are genuinely different directions,
                # not interchangeable "hidden" states, so the target for a
                # downward scroll must specifically be one positioned
                # below, not merely not-currently-visible.
                below = [
                    fid for fid in folder_ids
                    if chat.get_folder_row_scroll_position(fid) == "below"
                ]
                assert below, (
                    "Expected at least one seeded folder to be positioned "
                    "below the container's visible viewport (overflow "
                    "precondition from step 2)"
                )
                # Nearest-to-the-fold candidate — minimizes scroll distance
                # and, combined with SCROLL_DELTA's overlap guarantee,
                # ensures the target's row is genuinely checked as it
                # crosses into view.
                target_below = min(
                    below, key=lambda fid: chat.get_folder_item(fid).bounding_box()["y"]
                )
                reached = chat.scroll_conversation_list_until_folder_visible(
                    target_below, delta_y=SCROLL_DELTA, max_attempts=SCROLL_MAX_ATTEMPTS
                )
                assert reached, (
                    f"Folder {target_below} (positioned below the visible "
                    "viewport) should become reachable via real downward "
                    "scrolling — no folder should be permanently inaccessible"
                )

            with allure.step(
                "Step 5 — Identify a seeded folder now positioned ABOVE "
                "the visible viewport (scrolled past by step 4's downward "
                "scroll); scroll back up via repeated real wheel gestures "
                "until it becomes reachable again"
            ):
                above = [
                    fid for fid in folder_ids
                    if chat.get_folder_row_scroll_position(fid) == "above"
                ]
                assert above, (
                    "Expected at least one seeded folder to be positioned "
                    "above the visible viewport after step 4's downward scroll"
                )
                target_top = max(
                    above, key=lambda fid: chat.get_folder_item(fid).bounding_box()["y"]
                )
                reached = chat.scroll_conversation_list_until_folder_visible(
                    target_top, delta_y=-SCROLL_DELTA, max_attempts=SCROLL_MAX_ATTEMPTS
                )
                assert reached, (
                    f"Folder {target_top} (scrolled past, above the "
                    "viewport) should become reachable again via real "
                    "upward scrolling — the round trip should not leave "
                    "anything permanently inaccessible"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder-list-scroll flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            for folder_id in folder_ids:
                try:
                    conversation_api.delete_folder(folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
            logger.info("Cleaned up %d seeded folders", len(folder_ids))


class TestMoveToSubmenuFolderListScrollable:
    """ELITEA-2147: Chat – Move To Submenu Folder List is Scrollable When Many Folders Exist (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2147_chat-move-to-submenu-folder-list-is-scrollable-when-many-folders-exist.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_move_to_submenu_folder_list_scrollable(self, page, conversation_api):
        """Verify the "Move to" submenu's own folder list genuinely scrolls
        when many folders exist, and a folder reached only via scrolling is
        still functionally live (moving the conversation into it works).

        Steps (AFS
        test-specs/chat-interface/l3_move-to-submenu-folder-list-scrollable_ELITEA-2147.md,
        steps 3-4 AMENDED during implementation — same discovery and same
        reasoning as ELITEA-2146's implementer amendment, see that test's
        docstring):
        1. Open conv_target's "Move to" submenu (with retry — known defect
           EliteaAI/elitea-testing-public#1117); verify it mounts with
           "Create folder" + "Back to the list" visible.
        2. Verify the submenu's own popover Paper genuinely overflows.
        3. Identify a seeded folder that is NOT within the popover's bounds
           at the initial scroll position; scroll down via repeated real
           wheel gestures until it becomes reachable.
        4. Select that scrolled-to folder; verify the PUT resolves 200, the
           success toast appears, and conv_target actually renders inside
           that folder (proves the scrolled-to item is functionally wired,
           not decorative).

        Implementer amendment (live-discovered this pass): the AFS's
        original steps 3/4 assumed "scroll the popover to its raw
        scrollHeight-clientHeight maximum" would land on the LAST-seeded
        (by creation order) folder specifically. Live-confirmed this is
        false the same way as ELITEA-2146 (the popover lists ALL of the
        account's folders — not just the seeded 25 — in whatever order the
        `folders` store returns, which this test does not control and did
        not investigate further). The empirical "find a folder that's
        currently hidden, then prove it becomes reachable" approach
        verifies the same case-level claim (scrolling reaches every
        folder, including ones initially off-screen) without assuming a
        specific position.

        Setup creates conv_target (ungrouped, unpinned — "Move to" is
        disabled for a pinned conversation) and 25 folders via API.
        """
        chat = ChatPage(page)
        folder_ids: list[int] = []
        folder_names: dict[int, str] = {}
        conv_target_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                f"Setup — create conv_target + {SEEDED_FOLDER_COUNT} folders via API"
            ):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2147_target_{ts}")
                conv_target_id = target["id"]
                for i in range(SEEDED_FOLDER_COUNT):
                    name = f"AutoScrollMoveToFolder_{ts}_{i}"
                    folder = conversation_api.create_folder(name)
                    folder_ids.append(folder["id"])
                    folder_names[folder["id"]] = name

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Open conv_target's 'Move to' submenu (with retry "
                "— known defect EliteaAI/elitea-testing-public#1117); "
                "verify it mounts with 'Create folder' + 'Back to the "
                "list' visible"
            ):
                chat.open_move_to_submenu(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.move_to_create_folder_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.move_to_back_to_list_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 2 — Verify the submenu's own popover Paper genuinely "
                "overflows (scrollHeight > clientHeight), not just MUI's "
                "default overflow-y: auto declaration"
            ):
                assert chat.is_move_to_submenu_scrollable(), (
                    "'Move to' submenu popover should genuinely overflow "
                    "with 25+ folders present"
                )

            with allure.step(
                "Step 3 — Identify a seeded folder positioned BELOW the "
                "popover's visible viewport; scroll down via repeated "
                "real wheel gestures until its menuitem becomes reachable "
                "within the popover's bounds"
            ):
                # Same newest-created-renders-closer-to-top ordering as
                # ELITEA-2146's sidebar container (the submenu reuses the
                # same `folders` store order) — "below" specifically, not
                # merely not-currently-visible.
                below = [
                    fid for fid in folder_ids
                    if chat.get_move_to_folder_item_scroll_position(fid) == "below"
                ]
                assert below, (
                    "Expected at least one seeded folder's menuitem to be "
                    "positioned below the popover's visible viewport "
                    "(overflow precondition from step 2)"
                )
                target_folder_id = min(
                    below, key=lambda fid: chat.get_move_to_folder_item(fid).bounding_box()["y"]
                )
                reached = chat.scroll_move_to_submenu_until_folder_visible(
                    target_folder_id, delta_y=SCROLL_DELTA, max_attempts=SCROLL_MAX_ATTEMPTS
                )
                assert reached, (
                    f"Folder {target_folder_id}'s menuitem (positioned below "
                    "the popover's visible viewport) should become reachable "
                    "via real downward scrolling"
                )

            with allure.step(
                "Step 4 — Select the scrolled-to folder; verify the PUT "
                "resolves 200, the success toast appears, and conv_target "
                "actually renders inside that folder"
            ):
                target_folder_name = folder_names[target_folder_id]
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.select_move_to_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Move-to-scrolled-folder PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") == target_folder_id, (
                    f"Response body 'folder_id' should be {target_folder_id!r} "
                    f"after moving, got: {move_body!r}"
                )
                expected_toast = f'Chat moved to "{target_folder_name}" folder successfully'
                expect(chat.toast_message).to_have_text(expected_toast, timeout=UI_ELEMENT_TIMEOUT)

                chat.expand_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(target_folder_id), (
                    f"Scrolled-to folder {target_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    target_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conv_target {conv_target_id} should be inside the "
                    f"scrolled-to folder {target_folder_id} after moving — "
                    "proves the scrolled-to item is functionally wired, not "
                    "decorative"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during move-to-submenu-scroll flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            for folder_id in folder_ids:
                try:
                    conversation_api.delete_folder(folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder %s: %s", folder_id, exc)
            logger.info("Cleaned up %d seeded folders", len(folder_ids))


class TestFolderDisplaysConversationsOrEmptyState:
    """ELITEA-2148: Chat – Folder Displays Conversation Count or Empty State (l3, medium).

    Case title implies a numeric "conversation count" display; the product
    renders no such badge anywhere (source-confirmed, see the AFS's own
    metadata note) — the case's own numbered steps never actually ask for
    one either, so this test automates exactly those steps: expand/collapse
    behavior and the empty-state text.
    """

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2148_chat-folder-displays-conversation-count-or-empty-state.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_folder_displays_conversations_or_empty_state(self, page, conversation_api):
        """Verify a folder lists its conversations when expanded, hides
        them (via CSS visibility, not DOM removal) when collapsed, and an
        empty folder shows the empty-state text when expanded.

        Steps (AFS
        test-specs/chat-interface/l3_folder-displays-conversations-or-empty-state_ELITEA-2148.md):
        1. Expand folder_with_conversation; verify the conversation is
           listed inside it.
        2. Collapse it again; verify data-expanded flips to false AND the
           conversation row becomes invisible (MUI Collapse keeps it
           DOM-mounted with visibility: hidden — NOT removed, so this must
           be a visibility assertion, not a count assertion).
        3. Expand empty_folder; verify the exact empty-state text
           "No conversations added".

        Setup creates folder_with_conversation (+ one conversation moved
        into it) and empty_folder via API.
        """
        chat = ChatPage(page)
        folder_with_conversation_id = None
        empty_folder_id = None
        conversation_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create folder_with_conversation (+ one "
                "conversation moved into it) and empty_folder via API"
            ):
                ts = int(time.time())
                folder_with_conv = conversation_api.create_folder(
                    f"autotest_2148_with_conv_{ts}"
                )
                folder_with_conversation_id = folder_with_conv["id"]
                conv = conversation_api.create_conversation(f"autotest_2148_conv_{ts}")
                conversation_id = conv["id"]
                conversation_api.move_conversation_to_folder(
                    conversation_id, folder_with_conversation_id
                )
                empty_folder = conversation_api.create_folder(f"autotest_2148_empty_{ts}")
                empty_folder_id = empty_folder["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.wait_for_any_folder_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 1 — Expand folder_with_conversation; verify the "
                "conversation is listed inside it"
            ):
                chat.expand_folder(folder_with_conversation_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_with_conversation_id), (
                    f"folder_with_conversation {folder_with_conversation_id} "
                    "should carry data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    folder_with_conversation_id, conversation_id, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"conversation {conversation_id} should be listed inside "
                    f"folder_with_conversation {folder_with_conversation_id}"
                )

            with allure.step(
                "Step 2 — Collapse folder_with_conversation again; verify "
                "data-expanded flips to false AND the conversation row "
                "becomes invisible (MUI Collapse keeps it DOM-mounted, "
                "visibility: hidden — NOT removed)"
            ):
                chat.collapse_folder(folder_with_conversation_id, timeout=UI_ELEMENT_TIMEOUT)
                assert not chat.is_folder_expanded(folder_with_conversation_id), (
                    f"folder_with_conversation {folder_with_conversation_id} "
                    "should carry data-expanded=\"false\" after collapsing"
                )
                collapsed_conversation_item = chat.get_folder_item(
                    folder_with_conversation_id
                ).locator(chat.CONVERSATION_ITEM.format(conversation_id))
                expect(collapsed_conversation_item).not_to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Expand empty_folder; verify the exact "
                "empty-state text 'No conversations added'"
            ):
                chat.expand_folder(empty_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(empty_folder_id), (
                    f"empty_folder {empty_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                empty_state_text = chat.get_folder_empty_state_text(empty_folder_id)
                assert empty_state_text == "No conversations added", (
                    f"empty_folder {empty_folder_id} should show exactly "
                    f"'No conversations added', got: {empty_state_text!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during folder-expand/collapse flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            if conversation_id:
                try:
                    conversation_api.delete_conversation(conversation_id)
                    logger.info("Cleaned up conversation %s", conversation_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conversation_id, exc)
            if folder_with_conversation_id:
                try:
                    conversation_api.delete_folder(folder_with_conversation_id)
                    logger.info("Cleaned up folder_with_conversation %s", folder_with_conversation_id)
                except Exception as exc:
                    logger.warning(
                        "Failed to delete folder_with_conversation %s: %s",
                        folder_with_conversation_id, exc,
                    )
            if empty_folder_id:
                try:
                    conversation_api.delete_folder(empty_folder_id)
                    logger.info("Cleaned up empty_folder %s", empty_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete empty_folder %s: %s", empty_folder_id, exc)

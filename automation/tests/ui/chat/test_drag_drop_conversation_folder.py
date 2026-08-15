"""UI Tests for ELITEA-2142/2143/2145 — Chat: Drag-and-Drop Conversation <-> Folder.

Three cases sharing the SAME drag-and-drop surface (``surface_key:
chat-conversation-drag-drop``, ``@dnd-kit/core``'s ``PointerSensor`` —
``DraggableConversationItem.jsx`` / ``DroppableFolderItem.jsx`` /
``DroppableGroupedArea.jsx``, all logic in
``src/hooks/chat/useDragAndDrop.js``), cluster-analysed alongside ELITEA-2144
(folder-to-folder move, NOT in this PR — a separate dispatch), kept as
separate test methods per the AFS's own "differ in steps -> separate AFS/
test" rule (they were NOT analysed as a family — three distinct AFS files):

- ELITEA-2142 — drag a Today-section conversation onto a folder.
- ELITEA-2143 — the hover-highlight (dashed border,
  ``data-drop-active``) shown while hovering a candidate folder mid-drag.
- ELITEA-2145 — drag a conversation OUT of a folder, back to the general list.

Specs:
- test-specs/chat-interface/l3_drag-drop-conversation-to-folder_ELITEA-2142.md
- test-specs/chat-interface/l3_drag-drop-conversation-highlights-target-folder-on-hover_ELITEA-2143.md
- test-specs/chat-interface/l3_drag-drop-conversation-back-to-general-list_ELITEA-2145.md

Real Playwright mouse gestures drive the real product code — no substitution
(confirmed live via network capture during analysis, ``_surface.md`` §
ELITEA-2142/2143/2144/2145). Two new testids were added this implementation
(``chat-folder-drop-zone-{folder_id}`` + ``data-drop-active`` on
``DroppableFolderItem.jsx``, ``chat-conversation-list-drop-zone`` +
``data-drop-active`` on ``DroppableGroupedArea.jsx`` — both pure attribute
additions on an already-rendered ``ref={setNodeRef}`` Box, zero new DOM
nodes) — see ``ChatPage.FOLDER_DROP_ZONE`` /
``ChatPage.conversation_list_drop_zone``.

Two product defects were originally filed during this cluster's analysis;
BOTH build-time checks this implementation owed came back clean (neither
weakens any assertion in this file):
- elitea-testing-public#1542 — claimed a single-conversation drag-and-drop
  move never shows a success toast. **CORRECTED this implementation** (see
  ``test_drag_drop_conversation_to_folder``'s own docstring): the analyst's
  source read missed that the shared ``onMoveToFolderConversation`` mutation
  hook (used by BOTH the drag-drop and "Move to" menu flows) fires its own
  toast unconditionally. Live-confirmed the toast DOES show for a
  single-item drag. Step 6 hard-asserts its presence + exact text; #1542 was
  corrected via a comment on the issue (left open — human disposition).
- elitea-testing-public#1541 — dragging OUT of one folder and dropping onto
  ANOTHER folder lands the conversation ungrouped instead (confirmed on
  ELITEA-2144's own scenario, a SEPARATE dispatch, not in this PR).
  ELITEA-2142's own Today->folder direction was flagged as an explicit
  build-time risk by its AFS (same ``handleDragEnd`` code path, not
  independently pristine-confirmed live during analysis due to
  viewport/scroll obstacles) — build-time result: does NOT reproduce for
  this direction (the PUT resolved with the correct `folder_id`), so this
  direction is asserted as the case's literal expected behavior.
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
DRAG_ITERATIONS = 4
DRAG_STEPS_PER_MOVE = 4


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    A ``403 Forbidden`` on ``GET .../secrets/secrets/default/{project_id}``
    fires on every page load in this local environment regardless of any
    action taken — unrelated to the drag-and-drop flow. Same idiom as the
    sibling chat tests' equivalent filter
    (``test_move_conversation_to_folder.py``).
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


class TestDragDropConversationToFolder:
    """ELITEA-2142: Chat – Drag and Drop Conversation to a Folder (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2142_chat-drag-and-drop-conversation-to-a-folder.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_drag_drop_conversation_to_folder(self, page, conversation_api):
        """Drag a Today-section conversation onto a folder and drop it.

        Steps (AFS
        test-specs/chat-interface/l3_drag-drop-conversation-to-folder_ELITEA-2142.md):
        1. Verify conv_target is visible under Today and target_folder is visible.
        2. Press-and-hold + move toward target_folder; verify the drag activates.
        3. Drop onto target_folder; verify the PUT resolves 200 with the
           new folder_id.
        4. Verify conv_target no longer renders under any date-group heading.
        5. Expand target_folder and verify conv_target is inside it.
        6. Verify a success toast confirms the move.

        Setup creates conv_target + target_folder via API — real setup, not
        the tested action (the drag-and-drop gesture itself is).

        Build-time check this AFS owes (§ Automation Hints): the
        Today->folder direction was not independently pristine-confirmed
        live during analysis (viewport/scroll obstacles), flagged as a real
        risk of hitting the SAME #1541 drop-target-misresolution defect
        confirmed on the sibling folder-to-folder scenario (identical
        ``handleDragEnd`` code path). Live-confirmed clean during this
        implementation: the PUT resolved with ``folder_id`` correctly set
        to ``target_folder``'s own id, not null/ungrouped — this direction
        does NOT reproduce #1541, so steps 3-5 assert the case's literal
        expected behavior (not soft-asserted, not tied to #1541).

        AFS AMENDMENT (implementer exploration, this PR): step 6 was
        originally speced as a soft-assert of toast ABSENCE tied to a filed
        defect, #1542 ("no toast for a single-item drag move"). Reading
        ``useMoveToFolderConversation.hooks.js`` (NOT just
        ``useDragAndDrop.js``, which is where the analyst's source-confirmed
        claim stopped) shows the shared ``onMoveToFolderConversation`` mutation
        hook — used by BOTH the drag-drop and "Move to" menu flows — fires
        its own success toast unconditionally, independent of the
        `useDragAndDrop.js`-local, item-count-gated aggregate toast the
        analyst read. Live-confirmed via a standalone script (headless
        Chromium, real API-seeded conversation+folder, real drag gesture):
        the toast DOES appear with the exact "Move to" menu text
        (``Chat moved to "<folder>" folder successfully``). #1542 does not
        reproduce; corrected via a comment on the issue (left OPEN — human
        disposition, not closed by this implementation). Step 6 below is a
        normal hard assertion, matching the case's literal expected result.
        """
        chat = ChatPage(page)
        conv_target_id = None
        target_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create conv_target + target_folder via API; navigate to chat"
            ):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2142_target_{ts}")
                conv_target_id = target["id"]
                folder = conversation_api.create_folder(f"autotest_2142_folder_{ts}")
                target_folder_id = folder["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Verify conv_target is visible under Today and "
                "target_folder is visible in the folder list"
            ):
                assert chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should render under Today"
                expect(chat.get_folder_item(target_folder_id)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 2 — Press and hold on conv_target, move toward "
                "target_folder in incremental steps; verify the drag activates"
            ):
                chat.start_conversation_drag(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.wait_for_conversation_dragging(
                    conv_target_id, expected=True, timeout=1_000,
                ), f"conv_target {conv_target_id} should show the dragging opacity (0.5) once activated"
                chat.move_drag_over_target(
                    chat.get_folder_item(target_folder_id),
                    iterations=DRAG_ITERATIONS,
                    steps_per_move=DRAG_STEPS_PER_MOVE,
                )

            with allure.step(
                "Step 3 — Drop onto target_folder; verify the PUT resolves "
                "200 with the new folder_id (build-time #1541 check: "
                "confirmed clean for this direction, see docstring)"
            ):
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.release_drag(timeout=NAVIGATION_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Drag-drop-to-folder PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") == target_folder_id, (
                    f"Response body 'folder_id' should be {target_folder_id!r} "
                    f"after the drag-and-drop move, got: {move_body!r}"
                )
                # Captured HERE (not in step 6, where the case lists it) —
                # implementer technique adjustment, not a scope change: the
                # toast auto-dismisses after a few seconds, and steps 4-5
                # (date-group removal check + folder-expand) take long
                # enough to run that the toast is gone by the time a step-6
                # read would fire (live-confirmed this implementation —
                # "element(s) not found" on the first attempt). The captured
                # text is asserted below at step 6, matching the case's own
                # step order for the ASSERTION even though the DOM read
                # happens right after the action it confirms, same idiom as
                # ``test_move_conversation_to_folder.py``'s toast checks.
                toast_text_at_drop = chat.get_toast_text(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 4 — Verify conv_target is no longer rendered under "
                "any date-group heading (SCOPED 0-count — MUI Collapse "
                "keeps a collapsed folder's children DOM-mounted)"
            ):
                assert not chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=3_000,
                ), f"conv_target {conv_target_id} should no longer render under Today after the move"

            with allure.step(
                "Step 5 — Expand target_folder and verify conv_target is inside it"
            ):
                chat.expand_folder(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(target_folder_id), (
                    f"target_folder {target_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    target_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should be inside target_folder {target_folder_id}"

            with allure.step(
                "Step 6 — Verify a success toast confirmed the move "
                "(AMENDED — #1542 does NOT reproduce: the shared "
                "onMoveToFolderConversation mutation hook fires its own "
                "toast unconditionally, independent of useDragAndDrop.js's "
                "gated multi-select aggregate toast the analyst read; text "
                "captured at drop time — step 3 — since the toast "
                "auto-dismisses before steps 4-5 finish running)"
            ):
                assert toast_text_at_drop == f'Chat moved to "{folder["name"]}" folder successfully', (
                    f"Success toast text should confirm the move to {folder['name']!r}, "
                    f"got: {toast_text_at_drop!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during drag-drop-to-folder flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            chat.abort_drag()
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if target_folder_id:
                try:
                    chat.delete_folder_via_menu(target_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up target_folder %s", target_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete target_folder %s: %s", target_folder_id, exc)


class TestDragDropHighlightsTargetFolderOnHover:
    """ELITEA-2143: Chat – Drag and Drop Conversation Highlights Target Folder on Hover (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2143_chat-drag-and-drop-conversation-highlights-target-folder-on-hover.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_drag_drop_highlights_target_folder_on_hover(self, page, conversation_api):
        """Verify the dashed-border hover-highlight while dragging over folders.

        Steps (AFS
        test-specs/chat-interface/l3_drag-drop-conversation-highlights-target-folder-on-hover_ELITEA-2143.md):
        1. Begin dragging conv_target; verify the drag activates.
        2. Drag over folder_a; verify its drop-zone shows data-drop-active=true.
        3. Move toward folder_b; verify folder_a's highlight is removed AND
           folder_b's highlight appears.
        4. Drop on folder_b; verify the highlight disappears, the drag
           ends, the PUT resolves 200 with ``folder_id`` == folder_b's own
           id, and folder_b actually contains conv_target afterwards.

        No defect found for this case's own hover-highlight assertion —
        the mechanism is confirmed working correctly.

        AFS AMENDMENT (fix round 1, review finding): the original AFS
        marked the drop OUTCOME (does the conversation actually land in
        folder_b) out-of-scope, deferring it to ELITEA-2144 — but ELITEA-2144
        is a separate dispatch, not part of this PR/batch, and this case's
        OWN TMS Pass/Fail criteria explicitly requires it ("Pass: ... drop
        moves conversation" / "Fail: ... drop does not move conversation").
        Step 4 now hard-asserts the response body's ``folder_id`` and
        confirms conv_target renders inside folder_b via the UI (same
        pattern as ``test_drag_drop_conversation_to_folder`` steps 3/5).
        This is the SAME Today->folder direction confirmed clean of the
        #1541 drop-target-misresolution defect in
        ``test_drag_drop_conversation_to_folder`` (conv_target here is
        dragged straight from Today, never having been inside folder_a —
        only hovered — so the drop is a Today->folder_b move, not a
        folder-to-folder move); asserted as literal expected behavior, not
        soft-asserted or tied to any known defect. The AFS's own Coverage
        Map row 4 and Concrete-Handles framing are amended accordingly (see
        the AFS file).
        """
        chat = ChatPage(page)
        conv_target_id = None
        folder_a_id = None
        folder_b_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create conv_target + folder_a + folder_b via API; navigate to chat"
            ):
                ts = int(time.time())
                target = conversation_api.create_conversation(f"autotest_2143_target_{ts}")
                conv_target_id = target["id"]
                fa = conversation_api.create_folder(f"autotest_2143_a_{ts}")
                folder_a_id = fa["id"]
                fb = conversation_api.create_folder(f"autotest_2143_b_{ts}")
                folder_b_id = fb["id"]

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Begin dragging conv_target; verify the drag activates"
            ):
                chat.start_conversation_drag(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.wait_for_conversation_dragging(
                    conv_target_id, expected=True, timeout=1_000,
                ), f"conv_target {conv_target_id} should show the dragging opacity (0.5) once activated"

            with allure.step(
                "Step 2 — Drag over folder_a; verify its drop-zone shows data-drop-active=true"
            ):
                chat.move_drag_over_target(
                    chat.get_folder_item(folder_a_id),
                    iterations=DRAG_ITERATIONS,
                    steps_per_move=DRAG_STEPS_PER_MOVE,
                )
                expect(chat.get_folder_drop_zone(folder_a_id)).to_have_attribute(
                    "data-drop-active", "true", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Move away from folder_a toward folder_b; verify "
                "folder_a's highlight is removed AND folder_b's appears"
            ):
                chat.move_drag_over_target(
                    chat.get_folder_item(folder_b_id),
                    iterations=DRAG_ITERATIONS,
                    steps_per_move=DRAG_STEPS_PER_MOVE,
                )
                expect(chat.get_folder_drop_zone(folder_a_id)).to_have_attribute(
                    "data-drop-active", "false", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(chat.get_folder_drop_zone(folder_b_id)).to_have_attribute(
                    "data-drop-active", "true", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 4 — Drop the conversation on folder_b; verify the "
                "highlight disappears (drag ends), the PUT fires with "
                "folder_id resolving to folder_b, and folder_b actually "
                "contains conv_target afterwards (case Pass/Fail criteria: "
                "'drop moves conversation' / 'Fail: ... drop does not move "
                "conversation' — see docstring, fix-round amendment)"
            ):
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.release_drag(timeout=NAVIGATION_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    f"Drop PUT should resolve 200, got {move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") == folder_b_id, (
                    f"Response body 'folder_id' should be {folder_b_id!r} after "
                    f"dropping on folder_b, got: {move_body!r}"
                )
                expect(chat.get_folder_drop_zone(folder_b_id)).to_have_attribute(
                    "data-drop-active", "false", timeout=UI_ELEMENT_TIMEOUT
                )
                assert chat.wait_for_conversation_dragging(
                    conv_target_id, expected=False, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should no longer show the dragging opacity after drop"
                chat.expand_folder(folder_b_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(folder_b_id), (
                    f"folder_b {folder_b_id} should carry data-expanded=\"true\" "
                    "after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    folder_b_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should be inside folder_b {folder_b_id} after the drop"

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during hover-highlight flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            chat.abort_drag()
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if folder_a_id:
                try:
                    chat.delete_folder_via_menu(folder_a_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder_a %s", folder_a_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_a %s: %s", folder_a_id, exc)
            if folder_b_id:
                try:
                    chat.delete_folder_via_menu(folder_b_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up folder_b %s", folder_b_id)
                except Exception as exc:
                    logger.warning("Failed to delete folder_b %s: %s", folder_b_id, exc)


class TestDragDropConversationBackToGeneralList:
    """ELITEA-2145: Chat – Drag and Drop Conversation Back to the General List (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2145_chat-drag-and-drop-conversation-back-to-the-general-list.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_drag_drop_conversation_back_to_general_list(self, page, conversation_api):
        """Drag a conversation OUT of a folder, back to the general list.

        Steps (AFS
        test-specs/chat-interface/l3_drag-drop-conversation-back-to-general-list_ELITEA-2145.md):
        1. Expand source_folder; verify conv_target is inside it.
        2. Press and hold, drag toward the general-list area; verify the
           ungrouped drop-zone shows data-drop-active=true while hovered
           (the ``chat-conversation-list-drop-zone`` testid landed as part
           of this implementation — see docstring below — so the AFS's own
           "if it has landed, assert it" branch applies; the case's own
           wording is an OR with "accepts drop", not a hard requirement,
           but the mechanism is confirmed working, so it is asserted).
        3. Drop into the general list; verify the PUT resolves 200 with
           folder_id: null.
        4. Verify conv_target renders in Today (scoped 1-count).
        5. Verify source_folder still exists and conv_target is no longer inside it.

        Setup creates source_folder + conv_target via API, then moves
        conv_target into source_folder via API
        (``conversation_api.move_conversation_to_folder``) — real setup,
        not the tested action.

        Build-time check this AFS owes: this direction was assessed
        LOW RISK but not independently pristine-confirmed live during
        analysis (shared-DEV-account viewport/scroll obstacles kept the
        folder list and the Today section out of simultaneous view for a
        single clean gesture). Live-confirmed clean during this
        implementation: the PUT resolved with folder_id: null and the
        conversation reappeared under Today, matching the low-risk
        assessment — asserted as the case's literal expected behavior, not
        tied to any known defect.
        """
        chat = ChatPage(page)
        conv_target_id = None
        source_folder_id = None

        console_messages = []

        def _on_console(msg):
            if msg.type == "error" and not _is_known_secrets_403(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        try:
            with allure.step(
                "Setup — create source_folder + conv_target via API; move "
                "conv_target into source_folder via API; navigate to chat"
            ):
                ts = int(time.time())
                folder = conversation_api.create_folder(f"autotest_2145_folder_{ts}")
                source_folder_id = folder["id"]
                target = conversation_api.create_conversation(f"autotest_2145_target_{ts}")
                conv_target_id = target["id"]
                conversation_api.move_conversation_to_folder(conv_target_id, source_folder_id)

                chat.navigate_to_chat()
                chat.wait_for_page_load()

            with allure.step(
                "Step 1 — Expand source_folder; verify conv_target is inside it"
            ):
                chat.expand_folder(source_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_folder_expanded(source_folder_id), (
                    f"source_folder {source_folder_id} should carry "
                    "data-expanded=\"true\" after being clicked"
                )
                assert chat.is_conversation_in_folder(
                    source_folder_id, conv_target_id, timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should be inside source_folder {source_folder_id}"

            with allure.step(
                "Step 2 — Press and hold on conv_target, drag toward the "
                "general-list/date-group area; verify the ungrouped "
                "drop-zone shows data-drop-active=true while hovered"
            ):
                chat.start_conversation_drag(conv_target_id, timeout=UI_ELEMENT_TIMEOUT)
                assert chat.wait_for_conversation_dragging(
                    conv_target_id, expected=True, timeout=1_000,
                ), f"conv_target {conv_target_id} should show the dragging opacity (0.5) once activated"
                chat.move_drag_over_target(
                    chat.conversation_list_drop_zone,
                    iterations=DRAG_ITERATIONS,
                    steps_per_move=DRAG_STEPS_PER_MOVE,
                )
                expect(chat.conversation_list_drop_zone).to_have_attribute(
                    "data-drop-active", "true", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 3 — Drop into the general list; verify the PUT "
                "resolves 200 with folder_id: null"
            ):
                with page.expect_response(
                    lambda r: "/conversation/prompt_lib/" in r.url
                    and str(conv_target_id) in r.url
                    and r.request.method == "PUT",
                    timeout=NAVIGATION_TIMEOUT,
                ) as move_response_info:
                    chat.release_drag(timeout=NAVIGATION_TIMEOUT)
                move_response = move_response_info.value
                assert move_response.status == 200, (
                    "Drag-drop-back-to-list PUT should resolve 200, got "
                    f"{move_response.status} for {move_response.url}"
                )
                move_body = move_response.json()
                assert move_body.get("folder_id") is None, (
                    "Response body 'folder_id' should be null after "
                    f"dragging back to the general list, got: {move_body!r}"
                )

            with allure.step(
                "Step 4 — Verify conv_target now renders under Today "
                "(scoped 1-count)"
            ):
                assert chat.is_conversation_in_group(
                    conv_target_id, "today", timeout=UI_ELEMENT_TIMEOUT,
                ), f"conv_target {conv_target_id} should render under Today after moving back"

            with allure.step(
                "Step 5 — Verify source_folder still exists and conv_target "
                "is no longer inside it"
            ):
                expect(chat.get_folder_item(source_folder_id)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert not chat.is_conversation_in_folder(
                    source_folder_id, conv_target_id, timeout=3_000,
                ), (
                    f"conv_target {conv_target_id} should no longer be inside "
                    f"source_folder {source_folder_id} after the move"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the full flow"
            ):
                assert not console_messages, (
                    "Unexpected console errors during drag-back-to-list flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            chat.abort_drag()
            if conv_target_id:
                try:
                    conversation_api.delete_conversation(conv_target_id)
                    logger.info("Cleaned up conversation %s", conv_target_id)
                except Exception as exc:
                    logger.warning("Failed to delete conversation %s: %s", conv_target_id, exc)
            if source_folder_id:
                try:
                    chat.delete_folder_via_menu(source_folder_id, timeout=UI_ELEMENT_TIMEOUT)
                    logger.info("Cleaned up source_folder %s", source_folder_id)
                except Exception as exc:
                    logger.warning("Failed to delete source_folder %s: %s", source_folder_id, exc)

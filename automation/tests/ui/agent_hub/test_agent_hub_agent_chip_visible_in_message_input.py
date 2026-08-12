"""Agent Hub — the composer's active-participant chip shows the agent's
avatar, name, version, and a settings icon in the message-input area
(ELITEA-2362).

Opens the "User Story Creator" (id=172) Catalog agent's detail modal, starts
a chat via "Start Chat", and verifies the composer chip — a DIFFERENT
element from the Participants-panel row covered by ELITEA-2361 — shows the
agent's avatar, name, version chip, and settings button.

Spec: test-specs/agent-hub/l2_agent-hub-agent-chip-visible-in-message-input-with-version-and-settings_ELITEA-2362.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2075/2360)
and ``ChatPage``'s composer helpers (``switch_participant_button``,
``chat_version_selector_trigger``, both pre-existing) as-is. Two page-object
additions were needed: the chip avatar had no testid at all (added
``imgTestId="chat-switch-participant-avatar"`` to ``AgentEditorPanel.jsx``'s
EntityIcon call, on ``automation/testids``) and the settings button's
pre-existing testid (``chat-participant-settings-button``, added during an
unrelated ELITEA-2166 rework) had never been wired into ``ChatPage`` as a
``LocatorDescriptor`` until this case.

Case-text drift (CLARIFICATION, already tracked, not re-filed — AFS §
Known Issues / EliteaAI/elitea-testing-public#1042, which explicitly names
this case's sibling ELITEA-2361 as an affected case with the same drift):
case text "Start conversation" -> live product reads "Start Chat"; case
text's example version "ver-0.1" -> live agent's actual version is
"skills-v3.0". Asserted against the live copy.

Sequenced after ELITEA-2360's own root-cause fix (known defect #1043):
``AgentHubPage.click_start_chat()`` now owns the internal 1s wait before
clicking, so this test calls it exactly as-is with no extra synchronization
at the call site.

Known defect elitea-testing-public#1434 (Montserrat webfont 404) can fire
app-wide on any page render — filtered the same way as
``test_agent_hub_started_conversation_has_agent_as_participant.py``.
"""

import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CATALOG_AGENT_NAME = "User Story Creator"
EXPECTED_AGENT_VERSION = "skills-v3.0"


# Known defect elitea-testing-public#1434 (already filed) — an intermittent
# 404 fetching a Montserrat ``.woff2`` file from Google's Fonts CDN
# (fonts.gstatic.com). NOT tied to this test's own flow: EliteaUI's
# ``index.html`` loads Montserrat via a Google Fonts CSS ``<link>`` tag,
# so the woff2 fetch happens on EVERY page render, app-wide — unrelated to
# the Agent Hub modal or the composer chip this test exercises. See
# ``test_agent_hub_started_conversation_has_agent_as_participant.py`` for
# the full root-cause writeup; same filter idiom applied symmetrically to
# both side-channels below.
def _is_known_1434_montserrat_font_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "fonts.gstatic.com" in location_url and "montserrat" in location_url


def _is_known_1434_montserrat_font_404_response(status: int, url: str) -> bool:
    return status == 404 and "fonts.gstatic.com" in url and "montserrat" in url


class TestAgentHubAgentChipVisibleInMessageInput:
    """ELITEA-2362: Agent Hub — agent chip visible in message input with version and settings (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent_hub/ELITEA-2362_agent-hub-agent-chip-visible-in-message-input-with-version-a.md",
        "onetest-ai Test Case link",
    )
    def test_agent_chip_visible_in_message_input(self, page: Page, _browser_cookies):
        """Starting a conversation from a Catalog agent's detail modal shows the
        composer's active-participant chip with avatar, name, version, and a
        settings icon in the message-input area."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id: int | None = None

        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[tuple[int, str]] = []
        page.on(
            "response",
            lambda resp: failed_responses.append((resp.status, resp.url)) if resp.status >= 400 else None,
        )

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card to open the detail modal"):
                assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                    f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
                )
                # open_agent_by_name() waits on the agent-details GET response —
                # deterministic ready-signal for the modal, but click_start_chat()
                # owns the extra known-defect-#1043 wait internally (below).
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                # Known defect: elitea-testing-public#1434 — see
                # _is_known_1434_montserrat_font_404 docstring above.
                unexpected_errors = [m.text for m in console_errors if not _is_known_1434_montserrat_font_404(m)]
                assert not unexpected_errors, (
                    f"Unexpected console errors while opening the modal: {unexpected_errors}"
                )

            with allure.step(
                'Step 3 — Click "Start Chat" (case text: "Start conversation" — drift, '
                "tracked EliteaAI/elitea-testing-public#1042)"
            ):
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify the new chat is created and the user lands on the Chat page"):
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                # Known defect: elitea-testing-public#1434 — see
                # _is_known_1434_montserrat_font_404_response docstring above.
                unexpected_responses = [
                    (status, url)
                    for status, url in failed_responses
                    if not _is_known_1434_montserrat_font_404_response(status, url)
                ]
                assert not unexpected_responses, f"Unexpected 4xx/5xx responses: {unexpected_responses}"

            with allure.step("Step 5 — Verify the agent chip is visible in the message input area at the bottom"):
                assert chat.is_agent_participant_in_composer(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Composer should show {CATALOG_AGENT_NAME!r} as the active agent participant chip"
                )

            with allure.step("Step 6 — Verify the chip displays the agent avatar/icon"):
                avatar_img = chat.get_switch_participant_avatar(timeout=UI_ELEMENT_TIMEOUT)
                assert avatar_img.count() > 0, "Composer agent chip should display an avatar image"
                assert avatar_img.get_attribute("alt") == "elitea", (
                    "Agent chip avatar image should carry the product's own alt text ('elitea')"
                )

            with allure.step(f"Step 7 — Verify the chip displays the agent name {CATALOG_AGENT_NAME!r}"):
                chip_text = chat.switch_participant_button.text_content() or ""
                assert CATALOG_AGENT_NAME in chip_text, (
                    f"Composer agent chip should display the name {CATALOG_AGENT_NAME!r}, got: {chip_text!r}"
                )

            with allure.step(
                'Step 8 — Verify the chip displays the agent version (case text: "ver-0.1" — drift, '
                "live shows the actual skill version)"
            ):
                assert chat.chat_version_selector_trigger.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Version selector chip should be visible next to the agent chip in the composer"
                )
                version_text = chat.chat_version_selector_trigger.text_content() or ""
                assert EXPECTED_AGENT_VERSION in version_text, (
                    f"Expected version chip to read {EXPECTED_AGENT_VERSION!r}, got: {version_text!r}"
                )

            with allure.step("Step 9 — Verify a settings icon is visible on the agent chip"):
                assert chat.chat_participant_settings_button.is_visible(timeout=UI_ELEMENT_TIMEOUT), (
                    "Composer settings button should be visible alongside the agent chip"
                )

            with allure.step("Side-channel check — zero console errors, zero 4xx/5xx across the whole flow"):
                # Known defect: elitea-testing-public#1434 — see
                # _is_known_1434_montserrat_font_404 docstring above.
                unexpected_errors = [m.text for m in console_errors if not _is_known_1434_montserrat_font_404(m)]
                assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"
                unexpected_responses = [
                    (status, url)
                    for status, url in failed_responses
                    if not _is_known_1434_montserrat_font_404_response(status, url)
                ]
                assert not unexpected_responses, f"Unexpected 4xx/5xx responses: {unexpected_responses}"
        finally:
            console_errors.stop()
            # A conversation may not have been created yet if the flow failed before
            # navigation; only attempt cleanup once a conversation id is on the URL.
            match = re.search(r"/chat/(\d+)", page.url)
            if match:
                conv_id = int(match.group(1))
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception:
                    pass

"""Support Assistant — the widget sends the CURRENT project as its context.

TMS case ELITEA-2424 · AFS
``test-specs/support-assistant/l2_assistant-uses-correct-project-context_ELITEA-2424.md``

Switches the sidebar project selector to two different projects and, for each,
asks the Support Assistant which project the user is working in. Asserts the
outbound ``support_assistant_context`` frame carries that project's id and
name, that it differs from the assistant's own DEPLOYMENT project (the case's
"NOT the internal Support Assistant deployment project" clause), and that the
reply names the same id it was given.

Fidelity: no substitutions. ``page.on("websocket")`` is passive observation of
the frame the PRODUCT sends — nothing is routed, fulfilled, delayed or
rewritten (.agents/testing.md § Fidelity policy). The reply comes from the live
LLM over the real backend; because that producer is nondeterministic, the
captured frame is the ORACLE and the reply is asserted against values read out
of it, never against hand-written strings (.agents/testing.md § How to test a
NONDETERMINISTIC producer).

Two live-product facts this spec is shaped by (both recorded in the AFS):

1. The assistant sometimes resolves the PERSONAL ("Private") project to its
   internal name (``project_user_659``) while the UI label stays "Private" —
   so project identity is asserted on the ID, the name only against the
   captured frame, and the test drives two TEAM projects.
2. The widget's overlay container sits above the project-selector dropdown, so
   a project switch happens with the widget closed — each round starts from a
   fresh page load of ``/settings`` (which is what the case's "navigate to a
   different project" step describes anyway).

Markers:
    - p2 / support_assistant / ui / regression (not smoke — two live LLM round
      trips, ~40-80 s each)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_project_context.py -v
"""

import allure
import pytest
from config import settings
from pages.settings_project_general_page import SettingsProjectGeneralPage
from pages.support_assistant_page import SupportAssistantPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.ui,
    pytest.mark.support_assistant,
    pytest.mark.regression,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# Observed reply latency on this surface: 31-135 s, sampled at 77.0 s twice for
# this very question (surface digest § Assistant context payload, quirk 9).
REPLY_TIMEOUT = 240_000

# Two TEAM projects from config — never the personal project (see module docstring).
PROJECT_A = str(settings.users_team_project_id)
PROJECT_B = str(settings.elitea_team_project_id)

QUESTION = (
    "What project am I currently working in? "
    "What is the project name and project ID?"
)

SETTINGS_PATH = "/settings/project-general"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2424_assistant-uses-correct-project-context.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantProjectContext:
    """ELITEA-2424 — assistant uses the correct project context."""

    def _ask_project_question(self, support_page) -> None:
        """Open the widget on a fresh chat and send the project question."""
        support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
        expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
        support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
        copy_baseline = support_page.get_copy_button_count()
        support_page.send_message_via_testid(QUESTION, timeout=EXPECT_TIMEOUT)
        expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
            QUESTION, timeout=EXPECT_TIMEOUT
        )
        # The copy button renders only on a COMPLETED assistant message, which
        # makes its count the accurate "reply finished" signal — the message
        # item itself mounts instantly with a "Starting up..." placeholder.
        expect(support_page.message_copy_buttons).to_have_count(
            copy_baseline + 1, timeout=REPLY_TIMEOUT
        )

    def test_assistant_uses_current_project_context(self, page):
        """The context frame and the reply follow the selected project."""
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        support_page = SupportAssistantPage(page)
        settings_page = SettingsProjectGeneralPage(page)

        assert PROJECT_A != PROJECT_B, (
            "ELITEA-2424 needs two DIFFERENT projects; config gave "
            f"{PROJECT_A!r} twice"
        )

        # Armed before the first navigation: page.on("websocket") only fires
        # for sockets opened after the listener is attached.
        frames = support_page.capture_sent_socket_frames()

        with allure.step(f"Step 1 — Switch to project {PROJECT_A} and read its name"):
            settings_page.navigate()
            settings_page.switch_project(PROJECT_A)
            expect(settings_page.project_general_section).to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            project_a_name = settings_page.get_selected_project_name()
            assert project_a_name, "Sidebar selector reported no project name"

        with allure.step("Step 2-4 — Ask the Support Assistant which project this is"):
            self._ask_project_question(support_page)

        with allure.step(
            f"Step 5 — The context frame and the reply name project {PROJECT_A}"
        ):
            context_a = support_page.last_assistant_context(frames)
            assert context_a, "No support_predict frame was captured for project A"
            deployment_project_id = support_page.last_enter_room_project_id(frames)

            assert context_a.get("project_id") == int(PROJECT_A), (
                f"Widget sent project_id={context_a.get('project_id')!r}, "
                f"expected the selected project {PROJECT_A}"
            )
            assert context_a.get("project_name") == project_a_name, (
                f"Widget sent project_name={context_a.get('project_name')!r}, "
                f"sidebar shows {project_a_name!r}"
            )
            # The case's "NOT the internal Support Assistant deployment
            # project" clause: chat_enter_room carries the assistant's own
            # deployment project, which must not be what the context reports.
            assert deployment_project_id is not None, (
                "No chat_enter_room frame captured — cannot prove the context "
                "differs from the deployment project"
            )
            assert context_a.get("project_id") != deployment_project_id, (
                "Context project id equals the Support Assistant's deployment "
                f"project ({deployment_project_id})"
            )
            assert context_a.get("current_page") == SETTINGS_PATH, (
                f"Frame captured on {context_a.get('current_page')!r}, "
                f"expected {SETTINGS_PATH!r}"
            )
            # The id in the reply comes from the frame, not from the test.
            reply_a = support_page.get_last_assistant_text()
            assert str(context_a["project_id"]) in reply_a, (
                f"Reply does not name project id {context_a['project_id']}: {reply_a!r}"
            )

        with allure.step(f"Step 6 — Switch to a different project ({PROJECT_B})"):
            # A fresh load closes the widget, whose overlay would otherwise
            # intercept the selector dropdown's option click.
            settings_page.navigate()
            settings_page.switch_project(PROJECT_B)
            project_b_name = settings_page.get_selected_project_name()
            assert project_b_name and project_b_name != project_a_name, (
                f"Project did not change: {project_a_name!r} -> {project_b_name!r}"
            )

        with allure.step("Step 7 — Ask the same question in the new project"):
            self._ask_project_question(support_page)

        with allure.step(
            f"Step 8 — The context followed the switch to project {PROJECT_B}"
        ):
            context_b = support_page.last_assistant_context(frames)
            assert context_b, "No support_predict frame was captured for project B"

            assert context_b.get("project_id") == int(PROJECT_B), (
                f"Widget sent project_id={context_b.get('project_id')!r}, "
                f"expected the selected project {PROJECT_B}"
            )
            assert context_b.get("project_name") == project_b_name, (
                f"Widget sent project_name={context_b.get('project_name')!r}, "
                f"sidebar shows {project_b_name!r}"
            )
            assert context_b.get("project_id") != context_a.get("project_id"), (
                "Context project id did not change after switching projects"
            )
            assert context_b.get("project_id") != support_page.last_enter_room_project_id(
                frames
            ), "Context project id equals the Support Assistant's deployment project"

            reply_b = support_page.get_last_assistant_text()
            assert str(context_b["project_id"]) in reply_b, (
                f"Reply does not name project id {context_b['project_id']}: {reply_b!r}"
            )

        with allure.step("Step 9 — No console errors were raised during the flow"):
            assert not console_errors, f"Console errors: {console_errors}"

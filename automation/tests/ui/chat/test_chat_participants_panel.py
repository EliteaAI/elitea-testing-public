"""UI Tests for Chat Participants Panel — Agent, Pipeline, Toolkit, MCP.

Covers ELITEA-2094: creating a new conversation, adding one participant of
each of the four entity types via the plus-menu (Agents/Pipelines/Toolkits/
MCPs), and verifying the right-sidebar PARTICIPANTS area renders all four as
independent badges with distinct icons and no duplicates, that sending the
first message persists all four, and that a misconfigured MCP participant
shows the warning UI.

Spec: test-specs/chat-interface/l2_add-agent-pipeline-toolkit-mcp-participants-panel_ELITEA-2094.md
TMS case: ELITEA-2094

Scope notes (see AFS for full detail):
  - **KNOWN BLOCKING DEFECT (EliteaAI/elitea-testing-public#684):** sending a
    message once BOTH an Agent (step 2) and a Pipeline (step 3) participant
    are present — required by the case itself — CAN crash the client-side
    navigation to `/chat/{id}`, independent of pipeline health (the fixture
    here is a fresh, valid pipeline, not #684's originally-reported broken
    one). Race-condition-shaped, not a hard 100%: a rapid minimal repro hit
    it 5/5, but this full test's own 5-run sample (all 4 participant types,
    matching elapsed time to Send) hit it 1/5 — more time before Send gives
    the race more chances to resolve harmlessly. Root cause confirmed
    precisely during this implementation and added to the existing #684
    (same crash site, not a duplicate): the pipeline's version-detail fetch
    on Send uses the AGENT's version_id instead of its own, 400s, and
    crashes an unguarded `.meta.icon_meta` read in `ChatBox.jsx`. Step 9's
    conversation-creation assertion is a natural (unmasked) hard failure —
    see its own inline comment — which makes Steps 10-11 unreachable ONLY
    on the runs where it fires. A SECOND, milder symptom of the same
    participant-state fragility also intermittently affects Step 8's
    "already-added entity excluded from its own picker" check (soft-
    asserted, see its own inline comment) — isolated, does not block
    downstream steps. Agent/toolkit misconfiguration sub-cases (case step
    11's general wording) are additionally tracked separately
    (EliteaAI/elitea-testing-public#685), not attempted here.
  - The suite's seeding project (399, "Private") structurally cannot render
    the owner/"Users in this conversation" badge — EliteaUI gates the whole
    Users-badge block on ``!isPrivateProject``
    (``CollapsedPerticapantsList.jsx:87-88``), confirmed live during
    implementation. The owner-badge portion of case steps 9/10 is
    intentionally NOT asserted here — see the AFS § Implementer Phase 2
    finding for the full analysis and follow-up recommendation. Everything
    else provable in project 399 (steps 1-8, 10's 4-entity-badge portion,
    11's MCP sub-case) IS asserted.
  - A healthy remote MCP toolkit (no OAuth required) is a filed, real,
    deterministic product defect (EliteaAI/elitea-testing-public#687) — it is
    ALWAYS falsely flagged as misconfigured ("Server is disconnected!
    Reconnect it to use.") regardless of whether it actually works, because
    the frontend's `remoteMcpLoggedOut` check conflates "no OAuth token
    stored" with "needs login and hasn't logged in" (confirmed by reading
    ``ParticipantStatusRunner.jsx``, and live against 3 independent toolkit
    instances). Step 5's misconfiguration-absence check and Step 8's "mcp"
    duplicate-row-count check are soft-asserted (``expect.soft()``) against
    this defect rather than hard-failed; Step 11's "misconfigured entity
    shows a warning" check still passes (it never depended on distinguishing
    healthy from broken), but its discriminating power is currently
    undermined by #687 — see the AFS's Implementer Phase 2 finding.
"""

import logging
import re

import allure
import pytest
from pages.chat_page import ChatPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p1, pytest.mark.regression]

KNOWN_DEFECT_PIPELINE_CRASH = "github.com/EliteaAI/elitea-testing-public/issues/684"
KNOWN_DEFECT_MCP_FALSE_POSITIVE = "github.com/EliteaAI/elitea-testing-public/issues/687"
# Filed separately from #684 (reviewer finding #2, PR #688 fix-only pass):
# #684's own 2026-07-20T17:03 comment says the picker-exclusion symptom below
# is "Not yet root-caused to a specific line" — correlated with #684's
# Agent+Pipeline trigger condition, but NOT confirmed to share #684's
# precisely-diagnosed version_id-mixup mechanism. #689 is cross-linked to
# #684 as "possibly the same underlying instability, mechanism not yet
# confirmed shared."
KNOWN_DEFECT_PICKER_EXCLUSION = "github.com/EliteaAI/elitea-testing-public/issues/689"

UI_ELEMENT_TIMEOUT = 5000
NAVIGATION_TIMEOUT = 10000
# Freshly-created entities (agent/pipeline/toolkit/MCP, all seeded via API
# right before this test's UI steps) search noticeably slower in the plus-
# menu picker than a broad/generic prefix search (existing single-add tests
# only ever search "autotest_" and take the FIRST match — never a specific
# just-created entity's own full name). Confirmed live: the picker can sit
# on "Loading..." past the default 10s. Give entity-specific searches more
# runway; this is a timing/infrastructure allowance, not a weakened assertion.
ENTITY_SEARCH_TIMEOUT = 20000


class TestChatParticipantsPanel:
    """ELITEA-2094: Add Agent/Pipeline/Toolkit/MCP participants, verify panel."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2094_chat-create-new-conversation-with-agent-toolkit-mcp-and-pipeline-verify-all-particip.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(KNOWN_DEFECT_PIPELINE_CRASH, "Known defect — Agent+Pipeline participants crash Send (blocking)")
    @allure.issue(KNOWN_DEFECT_MCP_FALSE_POSITIVE, "Known defect — healthy MCP falsely shows misconfiguration warning")
    @allure.issue(
        KNOWN_DEFECT_PICKER_EXCLUSION,
        "Known defect — already-added agent picker-exclusion filter intermittently fails "
        "once a Pipeline participant also coexists (correlated with #684, not confirmed shared root cause)",
    )
    @pytest.mark.p1
    def test_add_agent_pipeline_toolkit_mcp_participants_and_verify_panel(
        self,
        page,
        request,
        conversation_api,
        agent_api,
        pipeline_api,
        agent_id,
        artifact_toolkit,
        mcp_toolkit_with_tools,
        mcp_toolkit_misconfigured,
    ):
        """ELITEA-2094: add one Agent/Pipeline/Toolkit/MCP participant each to
        a new conversation, verify the PARTICIPANTS panel renders 4 distinct
        badges with no duplicates, sending the first message persists them,
        and a misconfigured MCP participant shows the warning UI.
        """
        conv_id = None
        pipeline_id = None
        agent_name = agent_api.get_agent(agent_id)["name"]
        toolkit_name = artifact_toolkit["name"]
        mcp_name = mcp_toolkit_with_tools["name"]
        bad_mcp_name = mcp_toolkit_misconfigured["name"]

        # NOT the shared `pipeline_with_llm_id` fixture: it names the pipeline
        # via the exact same `f"autotest_{request.node.name}"[:32]` template
        # as the `agent_id` fixture, which — for THIS test's long node name —
        # produces a BYTE-IDENTICAL display name for the agent and the
        # pipeline. That would make Step 3's "composer button switches to the
        # pipeline's name" assertion vacuous (it'd pass even if the composer
        # never switched, since both names are the same string). A distinct
        # prefix ("autotest_pl_") guarantees the two names differ.
        pipeline_name = f"autotest_pl_{request.node.name}"[:32]
        pipeline = pipeline_api.create_pipeline_with_llm_node(
            name=pipeline_name,
            description=f"Auto-created LLM pipeline for test {request.node.name}",
        )
        pipeline_id = pipeline["id"]
        logger.info("Created LLM pipeline %s (%s)", pipeline_id, pipeline_name)

        try:
            with allure.step('Step 1 — Navigate to Chats and click "+ Chat"'):
                chat = ChatPage(page)
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                assert not chat.any_participants_badge_visible(timeout=1000), (
                    "PARTICIPANTS area should show no badges before any participant is added"
                )

            with allure.step("Step 2 — Add agent, verify AGENTS badge + composer button"):
                chat.add_agent_participant(agent_name[:20], timeout=ENTITY_SEARCH_TIMEOUT)
                assert chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                    "Agents badge should appear after adding an agent participant"
                )
                assert chat.is_agent_participant_in_composer(agent_name), (
                    "Composer's active-participant button should show the agent's name"
                )

            with allure.step("Step 3 — Add pipeline, verify PIPELINES badge + composer button switch"):
                chat.add_pipeline_participant(pipeline_name[:20], timeout=ENTITY_SEARCH_TIMEOUT)
                assert chat.is_participants_badge_visible(section="pipelines", timeout=UI_ELEMENT_TIMEOUT), (
                    "Pipelines badge should appear after adding a pipeline participant"
                )
                # Composer's active-participant slot REPLACES, not adds (Axis 2
                # finding, AFS step-3 note) — now shows the pipeline's name.
                assert chat.is_agent_participant_in_composer(pipeline_name), (
                    "Composer's active-participant button should switch to the pipeline's name"
                )
                # Agents badge is independently additive across sections — persists.
                assert chat.is_participants_badge_visible(section="agents", timeout=UI_ELEMENT_TIMEOUT), (
                    "Agents badge should persist after adding a pipeline participant"
                )

            with allure.step("Step 4 — Add toolkit via toggle, verify TOOLKITS badge"):
                chat.add_toolkit_participant(toolkit_name, timeout=ENTITY_SEARCH_TIMEOUT)
                assert chat.is_participants_badge_visible(section="toolkits", timeout=UI_ELEMENT_TIMEOUT), (
                    "Toolkits badge should appear after adding a toolkit participant"
                )

            with allure.step("Step 5 — Add healthy MCP via toggle, verify MCPS badge (no warning)"):
                chat.add_mcp_participant(mcp_name[:20], timeout=ENTITY_SEARCH_TIMEOUT)
                assert chat.is_participants_badge_visible(section="mcp", timeout=UI_ELEMENT_TIMEOUT), (
                    "MCP badge should appear after adding a healthy MCP participant"
                )
                # Known defect: EliteaAI/elitea-testing-public#687 — a healthy remote
                # MCP toolkit (no OAuth required, freshly synced tools confirmed
                # working against a live, reachable endpoint) is currently ALWAYS
                # falsely flagged as misconfigured. Root cause confirmed live +
                # by reading source (ParticipantStatusRunner.jsx's
                # `remoteMcpLoggedOut` check): it treats "no OAuth token in
                # browser localStorage" as "logged out", with no way to
                # distinguish a no-auth-required MCP server from one that
                # genuinely needs login — reproduced deterministically (8x poll
                # over 8s, no change) on 3 independent toolkit instances,
                # including the environment's own long-standing "Remote Github"
                # fixture. Soft so the rest of the flow (Steps 6-11) still runs —
                # sanctioned-RED exception per .agents/testing.md § Merge gate.
                expect.soft(
                    chat.get_participants_badge_locator(section="mcp"),
                    "Known defect: EliteaAI/elitea-testing-public#687 — a healthy "
                    "MCP participant should NOT trigger the misconfiguration warning",
                ).not_to_have_attribute(
                    "aria-label", re.compile("misconfiguration", re.IGNORECASE), timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step("Step 6 — Verify all four sections visible in PARTICIPANTS"):
                for section in ("agents", "pipelines", "toolkits", "mcp"):
                    assert chat.is_participants_badge_visible(section=section, timeout=UI_ELEMENT_TIMEOUT), (
                        f"{section!r} participants badge should be visible with all 4 entity types added"
                    )

            with allure.step("Step 7 — Verify each participant type has a distinct icon"):
                icon_markup = {
                    section: chat.get_participant_section_icon_markup(section=section, timeout=UI_ELEMENT_TIMEOUT)
                    for section in ("agents", "pipelines", "toolkits", "mcp")
                }
                distinct_icons = set(icon_markup.values())
                assert len(distinct_icons) == len(icon_markup), (
                    f"Each of the 4 participant sections should render a visually distinct icon, "
                    f"got {len(distinct_icons)} distinct out of {len(icon_markup)} sections"
                )

            with allure.step("Step 8 — Verify no duplicate entries (popper row count + picker exclusion)"):
                for section in ("agents", "pipelines", "toolkits"):
                    row_count = chat.get_participant_popper_row_count(section=section, timeout=UI_ELEMENT_TIMEOUT)
                    assert row_count == 1, (
                        f"{section!r} popper should show exactly 1 row for its single added participant, "
                        f"got {row_count}"
                    )
                    # Condition-based close wait (NOT a fixed sleep): the next
                    # loop iteration opens a DIFFERENT section's popper, and
                    # `chat-participants-popper` is the SAME testid for all 4
                    # sections — opening the next one before this one has
                    # fully unmounted (its MUI Grow close-transition) leaves
                    # two elements matching simultaneously, a Playwright
                    # strict-mode violation. Confirmed live during
                    # implementation (diagnostic dump showed both poppers
                    # present at opacity:0 — one entering, one still
                    # exiting). See `close_participants_popover` docstring.
                    chat.close_participants_popover(timeout=UI_ELEMENT_TIMEOUT)

                # "mcp" section soft-asserted separately (NOT in the loop above):
                # known defect EliteaAI/elitea-testing-public#687 (see Step 5) means
                # this MCP participant currently renders via ParticipantItem.jsx's
                # misconfigured/"attention" branch, which emits NO
                # `chat-participant-row-*` testid at all (confirmed live: only a
                # hover-only `chat-participant-remove-button` renders in that
                # branch) — so the row-count reads 0, not 1, for a reason
                # unrelated to duplication. Soft so the picker-exclusion check
                # and Steps 9-11 still run.
                mcp_rows = chat.get_participant_popper_rows_locator(section="mcp", timeout=UI_ELEMENT_TIMEOUT)
                expect.soft(
                    mcp_rows,
                    "Known defect: EliteaAI/elitea-testing-public#687 — 'mcp' popper "
                    "should show exactly 1 row for its single added participant",
                ).to_have_count(1, timeout=UI_ELEMENT_TIMEOUT)
                chat.close_participants_popover(timeout=UI_ELEMENT_TIMEOUT)

                # Stronger duplicate-prevention signal (Axis 2 addition): the
                # already-added agent should be excluded from its own picker.
                # Known defect: EliteaAI/elitea-testing-public#689 (filed
                # separately from #684 — reviewer finding #2, PR #688
                # fix-only pass; cross-linked to #684 as "possibly same
                # underlying instability, mechanism not yet confirmed
                # shared" — #684's own 2026-07-20T17:03 comment says THIS
                # symptom is "Not yet root-caused to a specific line", unlike
                # #684's own precisely-diagnosed version_id-mixup crash, so it
                # does not qualify as sharing #684's confirmed mechanism):
                # isolated live (agent participant only, no pipeline/toolkit/
                # mcp) the exclusion filter works correctly every time; once a
                # Pipeline participant also coexists (required by Step 3), it
                # intermittently fails — and a condition-based poll (added to
                # `get_picker_matching_rows_locator`'s underlying search) does
                # not resolve it, so this is a real state issue, not a timing
                # one this implementation could fix locally. Isolated/soft —
                # the rest of Step 8 (the agents/pipelines/toolkits row-count
                # loop above) and Steps 9-11 are unaffected by this one check
                # failing.
                agent_picker_matches = chat.get_picker_matching_rows_locator(
                    "agents", agent_name[:20], timeout=ENTITY_SEARCH_TIMEOUT
                )
                expect.soft(
                    agent_picker_matches,
                    "Known defect: EliteaAI/elitea-testing-public#689 — already-added "
                    "agent should be excluded from the Agents picker when re-opened",
                ).to_have_count(0, timeout=ENTITY_SEARCH_TIMEOUT)
                chat.close_picker_menu()

            with allure.step('Step 9 — Type "Hi" and Send; verify conversation created'):
                # Known defect: EliteaAI/elitea-testing-public#684 — BLOCKING, not
                # isolated (no expect.soft() candidate: everything downstream, Steps
                # 10-11, depends on a real conversation id the client never
                # receives). Root cause confirmed precisely during this
                # implementation (updated the existing #684 with the evidence,
                # since it's the same ChatBox.jsx crash site, not a duplicate):
                # once BOTH an Agent participant (Step 2) and a Pipeline participant
                # (Step 3) are present — required by the case itself — sending a
                # message makes the pipeline's version-detail fetch use the AGENT's
                # version_id instead of the pipeline's own (confirmed via direct id
                # comparison across 5 independent fresh agent+pipeline pairs: the
                # requested-but-404ing version id was always the OTHER, previously-
                # active participant's version, never the pipeline's own). The
                # resulting 400 feeds an unguarded `versionDetails.meta.icon_meta`
                # read in ChatBox.jsx's onSelectVersion, crashing before the client
                # navigates to `/chat/{id}` — independent of pipeline health (this
                # fixture is a fresh, valid, `create_pipeline_with_llm_node`
                # pipeline, not #684's originally-reported orphaned version
                # record). RACE-CONDITION-SHAPED, not a hard 100%: a rapid minimal
                # repro (agent+pipeline only, Send within ~1s) hit it 5/5, but
                # THIS full test's own 5-run sample (all 4 participant types,
                # more elapsed time before Send) hit it 1/5 — the more time
                # passes before Send, the more likely the race resolves
                # harmlessly first. A conversation IS still created server-side
                # even when it fires (confirmed via
                # `ConversationAPI.list_conversations()` after repro runs) — the
                # client-side navigation itself is what's broken, so a real user
                # sees an unresponsive Send with zero feedback. Left as a natural
                # hard failure (not soft-asserted, not `pytest.fail()`-wrapped)
                # per `.agents/testing.md` § Merge gate's sanctioned-RED
                # exception (single-cause + linked via this comment; see the
                # closed-set variant for how an intermittent-but-fully-diagnosed
                # known defect still qualifies) — this IS the honest signal on
                # the runs where it fires, not a test defect. NOTE: because this
                # can leave `conv_id` unresolved, this test's conversation
                # cleanup below may occasionally no-op, leaking one "New Chat"
                # conversation in project 399 per occurrence — see the AFS's
                # Implementer Phase 5 finding for why no workaround was added.
                #
                # Runtime verification (reviewer finding #1, PR #688 fix-only
                # pass): the assertions below have exactly ONE documented
                # cause today (#684's version_id mixup above), but that alone
                # is not proof a GIVEN failure instance IS that cause — any
                # other navigation failure would raise an identical-looking
                # `to_have_url`/`conv_id` AssertionError and get silently read
                # as "the known #684 defect" by anyone triaging CI. Capture
                # console/pageerror/network signals before Send so a failure
                # can be checked against #684's actual signature (a 400 on
                # .../version/prompt_lib/... and/or the unguarded
                # `icon_meta` TypeError) instead of being taken on faith.
                # NOTE: `page.on("console", ...)` alone — the idiom used
                # elsewhere in this repo (e.g.
                # test_agent_create_button_navigation.py,
                # test_mcp_search_by_name.py) — is NOT sufficient here:
                # empirically verified live (this fix) that an UNCAUGHT
                # exception like #684's `icon_meta` TypeError never reaches
                # the "console" event, only `page.on("pageerror", ...)`
                # does. Both are wired: "console" for the repo's established
                # side-channel idiom (catches any console.error the app
                # itself logs), "pageerror" because it's the event that
                # actually catches this specific crash.
                console_errors: list[str] = []
                page_errors: list[str] = []
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
                )
                page.on("pageerror", lambda exc: page_errors.append(str(exc)))
                version_detail_requests = chat.capture_requests_matching(
                    "version/prompt_lib", method="GET"
                )

                chat.send_message("Hi", use_enter=True)
                try:
                    expect(page).to_have_url(re.compile(r"/chat/\d+"), timeout=NAVIGATION_TIMEOUT)
                    match = re.search(r"/chat/(\d+)", page.url)
                    conv_id = match.group(1) if match else None
                    assert conv_id, "Conversation ID should be resolvable from the URL after Send"
                except AssertionError as exc:
                    # Navigation to /chat/{id} failed. Before this gets read
                    # as "the known #684 defect", verify the captured signals
                    # actually match #684's documented signature — a
                    # non-matching failure is a NEW bug, not #684, and must
                    # surface as one.
                    matches_684_network = any(
                        req["status"] == 400 for req in version_detail_requests
                    )
                    matches_684_typeerror = any("icon_meta" in err for err in page_errors)
                    if matches_684_network or matches_684_typeerror:
                        signature_note = (
                            "MATCHES known #684 signature "
                            f"(network_400={matches_684_network}, "
                            f"icon_meta_typeerror={matches_684_typeerror})"
                        )
                    else:
                        signature_note = (
                            "does NOT match known #684's signature (no 400 on "
                            "version/prompt_lib/... and no icon_meta TypeError "
                            "captured) — investigate as a NEW failure, not #684"
                        )
                    raise AssertionError(
                        f"{exc}\n\nSignature check: {signature_note}. "
                        f"console_errors={console_errors!r} page_errors={page_errors!r} "
                        f"version_detail_requests={version_detail_requests!r}"
                    ) from exc

                chat.wait_for_naming_label_to_resolve()
                chat.wait_for_conversations_to_load(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.get_conversation_link_count() > 0, (
                    "At least one conversation should appear in the sidebar after Send"
                )
                # NOTE: the case's owner/"Users in this conversation" badge sub-
                # assertion is intentionally NOT checked here — confirmed live
                # this project (399, Private) never renders that badge,
                # regardless of participants or message count. See AFS §
                # Implementer Phase 2 finding: private-project owner-badge gap.

            with allure.step("Step 10 — Verify all 4 entity participants remain listed after send"):
                for section in ("agents", "pipelines", "toolkits", "mcp"):
                    assert chat.is_participants_badge_visible(section=section, timeout=UI_ELEMENT_TIMEOUT), (
                        f"{section!r} badge should persist after sending the first message"
                    )

            with allure.step("Step 11 — Add misconfigured MCP, verify warning badge + popper text"):
                chat.add_mcp_participant(bad_mcp_name[:20], timeout=ENTITY_SEARCH_TIMEOUT)
                assert chat.is_participant_section_misconfigured(section="mcp", timeout=UI_ELEMENT_TIMEOUT), (
                    "MCP badge should show the misconfiguration warning once a disconnected MCP is added"
                )
                popper = chat.open_participants_popover(section="mcp", timeout=UI_ELEMENT_TIMEOUT)
                popper_text = (popper.text_content() or "").lower()
                assert "disconnected" in popper_text, (
                    f"MCP popper should show the disconnection warning text, got: {popper_text!r}"
                )
                chat.close_participants_popover(timeout=UI_ELEMENT_TIMEOUT)

        finally:
            if conv_id:
                try:
                    conversation_api.delete_conversation(int(conv_id))
                    logger.info("Deleted conversation %s", conv_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for conversation %s: %s", conv_id, exc)
            if pipeline_id:
                try:
                    pipeline_api.delete_pipeline(pipeline_id)
                    logger.info("Deleted pipeline %s", pipeline_id)
                except Exception as exc:
                    logger.warning("Cleanup failed for pipeline %s: %s", pipeline_id, exc)

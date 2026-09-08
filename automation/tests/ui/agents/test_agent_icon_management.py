"""Agent icon can be changed and persists on the agents list card (ELITEA-1899).

Creates a dedicated, uniquely-named disposable agent (icon state is a
visible, shared-list-affecting mutation — per this project's Hard Rule 10
test-data guidance, a fresh instance per run is load-bearing, not
incidental, same reasoning as the ELITEA-1884/ELITEA-1888 AFS's). Opens the
icon picker from the agent detail page, selects a different default icon,
verifies the header icon updates immediately (no reload), then navigates to
the Agents dashboard and verifies the matching card shows the identical
icon URL.

SANCTIONED RED — known product defect
https://github.com/EliteaAI/elitea-testing-public/issues/2055
-------------------------------------------------------------------------
Since 2026-09-08 the agent header icon no longer updates **in place** after
a picker selection: `EntityIcon.jsx` renders the `<img>` only when
`icon?.url` is truthy, and `replaceApplicationIcon`'s optimistic RTK patch
never reaches the form's formik values — so `agent-form-icon-img` is
*absent from the DOM entirely* (not hidden) until a reload. Persistence
itself is fine: the `PUT .../upload_icon/.../{versionId}` returns 200
`{"updated": true}` and both the header and the list card show the new icon
after a reload. Sampled at +0.3/+1.3/+3.3/+7.3/+15.3 s post-selection: absent
every time, on DEV and on localhost — deterministic, NOT a timing race, so a
longer wait is not a fix.

Handling, per `.agents/testing.md` § Merge gate → *Sanctioned-RED exception*:
the two assertions that observe the immediate (no-reload) header update stay
in place, still asserting the **correct** behaviour, routed through this
spec's `soft_failures` aggregation with a `# Known defect: #2055` marker, so
they flip green the moment the product is fixed. Nothing is deleted,
skipped, or weakened. Every other assertion — the PUT 200, Save-stays-disabled,
and the exact-URL match on the dashboard card, which is the case's real
subject — remains HARD and passes today.

TRANSIT SUBSTITUTION (declared, `.agents/testing.md` § Fidelity policy):
Step 4b performs a `page.reload()` purely to *reach* Steps 5-7 while #2055
is open. It fabricates nothing — every value asserted downstream (the
post-reload header src, the card src) is still produced by the system; the
reload only makes the already-persisted value renderable.

Removing it once #2055 is fixed is NOT a standalone deletion — `persisted_src`
anchors both Step 7's card comparison and Step 4b's immediate-vs-persisted
assertion, so a naive removal is a `NameError`. The paired edit is: re-anchor
Step 7 to `immediate_src`, drop the now-redundant immediate-vs-persisted
assertion, and promote Step 3's/Step 4's soft entries back to hard asserts.

Case's step 5 ("Click Save") is NOT performed literally — the icon change
persists immediately and independently via its own `PUT
.../upload_icon/.../{versionId}` call, decoupled from the agent form's
Save/Discard state (the main Save button stays disabled after an icon-only
change, since the icon field isn't formik-tracked). Asserting a literal
Save click would either no-op harmlessly or, if Save happened to be enabled
from an unrelated pending edit, trigger an unrelated save outside this
case's intent. Filed as a case-text CLARIFICATION (reverse-masking guard),
not a defect: https://github.com/EliteaAI/elitea-testing-public/issues/566

Spec: test-specs/agents/l3_agent-icon-change-persists-on-list-card_ELITEA-1899.md
"""

import uuid

import allure
import pytest

from config import settings
from pages.agent_detail_page import AgentDetailPage
from pages.agents_list_page import AgentsListPage
from utils.console_errors import collect_console_errors

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000

# Sampling window for the "header updates immediately (no reload)" observable.
# Deliberately short: the analyst established the <img> is ABSENT rather than
# late (sampled to +15.3 s, absent every time — AFS § 2026-09-09 Repair), so a
# longer wait would only buy run time, never a different answer. Restore a
# larger value ONLY if #2055's fix turns out to be genuinely asynchronous.
IMMEDIATE_ICON_TIMEOUT = 2000

# A fixed known index (not the picker's implicit default) so the test
# deterministically exercises a *change* rather than re-selecting whatever
# icon a fresh agent happens to start with.
ICON_OPTION_INDEX = 3

KNOWN_DEFECT_2055 = "https://github.com/EliteaAI/elitea-testing-public/issues/2055"


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Mirrors the ELITEA-1884/ELITEA-1888 pattern: uses
    ``reasoning_effort: "none"`` and omits ``temperature`` entirely so agent
    creation does not hit the open #524 defect (`temperature` is not allowed
    together with a `reasoning_effort` other than 'none' on the project's
    reasoning-capable default model, which ``AgentAPI.create_agent()``'s
    convenience payload always sends). This does not "fix" #524 — it simply
    avoids the known-bad combination in this test's own fixture payload.
    """
    return {
        "name": name,
        "description": "Agent for ELITEA-1899 icon change persistence check",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "",
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "none",
                    "model_name": settings.default_model_name,
                    "model_project_id": settings.default_model_project_id,
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


class TestAgentIconManagement:
    """Agent icon can be changed and persists on the agents list card (ELITEA-1899, p3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1899_agent-icon-can-be-changed-and-persists-on-agents-list-card.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    @pytest.mark.regression
    def test_agent_icon_change_persists_on_list_card(self, page, agent_api):
        """Selecting a new icon in the picker updates the header immediately
        and the identical icon persists on the agent's dashboard card.

        Currently SANCTIONED RED on the "immediately" half — open product
        defect #2055 (see module docstring): the header ``<img>`` is not
        rendered until a reload. Those two assertions are soft-aggregated and
        still assert the correct behaviour; everything else is hard and green.
        """
        # Every non-mutating setup statement runs BEFORE the create, so nothing
        # can raise between "the agent exists" and "the try/finally that deletes
        # it is armed" (`.agents/testing.md` § Teardown-guard ordering — the flag
        # goes up before the mutation, never after).
        detail_page = AgentDetailPage(page)
        # URL-annotated capture (utils/console_errors) rather than the
        # hand-rolled `page.on("console", ...)` this spec used to carry — the
        # recurring background-resource noise class in `.agents/testing.md`
        # § Unconfirmed needs the failing resource's URL to be diagnosable.
        # Capture-only: nothing is filtered, no status code is swallowed.
        console_errors = collect_console_errors(page)
        # Terminal failures for the known, isolated product defect #2055 are
        # aggregated here and raised once at the end via pytest.fail(), so a
        # single mechanism owns every soft failure in this spec
        # (`.agents/testing.md` § Merge gate, closed-set variant).
        soft_failures: list[str] = []
        icon_requests = detail_page.capture_requests_matching("upload_icon", method="PUT")

        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1899-icon-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        try:
            with allure.step("Step 1 — Navigate to the agent detail page"):
                detail_page.navigate(agent_id)
                assert detail_page.get_name() == agent_name, (
                    "Agent detail page should show the newly created agent"
                )

            with allure.step(
                "Step 2 — Click the agent icon (hover first) — icon picker opens"
            ):
                # AUTOMATION QUIRK (ELITEA-1899 AFS, not a product defect): the
                # icon's clickable state only mounts once its hover-triggered
                # edit-pencil overlay is rendered — a bare single .click() with
                # no prior .hover() only triggers the hover state and does not
                # open the dialog. open_icon_picker() hovers before clicking.
                detail_page.open_icon_picker(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.icon_picker_dialog.is_visible(), (
                    "Icon picker dialog should be open after hover + click"
                )

            with allure.step("Step 3 — Select a different icon from the picker"):
                previous_src = detail_page.get_header_icon_src(
                    timeout=IMMEDIATE_ICON_TIMEOUT
                )
                new_src = detail_page.select_icon_option(
                    ICON_OPTION_INDEX, timeout=UI_ELEMENT_TIMEOUT
                )
                # Known defect: #2055 — the header <img> is absent from the DOM
                # after a selection until a reload, so this read returns "".
                # Kept asserting the CORRECT behaviour (a changed, non-empty
                # src with no reload) and soft-aggregated, never weakened:
                # it flips green the moment the product is fixed.
                if not new_src or new_src == previous_src:
                    soft_failures.append(
                        f"Known defect {KNOWN_DEFECT_2055}: selecting a different "
                        "icon option should change the header icon src in place "
                        f"(no reload) — before: {previous_src!r}, after: {new_src!r}"
                    )
                # HARD — the mutation itself is honest and passes today; this is
                # the proof the icon really was applied server-side.
                resolved = [r for r in icon_requests if r["status"] is not None]
                assert resolved and resolved[-1]["status"] == 200, (
                    "PUT .../upload_icon/... should return 200 for the icon "
                    f"selection, captured: {icon_requests!r}"
                )

            with allure.step(
                "Step 4 — New icon is shown in the agent header immediately (no reload)"
            ):
                # Known defect: #2055 — same observable as Step 3, re-read after
                # the dialog has fully closed and the network settled (the
                # analyst's +0.3 s .. +15.3 s sampling found it absent at every
                # offset). Soft-aggregated for the same reason.
                immediate_src = detail_page.get_header_icon_src(
                    timeout=IMMEDIATE_ICON_TIMEOUT
                )
                if not immediate_src or immediate_src == previous_src:
                    soft_failures.append(
                        f"Known defect {KNOWN_DEFECT_2055}: the agent header should "
                        "display the newly selected icon with no reload — got "
                        f"{immediate_src!r} (unchanged from {previous_src!r})"
                    )

            with allure.step(
                "Step 4b — TRANSIT (declared, works around #2055): reload so the "
                "already-persisted icon renders, giving Steps 5-7 a real "
                "system-produced reference URL"
            ):
                # Transit substitution per `.agents/testing.md` § Fidelity
                # policy: the reload only REACHES the later steps — the value
                # below is still produced by the system (it is what the backend
                # persisted in Step 3), nothing is fabricated or injected.
                # Plain reload + the page object's own readiness wait rather
                # than BasePage.reload_and_wait(), whose wait_until="networkidle"
                # races the app's persistent Socket.IO polling transport (#1847).
                page.reload()
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                persisted_src = detail_page.get_header_icon_src(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert persisted_src and persisted_src != previous_src, (
                    "After a reload the agent header must show the icon persisted "
                    f"by Step 3's PUT — expected a new non-empty src, got "
                    f"{persisted_src!r} (before the change: {previous_src!r})"
                )
                # Restores the pre-repair immediate-header <-> card link. Guarded on
                # immediate_src being readable, so it never evaluates while #2055 is
                # open and cannot pollute the sanctioned-RED single-cause signature.
                # HARD by design: post-fix, an immediate header icon that differs
                # from the persisted one is a NEW defect (exactly #2055's own
                # broken-optimistic-patch class, rendering the wrong icon rather
                # than none) and must surface as a raw red, never as a member of
                # #2055's closed set.
                if immediate_src:
                    assert immediate_src == persisted_src, (
                        "The icon rendered in the header immediately after selection "
                        f"must be the one that persisted — immediate: {immediate_src!r}, "
                        f"persisted: {persisted_src!r}"
                    )

            with allure.step(
                "Step 5 — CLARIFICATION (issue #566, not a defect): the icon "
                "change already persisted via its own PUT call in Step 3 — "
                "there is no separate 'click Save' action for this field. "
                "The main Save button stays disabled after an icon-only change "
                "since the icon field is not formik-tracked"
            ):
                assert not detail_page.is_save_enabled(), (
                    "Save button should remain disabled after an icon-only "
                    "change — the icon persists independently via its own "
                    "PUT call, not through the form's Save/Discard state"
                )

            with allure.step("Step 6 — Navigate to the Agents dashboard"):
                list_page = AgentsListPage(page)
                list_page.navigate()
                assert list_page.agent_exists_in_list(agent_name), (
                    "Newly-edited agent should appear on the Agents dashboard"
                )

            with allure.step(
                "Step 7 — Agent card shows the newly selected icon (exact src match)"
            ):
                card_src = list_page.get_card_icon_src(agent_name, timeout=UI_ELEMENT_TIMEOUT)
                assert card_src == persisted_src, (
                    "Agent card icon src should exactly match the agent header "
                    f"icon src — expected {persisted_src!r}, got {card_src!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the flow"
            ):
                assert not console_errors, (
                    "Expected no console errors across the icon-change flow, got: "
                    f"{console_errors}"
                )

            # Wrapped so the sanctioned-RED signature attaches to a STEP in the
            # allure report, not merely to the test — the gate reads per-step
            # status across runs when confirming the signature is identical.
            with allure.step(
                "Sanctioned RED — raise the aggregated known-defect #2055 "
                "soft failures (every other assertion above passed)"
            ):
                if soft_failures:
                    pytest.fail(
                        "Soft assertion(s) failed — known isolated product defect "
                        f"{KNOWN_DEFECT_2055}, not test/infrastructure. The icon "
                        "mutation (PUT 200), its persistence after reload, the "
                        "immediate-vs-persisted and Save-stays-disabled checks and "
                        "the exact-URL match on the dashboard card all passed:\n"
                        + "\n".join(soft_failures)
                    )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")

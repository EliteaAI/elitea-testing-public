"""UI test — Context Management / Summarization values persist after autosave + reload.

Family spec covering two TMS cases that are the SAME flow (set field(s) on
Settings -> Memory, blur to trigger the page's autosave, reload, values are
still there) with different field sets:

- **ELITEA-2376** — Max Context Tokens = 32000, Preserve Recent Messages = 10
- **ELITEA-2379** — Summarization Instructions = "Summarize briefly, focus on
  key actions.", Target Summary Tokens = 300

One parameterized test, one row per case, each row asserting its OWN expected
values (never a flattened shared assertion).

AFS: test-specs/settings-user-profile/
l3_context-management-values-persist-after-reload_ELITEA-2376-2379.md

Known case-text vs live-product divergence (not weakened — the live contract
is asserted; EliteaAI/elitea-testing-public#1238): both cases say
"Personalization -> DEFAULT CONTEXT MANAGEMENT / DEFAULT SUMMARIZATION";
`/settings/personalization` 404s and the live route is Settings -> Memory.

Open bug EliteaAI/elitea-testing-public#1129 ("the numeric fields on this page
never autosave when typed; values revert on reload") did **not** reproduce for
any of the four fields during this case's live analysis — including Preserve
Recent Messages, the last field nobody had re-tested. These assertions are
therefore plain hard assertions, deliberately NOT soft-asserted against #1129:
if the bug comes back, this spec is exactly the red signal that should fire.

Test data is per-user profile state on the SHARED ``${TEST_USER}`` account —
every field is read before it is written and restored in ``finally`` (surface
digest § Test data gotcha).

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: medium priority (both cases' priority `medium` -> l3 -> p2, matching
      the sibling ELITEA-2374/2377 specs in this suite)
    - regression
"""

import logging

import allure
import pytest
from pages.user_profile_settings_page import UserProfileSettingsPage
from playwright.sync_api import Response, expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout / autosave constants
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000    # Fields, toggles, section container
AUTOSAVE_TIMEOUT = 15_000      # Autosave PUT round-trip (per-keystroke typing is slow)
AUTOSAVE_PUT_PATH = "/api/v2/social/author/"  # Autosave endpoint for /settings/memory

# Case values (AFS § Test Data — each row asserts its own).
MAX_CONTEXT_TOKENS_VALUE = 32000      # ELITEA-2376, inside [1000, 10_000_000]
PRESERVE_RECENT_MESSAGES_VALUE = 10   # ELITEA-2376
SUMMARIZATION_INSTRUCTIONS_VALUE = "Summarize briefly, focus on key actions."  # ELITEA-2379
TARGET_SUMMARY_TOKENS_VALUE = 300     # ELITEA-2379, inside [100, 4096]


# Scratch values used ONLY when the account already holds the case value (see
# _write_and_assert_autosave): the page autosaves on blur through
# `useFormikAutoSaveOnBlur`, which returns early when Formik is not `dirty` —
# re-typing the value already stored fires no PUT at all. Writing a distinct
# scratch value first makes the case's own write a genuine change, so
# "typed -> autosaved -> survived a reload" stays a real observation on every
# run rather than an accident of whatever the shared account happened to hold.
MAX_CONTEXT_TOKENS_SCRATCH = 31000
PRESERVE_RECENT_MESSAGES_SCRATCH = 7
SUMMARIZATION_INSTRUCTIONS_SCRATCH = "Scratch instructions (pre-case baseline)."
TARGET_SUMMARY_TOKENS_SCRATCH = 250


def _is_autosave_put_response(response: Response) -> bool:
    """True for the Settings -> Memory autosave PUT."""
    return response.request.method == "PUT" and AUTOSAVE_PUT_PATH in response.url


def _write_and_assert_autosave(page, write, description: str) -> None:
    """Run *write* (a field setter that ends with a blur) and assert the autosave PUT.

    Blur is the page's only save trigger — there is no Save button — so the PUT
    status is asserted rather than merely awaited.
    """
    with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
        write()
    assert put_info.value.status == 200, (
        f"{description} should autosave via PUT {AUTOSAVE_PUT_PATH} -> 200, "
        f"got {put_info.value.status}"
    )


class TestContextManagementValuesPersist:
    """Typed Settings -> Memory values survive autosave + a full page reload."""

    @pytest.mark.parametrize(
        "case_id,needs_summarization",
        [
            pytest.param("ELITEA-2376", False, id="context-management-fields"),
            pytest.param("ELITEA-2379", True, id="summarization-fields"),
        ],
    )
    def test_context_management_values_persist_after_reload(
        self, page, case_id: str, needs_summarization: bool
    ):
        """Typed values autosave on blur and are still there after a reload.

        Args:
            case_id: TMS id this row covers — ELITEA-2376 (Max Context Tokens
                + Preserve Recent Messages) or ELITEA-2379 (Summarization
                Instructions + Target Summary Tokens).
            needs_summarization: whether this row additionally requires the
                Automatic Summarization toggle ON (its two fields carry a real
                ``disabled`` prop while it is OFF).
        """
        profile = UserProfileSettingsPage(page)

        with allure.step(
            f"[{case_id}] Step 1 — Navigate to Settings -> Memory and verify "
            f"the Context Management section is visible"
        ):
            profile.navigate_to_profile()
            expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            f"[{case_id}] Step 2 — Ensure the row's preconditions hold: "
            f"Context Management ON"
            + (" and Automatic Summarization ON" if needs_summarization else "")
        ):
            if profile.is_context_management_enabled():
                logger.info("Context Management already ON — precondition satisfied")
            else:
                with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                    profile.enable_context_management()
                assert put_info.value.status == 200, (
                    f"Turning Context Management ON should autosave via PUT "
                    f"{AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                )

            if needs_summarization:
                expect(profile.automatic_summarization_toggle).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                if profile.is_automatic_summarization_enabled():
                    logger.info("Automatic Summarization already ON — precondition satisfied")
                else:
                    with page.expect_response(_is_autosave_put_response, timeout=AUTOSAVE_TIMEOUT) as put_info:
                        profile.enable_automatic_summarization()
                    assert put_info.value.status == 200, (
                        f"Turning Automatic Summarization ON should autosave via PUT "
                        f"{AUTOSAVE_PUT_PATH} -> 200, got {put_info.value.status}"
                    )

        with allure.step(
            f"[{case_id}] Step 3 — Read the current values of this row's "
            f"fields (restored in teardown — shared ${{TEST_USER}} account)"
        ):
            if case_id == "ELITEA-2376":
                original_max_tokens = profile.get_max_context_tokens()
                original_preserve = profile.get_preserve_recent_messages()
                logger.info(
                    "Originals: max_context_tokens=%d, preserve_recent_messages=%d",
                    original_max_tokens,
                    original_preserve,
                )
            else:
                original_instructions = profile.get_summarization_instructions()
                original_target_tokens = profile.get_target_summary_tokens()
                logger.info(
                    "Originals: summarization_instructions=%r, target_summary_tokens=%d",
                    original_instructions,
                    original_target_tokens,
                )

        try:
            if case_id == "ELITEA-2376":
                with allure.step(
                    f"[{case_id}] Setup — If the shared account already holds a "
                    f"case value, write a scratch value first so step 4's write "
                    f"is a genuine change (the page only autosaves a dirty form)"
                ):
                    if original_max_tokens == MAX_CONTEXT_TOKENS_VALUE:
                        _write_and_assert_autosave(
                            page,
                            lambda: profile.type_max_context_tokens_raw(str(MAX_CONTEXT_TOKENS_SCRATCH)),
                            f"Seeding Max Context Tokens to the scratch value {MAX_CONTEXT_TOKENS_SCRATCH}",
                        )
                    if original_preserve == PRESERVE_RECENT_MESSAGES_VALUE:
                        _write_and_assert_autosave(
                            page,
                            lambda: profile.set_preserve_recent_messages(PRESERVE_RECENT_MESSAGES_SCRATCH),
                            f"Seeding Preserve Recent Messages to the scratch value "
                            f"{PRESERVE_RECENT_MESSAGES_SCRATCH}",
                        )

                with allure.step(
                    f"[{case_id}] Step 4 — Set Max Context Tokens to "
                    f"{MAX_CONTEXT_TOKENS_VALUE} and Preserve Recent Messages "
                    f"to {PRESERVE_RECENT_MESSAGES_VALUE}; each blur must "
                    f"autosave (PUT -> 200). Blur IS the case's 'click "
                    f"somewhere on UI to trigger autosave' — this page has no "
                    f"Save button."
                ):
                    _write_and_assert_autosave(
                        page,
                        lambda: profile.type_max_context_tokens_raw(str(MAX_CONTEXT_TOKENS_VALUE)),
                        f"Setting Max Context Tokens to {MAX_CONTEXT_TOKENS_VALUE}",
                    )
                    _write_and_assert_autosave(
                        page,
                        lambda: profile.set_preserve_recent_messages(PRESERVE_RECENT_MESSAGES_VALUE),
                        f"Setting Preserve Recent Messages to {PRESERVE_RECENT_MESSAGES_VALUE}",
                    )
            else:
                with allure.step(
                    f"[{case_id}] Setup — If the shared account already holds a "
                    f"case value, write a scratch value first (same dirty-form "
                    f"reason as the sibling row)"
                ):
                    if original_instructions == SUMMARIZATION_INSTRUCTIONS_VALUE:
                        _write_and_assert_autosave(
                            page,
                            lambda: profile.set_summarization_instructions(
                                SUMMARIZATION_INSTRUCTIONS_SCRATCH
                            ),
                            "Seeding Summarization Instructions to the scratch value",
                        )
                    if original_target_tokens == TARGET_SUMMARY_TOKENS_VALUE:
                        _write_and_assert_autosave(
                            page,
                            lambda: profile.set_target_summary_tokens(TARGET_SUMMARY_TOKENS_SCRATCH),
                            f"Seeding Target Summary Tokens to the scratch value "
                            f"{TARGET_SUMMARY_TOKENS_SCRATCH}",
                        )

                with allure.step(
                    f"[{case_id}] Step 4 — Enter the summarization "
                    f"instructions and set Target Summary Tokens to "
                    f"{TARGET_SUMMARY_TOKENS_VALUE}; each blur must autosave "
                    f"(PUT -> 200)"
                ):
                    _write_and_assert_autosave(
                        page,
                        lambda: profile.set_summarization_instructions(SUMMARIZATION_INSTRUCTIONS_VALUE),
                        "Setting Summarization Instructions",
                    )
                    assert profile.get_summarization_instructions() == SUMMARIZATION_INSTRUCTIONS_VALUE, (
                        "The Summarization Instructions field should display the entered "
                        "value before the reload (case step 3's 'field accepts the input')"
                    )
                    _write_and_assert_autosave(
                        page,
                        lambda: profile.set_target_summary_tokens(TARGET_SUMMARY_TOKENS_VALUE),
                        f"Setting Target Summary Tokens to {TARGET_SUMMARY_TOKENS_VALUE}",
                    )

            with allure.step(f"[{case_id}] Step 5 — Reload the page"):
                profile.navigate_to_profile()
                expect(profile.context_management_section).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            if case_id == "ELITEA-2376":
                with allure.step(
                    f"[{case_id}] Step 6 — Verify Max Context Tokens shows "
                    f"{MAX_CONTEXT_TOKENS_VALUE} and Preserve Recent Messages "
                    f"shows {PRESERVE_RECENT_MESSAGES_VALUE}"
                ):
                    expect(profile.max_context_tokens_input).to_have_value(
                        str(MAX_CONTEXT_TOKENS_VALUE), timeout=UI_ELEMENT_TIMEOUT
                    )
                    expect(profile.preserve_recent_messages_input).to_have_value(
                        str(PRESERVE_RECENT_MESSAGES_VALUE), timeout=UI_ELEMENT_TIMEOUT
                    )
            else:
                with allure.step(
                    f"[{case_id}] Step 6 — Verify Summarization Instructions "
                    f"shows the entered text and Target Summary Tokens shows "
                    f"{TARGET_SUMMARY_TOKENS_VALUE}"
                ):
                    expect(profile.summarization_instructions_textarea).to_have_value(
                        SUMMARIZATION_INSTRUCTIONS_VALUE, timeout=UI_ELEMENT_TIMEOUT
                    )
                    expect(profile.target_summary_tokens_input).to_have_value(
                        str(TARGET_SUMMARY_TOKENS_VALUE), timeout=UI_ELEMENT_TIMEOUT
                    )
        finally:
            # Restore the shared ${TEST_USER} account to the values read in
            # step 3 (not a case step — no allure.step). Best-effort: a
            # restore failure must not mask the real assertion failure, but it
            # IS logged loudly.
            try:
                profile.navigate_to_profile()
                if case_id == "ELITEA-2376":
                    profile.type_max_context_tokens_raw(str(original_max_tokens))
                    profile.set_preserve_recent_messages(original_preserve)
                    logger.info(
                        "Cleanup: restored max_context_tokens=%d, preserve_recent_messages=%d",
                        original_max_tokens,
                        original_preserve,
                    )
                else:
                    profile.set_summarization_instructions(original_instructions)
                    profile.set_target_summary_tokens(original_target_tokens)
                    logger.info(
                        "Cleanup: restored summarization_instructions=%r, target_summary_tokens=%d",
                        original_instructions,
                        original_target_tokens,
                    )
                profile.wait_for_autosave(timeout=AUTOSAVE_TIMEOUT)
            except Exception as exc:  # noqa: BLE001 — cleanup must not mask the real failure
                logger.warning("Cleanup: failed to restore %s values: %s", case_id, exc)

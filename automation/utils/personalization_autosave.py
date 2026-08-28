"""Shared helpers for the Settings -> AI Personality autosave specs.

The `PERSONA MANAGEMENT` section of `/settings/ai-personality` writes through a
single autosave endpoint and mutates **shared account state** (`persona` and the
per-persona `personality_instructions` map on the `${TEST_USER}` record), which
also drives real chat behaviour. Every spec touching it therefore needs the same
three things:

* a predicate for the autosave `PUT` (asserted, never merely awaited -- the
  `networkidle` wait this suite used to reach for never settles on this app,
  because of the persistent Socket.IO polling transport, #1847);
* the `/settings/ai-personality` console-error filter for the known
  `disableUnderline` warning (#1771);
* a route-guarded read-before-write restore, strict on the success path and
  best-effort on the failure path.

Extracted here rather than copied a fifth time (Hard Rule 7: the third
repetition is the threshold). ``tests/ui/settings/
test_personalization_autosave_no_save_button.py`` (ELITEA-2387) predates this
module and keeps its own private copies -- it is a merged spec and touching it
would be a non-additive change to shared, already-reviewed code (Hard Rule 3).
Migrate it opportunistically the next time it is edited for its own reasons.
"""

import logging

import allure
from pages.settings_personalization_page import (
    AI_PERSONALITY_PATH,
    AUTHOR_SETTINGS_ENDPOINT,
    SettingsPersonalizationPage,
)
from playwright.sync_api import Response, expect

logger = logging.getLogger(__name__)

#: Autosave round-trip budget. Generous on purpose -- the write is asserted, so
#: a slow-but-successful save must not read as a failure.
AUTOSAVE_TIMEOUT = 15_000

#: Known defect EliteaAI/elitea-testing-public#1771 -- `/settings/ai-personality`
#: (and `/settings/memory`) log a React `disableUnderline` warning from
#: `StyledInputEnhancer` on every load. Pre-dates this case family and is
#: unrelated to autosave. Filtered by its exact message fragment ONLY, so any
#: other console error still fails the spec.
KNOWN_DEFECT_1771_FRAGMENT = "disableUnderline"


def is_author_autosave(response: Response) -> bool:
    """Whether *response* is the personalization autosave write."""
    return AUTHOR_SETTINGS_ENDPOINT in response.url and response.request.method == "PUT"


def unexpected_console_errors(console_errors: list[str]) -> list[str]:
    """Console errors other than the known #1771 `disableUnderline` warning."""
    return [e for e in console_errors if KNOWN_DEFECT_1771_FRAGMENT not in e]


def persona_value_of(label: str) -> str:
    """Option *value* for a persona *label* (``"QA"`` -> ``"qa"``).

    Every entry of `PERSONA_OPTIONS` (`src/common/constants.js`) has
    ``value == label.lower()``.
    """
    return label.strip().lower()


def _ensure_on_ai_personality(personalization: SettingsPersonalizationPage) -> None:
    """Route-guard: the restore may run from anywhere the test failed.

    Reading the persona select on a route that does not render it makes
    Playwright auto-wait and then raise ``TimeoutError``. Raised out of a
    teardown block, that exception REPLACES the real failure in the report (the
    original survives only as ``__context__``), so a one-line assertion failure
    would be reported as a 30s timeout on an unrelated locator.
    """
    if AI_PERSONALITY_PATH not in personalization.page.url:
        personalization.open_settings_tab("ai-personality")
    personalization.wait_for_persona_select()


def restore_persona(personalization: SettingsPersonalizationPage, original_label: str) -> None:
    """Put the shared account's Default persona back on *original_label*."""
    _ensure_on_ai_personality(personalization)

    if personalization.get_persona() == original_label:
        return

    with allure.step(f"Teardown - Restore the original persona ({original_label})"):
        with personalization.page.expect_response(
            is_author_autosave, timeout=AUTOSAVE_TIMEOUT
        ) as restore:
            personalization.select_persona(persona_value_of(original_label))
        assert restore.value.status == 200, (
            "Failed to restore the original persona -- shared account state is left on a "
            f"different value (restore PUT returned {restore.value.status})"
        )
        expect(personalization.persona_select_combobox).to_have_text(original_label)


def restore_user_instructions(
    personalization: SettingsPersonalizationPage,
    persona_label: str,
    original_text: str,
) -> None:
    """Put *persona_label*'s user-instructions slot back to *original_text*.

    The field is stored per persona, so the slot is reached by first selecting
    that persona -- restoring the text under the wrong persona would both leave
    the original slot dirty and pollute a second one. A run that restores the
    persona but leaves text behind changes what the NEXT run of these specs
    observes, so this is part of the contract, not politeness.
    """
    _ensure_on_ai_personality(personalization)

    if personalization.get_persona() != persona_label:
        with personalization.page.expect_response(
            is_author_autosave, timeout=AUTOSAVE_TIMEOUT
        ) as switch:
            personalization.select_persona(persona_value_of(persona_label))
        assert switch.value.status == 200, (
            f"Failed to switch to {persona_label} to restore its instructions slot "
            f"(PUT returned {switch.value.status})"
        )

    if personalization.get_user_instructions() == original_text:
        return

    with allure.step(f"Teardown - Restore {persona_label}'s user instructions"):
        personalization.fill_user_instructions(original_text)
        with personalization.page.expect_response(
            is_author_autosave, timeout=AUTOSAVE_TIMEOUT
        ) as restore:
            personalization.click_neutral_content_area()
        assert restore.value.status == 200, (
            "Failed to restore the original user instructions -- shared account state is "
            f"left dirty (restore PUT returned {restore.value.status})"
        )


def best_effort(action, description: str) -> None:
    """Run a teardown *action*, logging instead of raising.

    Used only on the path where the test body ALREADY failed: there the real
    failure is the report, and a teardown exception would replace it. On the
    success path the strict variants above are used, so a genuine restore
    failure still fails the test rather than silently leaking shared state.
    """
    try:
        action()
    except Exception:  # noqa: BLE001 -- deliberate: never mask the real failure
        logger.warning(
            "Teardown could not %s after a test failure -- the shared account may be "
            "left in a modified state",
            description,
            exc_info=True,
        )

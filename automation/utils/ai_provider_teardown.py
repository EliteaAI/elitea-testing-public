"""Shared teardown for AI-provider configuration specs.

Every spec in the ``settings-ai-providers`` cluster that creates a
configuration owes the same `finally`: go back to the list page, expand the
section the configuration lives in, delete it through the real UI flow (card ->
three-dot menu -> type-to-confirm dialog), and report the resulting card count
so the spec can prove the project was left as it was found.

The two merged LLM specs (``test_llm_model_create.py`` /
``test_llm_model_edit.py``) each carry their own module-level copy of that
logic. This cluster adds four more specs; extracting the shared shape here at
the third repetition is the project's own rule
(``test-automation-implementation`` Hard Rule 7). The merged copies are
deliberately left untouched -- migrating them is a refactor, not part of a
test-case PR (named as tech debt in the ELITEA-2398/2410/2399/2400/2401 Run
Report).

Two behaviours are load-bearing and easy to get wrong:

* **The section must be ISOLATED before the card is counted.** Accordion content
  unmounts on collapse (``AIProviderAccordion.jsx``), so a card is not in the DOM
  until its section is opened -- and the card testid is generic, so a whole-page
  count depends on which OTHER sections happen to be open.
  ``AIProvidersPage.isolate_section`` settles both.
* **Teardown must never mask the test's own failure.** Every exception is
  logged and swallowed, and the function returns ``None`` so the caller can
  tell "cleanup could not run" apart from "cleanup ran and the count is N".
"""

import logging
from collections.abc import Iterable

from playwright.sync_api import Locator, expect

logger = logging.getLogger("elitea.utils.ai_provider_teardown")

UI_ELEMENT_TIMEOUT = 10_000


def delete_configurations_if_present(
    providers_page,
    form,
    section_header: Locator,
    candidate_names: Iterable[str],
    timeout: int = UI_ELEMENT_TIMEOUT,
) -> int | None:
    """Delete whichever of *candidate_names* is on the AI Providers list.

    Args:
        providers_page: an :class:`~pages.ai_providers_page.AIProvidersPage`.
        form: an :class:`~pages.ai_provider_form_page.AiProviderFormPage`.
        section_header: the accordion header of the section the configuration
            lives in -- expanded before every lookup (see module docstring).
        candidate_names: display names to try, in order. Several are passed
            when a spec renames its subject mid-flight and a failure may have
            left either name live.

    Returns:
        The number of configuration cards in *section_header*'s own section
        afterwards (the section is ISOLATED first, so the count is scoped to it
        and comparable with a baseline captured the same way), or ``None`` if
        teardown could not run at all.

    Tolerant of every candidate being absent -- which is exactly what a fixed
    #1984 produces for ``test_embedding_model_required_field_validation.py``.
    """
    try:
        providers_page.navigate()
        section_header.wait_for(state="visible", timeout=timeout)
        providers_page.isolate_section(section_header)

        for name in dict.fromkeys(candidate_names):
            if providers_page.card_for_model(name).count() == 0:
                logger.info("Teardown: no configuration named %r to delete", name)
                continue
            providers_page.open_model_card(name)
            form.wait_for_form()
            form.delete_current_configuration(name)
            providers_page.navigate()
            section_header.wait_for(state="visible", timeout=timeout)
            providers_page.isolate_section(section_header)
            expect(providers_page.card_for_model(name)).to_have_count(0)
            logger.info("Teardown: deleted the configuration %r", name)

        return providers_page.get_configuration_card_count()
    except Exception:  # noqa: BLE001 - teardown must never mask the test's own failure
        logger.exception("Teardown failed to delete the configuration(s) %r", list(candidate_names))
        return None

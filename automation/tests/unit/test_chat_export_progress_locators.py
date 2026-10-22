"""Pins the locator-policy contract of ``ChatPage.click_export_capturing_progress`` (ELITEA-3764 fix round 1).

The method's in-page MutationObserver needs CSS selectors (JS cannot take a Playwright
Locator). They must come from class-level constants derived from the declared
``LocatorDescriptor`` testids, never from ``data-testid`` literals inside the method body.
"""

import inspect

from pages.chat_page import ChatPage


def test_export_progress_selectors_derive_from_declared_locators():
    assert ChatPage.EXPORT_PROGRESS_SELECTOR == f'[data-testid="{ChatPage.export_chat_modal_progress.testid}"]'
    assert ChatPage.EXPORT_MODAL_SELECTOR == f'[data-testid="{ChatPage.export_chat_modal.testid}"]'


def test_click_export_capturing_progress_builds_no_selector_in_body():
    source = inspect.getsource(ChatPage.click_export_capturing_progress)
    assert "data-testid" not in source, "selector literal built inside method body"
    assert "export-chat-modal" not in source.replace("``export-chat-modal-progress``", ""), (
        "testid literal duplicated inside method body"
    )

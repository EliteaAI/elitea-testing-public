"""Settings -> General page object (project identity + project switching).

URL: ``/settings`` (redirects to ``/settings/project-general``).

Covers the surface ELITEA-2424 uses to establish "which project am I in":
the sidebar project selector (app-wide chrome) plus the General section that
names the selected project.

Locator provenance (all pre-existing testids, none added by this case):
``project-selector-trigger-combobox`` — EliteaUI
``src/[fsd]/widgets/sidebar-root/ui/SidebarProjectSelect.jsx`` (the shared
``ProjectSelect`` appends ``-combobox`` to the passed ``data-testid``), already
driven by :class:`pages.analytics_page.AnalyticsPage` and
:class:`pages.admin_users_page.AdminUsersPage`. ``select-option-{id}`` — the
shared ``SingleSelectMenuItem.jsx`` option family reused across the suite.
``project-general-section`` — EliteaUI
``src/[fsd]/features/settings/ui/project-general/ProjectGeneralContent.jsx``.

The selector fields are declared here rather than cross-imported from another
page object, matching the convention the two existing implementations already
follow (see ``AnalyticsPage.project_selector_trigger``).
"""

import logging

from playwright.sync_api import Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.settings_project_general")

SETTINGS_PATH = "/settings"


class SettingsProjectGeneralPage(BasePage):
    """Settings -> General page, plus the sidebar project selector."""

    project_selector_trigger = LocatorDescriptor(
        testid="project-selector-trigger-combobox",
        description="Sidebar project selector combobox trigger",
    )

    project_general_section = LocatorDescriptor(
        testid="project-general-section",
        description="Settings -> General project section (name + teammates)",
    )

    # Project-selector dropdown options — same shared ``select-option-{value}``
    # family (``SingleSelectMenuItem.jsx``) as ``AnalyticsPage.SELECT_OPTION``
    # and ``AdminUsersPage.SELECT_OPTION``: reuse the pattern, never invent a
    # second one. Dynamic testids live at class level per
    # ``.agents/testing.md`` § Locator policy.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    def __init__(self, page: Page):
        super().__init__(page)

    def navigate(self, timeout: int = 30000) -> None:
        """Load ``/settings`` and wait for the General section to render."""
        super().navigate(SETTINGS_PATH)
        self.project_general_section.wait_for(state="visible", timeout=timeout)

    def switch_project(self, project_id, timeout: int = 30000) -> None:
        """Select *project_id* in the sidebar project selector.

        The selector is app-wide chrome, so this works from any route; the
        General section re-renders in place (no navigation).

        NOTE: the Support Assistant widget renders in a bottom-left overlay
        container that sits above the selector's dropdown, so the widget must
        be closed (or the page freshly loaded) before calling this — with the
        widget open, the option click is intercepted by the widget subtree.

        Args:
            project_id: Numeric project id (the ``select-option-`` suffix)
            timeout: Maximum wait time in milliseconds
        """
        logger.info("Switching sidebar project to %s", project_id)
        self.project_selector_trigger.click(timeout=timeout)
        option = self.page.locator(self.SELECT_OPTION.format(project_id))
        option.wait_for(state="visible", timeout=timeout)
        # The dropdown option carries the project's display name, so the
        # trigger picking that name up is the product's own "the selection
        # landed" signal. Waiting on the section or the network instead returns
        # while the sidebar label still shows the PREVIOUS project (observed
        # live: a switch read back the old name and failed a later assertion).
        target_name = self._name_of(option)
        option.click()
        expect(self.project_selector_trigger).to_contain_text(
            target_name, timeout=timeout
        )
        self.project_general_section.wait_for(state="visible", timeout=timeout)
        self.wait_for_network(timeout=timeout)

    @staticmethod
    def _name_of(element) -> str:
        """Project display name rendered by *element* (trigger or option).

        Both render the name on the LAST line — the trigger prefixes an avatar
        letter and a ``Project:`` label, an option prefixes the avatar letter
        when the project has one.

        Args:
            element: Trigger or option Locator

        Returns:
            The project display name
        """
        return element.inner_text().strip().splitlines()[-1].strip()

    def get_selected_project_name(self) -> str:
        """Project name currently shown in the sidebar selector trigger.

        The trigger renders three lines — an avatar letter, the ``Project:``
        label and the name (e.g. ``"U\\nProject:\\nUI Testing"``) — so the name
        is the last line.

        Returns:
            The selected project's display name
        """
        return self._name_of(self.project_selector_trigger)

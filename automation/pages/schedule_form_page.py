"""Schedule create page ("New Schedule") reached from a pipeline's SCHEDULES section.

URL: /pipelines/all/{id}/schedules/create?viewMode=owner&name=...&versionId=...
Replaces the retired Trigger-dropdown "Schedule" option + settings modal (EL-7011).
"""

import logging

from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, ScopedLocator

logger = logging.getLogger("elitea.pages.schedule_form")


class ScheduleFormPage(BasePage):
    """New Schedule page: locked pipeline, Builder/Cron Expression modes, risk check, Save/Cancel."""

    name_input = LocatorDescriptor(
        role="textbox",
        name="Name",
        suggested_testid="schedule-name-input",
        description="Schedule Name input on the New Schedule page (unique textbox named Name)",
    )
    locked_pipeline = LocatorDescriptor(testid="schedule-locked-entity", description="Locked Pipeline field")
    version_select = LocatorDescriptor(testid="schedule-version", description="Version select")
    mode_tabs = LocatorDescriptor(testid="pipeline-schedule-mode-tabs", description="Builder / Cron Expression toggle group")
    builder_button = LocatorDescriptor(
        role="button",
        name="Builder",
        suggested_testid="pipeline-schedule-mode-builder-button",
        description="Builder toggle (ToggleButton, role button not tab); unique page-wide",
    )
    cron_button = LocatorDescriptor(
        role="button",
        name="Cron Expression",
        suggested_testid="pipeline-schedule-mode-cron-button",
        description="Cron Expression toggle (ToggleButton, role button not tab); unique page-wide",
    )
    period_select = LocatorDescriptor(testid="schedule-cron-period-select", description="Every (Day/Week/Month)")
    weekdays_select_week = LocatorDescriptor(
        testid="schedule-cron-weekdays-select-week", description="'on' weekday select (week period only)"
    )
    hour_select = LocatorDescriptor(testid="schedule-cron-hour-select", description="Hour select")
    minute_select = LocatorDescriptor(testid="schedule-cron-minute-select", description="Minute select")
    summary_text = LocatorDescriptor(testid="pipeline-schedule-summary-text", description="Cron summary line")
    cron_input = LocatorDescriptor(testid="pipeline-schedule-cron-input", description="Raw cron expression input")
    CRON_INNER_INPUT = ScopedLocator(
        css="input",
        suggested_testid="pipeline-schedule-cron-text-input",
        description="The <input> inside the cron-expression wrapper (testid sits on the wrapper on DEV); scope = cron_input",
    )
    save_button = LocatorDescriptor(testid="schedule-save-button", description="Schedule Save button")
    cancel_button = LocatorDescriptor(testid="schedule-cancel-button", description="Schedule Cancel button")
    breadcrumb_current = LocatorDescriptor(
        css='[aria-current="page"]',
        suggested_testid="schedule-breadcrumb-current-text",
        description="Current breadcrumb item (reads 'New Schedule'); only on-page aria-current element",
    )

    # Risk check (human-input steps in the SAVED version block scheduling)
    risk_block_box = LocatorDescriptor(testid="schedule-risk-block-box", description="Blocking risk box")
    risk_hint = LocatorDescriptor(
        css="#schedule-risk-hint",
        suggested_testid="schedule-risk-hint-text",
        description="'Fix the risk check to save' hint beside Save (id referenced by Save aria-describedby)",
    )
    risk_open_pipeline_link = ScopedLocator(
        role="link",
        name="Open pipeline to change steps",
        suggested_testid="schedule-risk-block-open-pipeline-link",
        description="target=_blank link inside the risk box; scope = risk_block_box",
    )

    # Cron option rows (single open listbox at a time)
    CRON_OPTION = ScopedLocator(role="option", name="{}", exact=True, suggested_testid="schedule-cron-option-{}")

    RISK_CHECK_PATH = "/schedules/prompt_lib/"

    def __init__(self, page: Page):
        super().__init__(page)

    def wait_until_ready(self, timeout: int = 15000) -> None:
        """Create page rendered (Save visible, locked pipeline shown)."""
        self.save_button.wait_for(state="visible", timeout=timeout)
        self.locked_pipeline.wait_for(state="visible", timeout=timeout)

    def fill_name(self, name: str, timeout: int = 10000) -> None:
        self.name_input.click(timeout=timeout)
        self.name_input.fill(name, timeout=timeout)

    def get_cron_select_count(self) -> int:
        """Number of Builder-mode cron selects present (period/weekdays/hour/minute)."""
        return sum(
            d.count()
            for d in (self.period_select, self.weekdays_select_week, self.hour_select, self.minute_select)
        )

    def _pick(self, select: Locator, option: str, timeout: int) -> None:
        select.click(timeout=timeout)
        opt = self.CRON_OPTION.within(self.page, option)
        opt.click(timeout=timeout)
        expect(opt).to_have_count(0, timeout=timeout)

    def select_period(self, period: str, timeout: int = 10000) -> None:
        self._pick(self.period_select, period, timeout)

    def set_hour_minute(self, hour: str, minute: str, timeout: int = 10000) -> None:
        self._pick(self.hour_select, hour, timeout)
        self._pick(self.minute_select, minute, timeout)

    def get_cron_value(self) -> str:
        return self.CRON_INNER_INPUT.within(self.cron_input).input_value()

    def get_summary_text(self, timeout: int = 10000) -> str:
        self.summary_text.wait_for(state="visible", timeout=timeout)
        return (self.summary_text.text_content() or "").strip()

    def save(self, project_id: str, timeout: int = 15000) -> dict:
        """Click Save, wait for the schedule POST (201), return its JSON body."""
        expect(self.save_button).to_be_enabled(timeout=timeout)
        with self.page.expect_response(
            lambda r: f"{self.RISK_CHECK_PATH}{project_id}" in r.url
            and r.request.method == "POST"
            and "/check" not in r.url
            and r.status == 201,
            timeout=timeout,
        ) as info:
            self.save_button.click(timeout=timeout)
        return info.value.json()

    def wait_for_risk_check(self, timeout: int = 15000):
        """Context manager: wrap the navigation that triggers the risk check POST .../check."""
        return self.page.expect_response(
            lambda r: r.url.rstrip("/").endswith("/check") and self.RISK_CHECK_PATH in r.url, timeout=timeout
        )

    def open_from_pipeline(self, pipeline_page, timeout: int = 20000) -> None:
        """Click "+ Schedule" on the pipeline page and wait for the create page AND its risk check (POST .../check)."""
        with self.wait_for_risk_check(timeout=timeout):
            pipeline_page.open_new_schedule_page(timeout=timeout)
        self.wait_until_ready(timeout=timeout)

    def get_risk_block_text(self, timeout: int = 10000) -> str:
        self.risk_block_box.wait_for(state="visible", timeout=timeout)
        return (self.risk_block_box.text_content() or "").strip()

    def cancel(self, timeout: int = 10000) -> None:
        """Cancel back to the pipeline page."""
        self.cancel_button.click(timeout=timeout)
        self.page.wait_for_url(lambda url: "/schedules/create" not in url, timeout=timeout)

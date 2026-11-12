"""Run Analytics page object (Skill -> Run History -> row menu -> Analytics).

URL: /skills/all/{id}/history/analytics?run=..&history_run_id=..  (ELITEA-4632)

Costs-tab KPI cards and the "Cost by User" / "Cost by Model" tables render
without testids on DEV, so they are declared as ladder ``xpath`` scoped locators
under ``run-analytics-page`` (non-positional, anchored on the visible label).
"""

import json
import logging
import math
import re
import time

from playwright.sync_api import Page, Response, expect

from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor, ScopedLocator

logger = logging.getLogger(__name__)


class RunAnalyticsPage(BasePage):
    """Run Analytics page of a skill run (Costs / Tokens / Health tabs)."""

    COSTS_API_FRAGMENT = "/usage/analytics_costs/"

    # --- Page shell ------------------------------------------------------
    page_root = LocatorDescriptor(testid="run-analytics-page", description="Run Analytics page root")
    breadcrumb_items = LocatorDescriptor(testid="breadcrumb-item", description="Breadcrumb links (enumerated)")
    breadcrumb_current = LocatorDescriptor(testid="breadcrumb-current", description="Current (last) breadcrumb")
    run_info = LocatorDescriptor(testid="run-analytics-run-info", description="Run: <date> · Version · Model header")
    refresh_button = LocatorDescriptor(testid="run-analytics-refresh-button", description="Re-fetch analytics data")
    costs_empty = LocatorDescriptor(testid="run-analytics-costs-empty", description="Costs tab no-data placeholder")
    tab_costs = LocatorDescriptor(testid="run-analytics-tab-costs", description="Costs tab")
    tab_tokens = LocatorDescriptor(testid="run-analytics-tab-tokens", description="Tokens tab")
    tab_health = LocatorDescriptor(testid="run-analytics-tab-health", description="Health tab")

    # --- Costs tab content (no testids on DEV) ---------------------------
    KPI_CARD_VALUE = ScopedLocator(
        xpath=".//span[normalize-space()='{}' and not(@role)]/../following-sibling::div/span",
        suggested_testid="run-analytics-costs-kpi-value-{}",
        description="Value of the KPI card whose label span reads {}; table headers (role=button) excluded. "
        "Rungs 1-4 failed: cards are MuiBox with a plain label span, no testid/role/label",
    )
    TABLE_CELLS = ScopedLocator(
        xpath=".//span[normalize-space()='{}']/../following-sibling::div//p",
        suggested_testid="run-analytics-costs-table-cell-{}",
        description="Data cells of the table titled {}; rungs 1-4 failed: cells are bare <p> without testid/role",
    )

    TABLE_USER_NAMES = ScopedLocator(
        xpath=".//span[normalize-space()='{}']/../following-sibling::div//span[contains(@class,'user-label-name')]",
        suggested_testid="run-analytics-costs-table-user-name-{}",
        description="User-name labels (UserLabel span.user-label-name, a stable app class) in the table titled {}; "
        "rungs 1-4 failed: name span has no testid/role/label",
    )

    @action("Wait for Run Analytics page to load")
    def wait_until_loaded(self, timeout: int = 15000) -> None:
        self.page.wait_for_url(re.compile(r"/skills/all/\d+/history/analytics\?"), timeout=timeout)
        self.page_root.wait_for(state="visible", timeout=timeout)

    def breadcrumb_texts(self) -> list[str]:
        return [t.strip() for t in self.breadcrumb_items.all_text_contents()]

    @action("Wait for Costs data to be ingested")
    def wait_for_costs_data(self, timeout_s: int = 150) -> dict:
        """Refresh until the empty placeholder is gone; return the final costs payload.

        Usage events are ingested asynchronously (~10-40 s after the run); each
        iteration re-fetches via the refresh button and waits on the response
        (the response round-trip is the pacing — no sleep).
        """
        deadline = time.time() + timeout_s
        while True:
            with self.page.expect_response(self._is_costs_response, timeout=30000) as info:
                self.refresh_button.click()
            payload = self._payload(info.value)
            if payload.get("kpis", {}).get("total_tokens", 0) > 0:
                expect(self.costs_empty).to_have_count(0, timeout=10000)
                expect(self.KPI_CARD_VALUE.within(self.page_root, "TOTAL COST")).to_be_visible(timeout=10000)
                return payload
            if time.time() > deadline:
                raise TimeoutError("Costs data never appeared on the Run Analytics page")

    @classmethod
    def _is_costs_response(cls, r: Response) -> bool:
        return cls.COSTS_API_FRAGMENT in r.url and r.status == 200

    @staticmethod
    def _payload(r: Response) -> dict:
        return json.loads(r.text())

    def kpi_value(self, label: str) -> str:
        return (self.KPI_CARD_VALUE.within(self.page_root, label).text_content() or "").strip()

    def table_cells(self, title: str) -> list[str]:
        return [t.strip() for t in self.TABLE_CELLS.within(self.page_root, title).all_text_contents()]

    def table_user_names(self, title: str) -> list[str]:
        return [t.strip() for t in self.TABLE_USER_NAMES.within(self.page_root, title).all_text_contents()]

    @staticmethod
    def format_user_name(user: dict) -> str:
        """Mirror the product's ``formatUserName``: display name, else email, else 'User <id>'."""
        if user.get("user_display_name"):
            return user["user_display_name"]
        if user.get("user_email"):
            return user["user_email"]
        return "" if user.get("user_id") is None else f"User {user['user_id']}"

    @staticmethod
    def format_cost(value: float | None) -> str:
        """Mirror the product's ``fmtCost`` (analyticsCommon.helpers.js) tier by tier.

        None / non-finite -> '-'; 0 -> '$0.00'; |v| < 1e-5 -> '< $0.00001';
        |v| < 1e-4 -> 5 decimals; |v| < 0.01 -> ROUNDED UP to 4 decimals (0.000512 -> '$0.0006');
        |v| < 1 -> 4 decimals; |v| < 1000 -> 2 decimals; < 1e6 -> 'N.NK'; else 'N.NM'.
        A negative value gets a '-' sign prefix (before '< ' for the sub-1e-5 tier: '-< $0.00001').
        """
        if value is None or not math.isfinite(value):
            return "-"
        if value == 0:
            return "$0.00"
        sign = "-" if value < 0 else ""
        a = abs(value)
        if a < 1e-5:
            return f"{sign}< $0.00001"
        if a < 1e-4:
            return f"{sign}${a:.5f}"
        if a < 0.01:
            # Exact mirror of the product's Math.ceil(abs * 10_000) / 10_000 (no pre-rounding): Python and JS
            # share IEEE-754 doubles, so float-ceil quirks (0.0051*10000 = 51.00000000000001 -> $0.0052) are
            # deliberately reproduced.
            return f"{sign}${math.ceil(a * 10000) / 10000:.4f}"
        if a < 1:
            return f"{sign}${a:.4f}"
        if a < 1000:
            return f"{sign}${a:.2f}"
        if a < 1e6:
            return f"{sign}${a / 1000:.1f}K"
        return f"{sign}${a / 1e6:.1f}M"

    @action("Switch analytics tab")
    def open_tab(self, tab: LocatorDescriptor) -> None:
        tab.click()
        expect(tab).to_have_attribute("aria-selected", "true", timeout=10000)

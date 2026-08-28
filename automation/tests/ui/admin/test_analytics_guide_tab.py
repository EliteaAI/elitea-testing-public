"""UI test — Guide tab displays explanatory documentation for each metric.

Read-only verification of static, bundled documentation content
(`.agents/testing.md` § Test data strategy). The Guide tab issues NO network
request at all and is project- and date-range-independent.

Test case: ELITEA-2325
AFS: test-specs/settings-analytics/l2_guide-tab-metric-documentation_ELITEA-2325.md

Fidelity (`.agents/testing.md` § Fidelity policy): NO substitution. Everything
asserted is rendered by the live product from its own bundled `GUIDE_SECTIONS`
constant; the layout measurements in step 5 are read-only DOM reads of what the
product laid out (`scrollHeight`/`clientHeight` have no Playwright accessor),
never injected or forced state.

Case-text drift (see AFS § Metadata, filed elitea-testing-public#1950): the case
says "each metric section shows description, Calculation (highlighted in blue),
Data source (highlighted in blue)". Live, `Calculation:` renders on a minority
of metrics and `Data source:` on fewer still — both are `{m.x && ...}`
conditionals, and even `COST` inside the case's own `Overview Tab` section has
neither. The blue is on the VALUE, not the label. This test therefore asserts
the full description+Calculation+Data source contract for the four metrics the
case actually names, and the honest generalisation for every rendered metric: a
non-empty name and description, and a `Calculation:` / `Data source:` LABEL
present exactly when its VALUE node is (never one orphaned from the other).
"""

import logging

import allure
import pytest
from pages.analytics_page import AnalyticsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_SECTION_TITLES = (
    "Overview Tab",
    "Overview Charts",
    "Costs Tab",
    "Tokens Tab",
    "Agents & Pipelines Tab",
    "Tools Tab",
    "Users Tab",
    "Health Tab",
    "General Concepts",
)

CASE_SECTION_TITLE = "Overview Tab"
CASE_METRIC_NAMES = ("TEAM", "AI ACTIVE", "Adoption Rate", "LLM CALLS")

# `styles.guideCalcValue`'s #58A6FF — the "highlighted in blue" the case
# describes, confirmed live via getComputedStyle against the active theme.
GUIDE_VALUE_BLUE = "rgb(88, 166, 255)"


class TestAnalyticsGuideTab:
    """ELITEA-2325 — Guide tab: documentation sections, the case's four named
    Overview metrics with their blue Calculation/Data source values, the
    label-iff-value pairing across every metric, and non-truncated content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/analytics/ELITEA-2325_guide-tab-displays-explanatory-documentation-for-each-metric.md",
        "onetest-ai Test Case link",
    )
    def test_guide_tab_metric_documentation(self, page):
        """Guide tab renders its documentation sections, documents the case's
        four named Overview metrics with blue Calculation and Data source
        values, and clips no description text."""
        analytics_page = AnalyticsPage(page)
        console_errors = analytics_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Analytics and open the Guide tab"):
                analytics_page.navigate_capturing_analytics()
                analytics_page.open_guide_tab()
                assert analytics_page.is_tab_selected(analytics_page.tab_guide), (
                    "Expected the 'Guide' tab to be aria-selected=true after clicking it"
                )

            with allure.step(
                "Step 2 — Verify the tab loads documentation (not blank): sections and metrics "
                "are rendered, and the section titles match in order"
            ):
                section_count = analytics_page.guide_sections.count()
                metric_count = analytics_page.guide_metrics.count()
                assert section_count > 0, "Expected the Guide tab to render documentation sections"
                assert metric_count > 0, "Expected the Guide tab to render metric entries"
                actual_titles = tuple(analytics_page.get_guide_section_titles())
                assert actual_titles == EXPECTED_SECTION_TITLES, (
                    f"Expected section titles {EXPECTED_SECTION_TITLES}, got {actual_titles}"
                )
                logger.info("Guide rendered %d sections, %d metrics", section_count, metric_count)

            with allure.step(
                'Step 3 — Verify the "Overview Tab" section documents TEAM, AI ACTIVE, '
                "Adoption Rate and LLM CALLS, in that order"
            ):
                section_index = analytics_page.get_guide_section_index_by_title(CASE_SECTION_TITLE)
                assert section_index >= 0, (
                    f"Expected a guide section titled {CASE_SECTION_TITLE!r}, got "
                    f"{analytics_page.get_guide_section_titles()}"
                )
                metric_names = analytics_page.get_guide_metric_names_in_section(section_index)
                positions = [
                    metric_names.index(name) for name in CASE_METRIC_NAMES if name in metric_names
                ]
                missing = [name for name in CASE_METRIC_NAMES if name not in metric_names]
                assert not missing, (
                    f"Expected the {CASE_SECTION_TITLE!r} section to document {list(CASE_METRIC_NAMES)}, "
                    f"missing {missing} (section metrics: {metric_names})"
                )
                assert positions == sorted(positions), (
                    f"Expected {list(CASE_METRIC_NAMES)} to appear in that order, got the section's "
                    f"order {metric_names}"
                )

            with allure.step(
                "Step 4 — Verify each named metric shows a description plus blue Calculation "
                "and Data source values, and that no metric anywhere orphans a label from its value"
            ):
                for metric_name in CASE_METRIC_NAMES:
                    block = analytics_page.get_guide_metric_block(section_index, metric_name)
                    block_text = block.inner_text()
                    description = block.locator(
                        analytics_page.GUIDE_METRIC_DESCRIPTION_SELECTOR
                    ).first
                    assert (description.text_content() or "").strip(), (
                        f"Expected metric {metric_name!r} to render a non-empty description"
                    )
                    assert "Calculation:" in block_text, (
                        f"Expected metric {metric_name!r} to show a 'Calculation:' label"
                    )
                    assert "Data source:" in block_text, (
                        f"Expected metric {metric_name!r} to show a 'Data source:' label"
                    )
                    for selector, label in (
                        (analytics_page.GUIDE_METRIC_CALCULATION_VALUE, "Calculation"),
                        (analytics_page.GUIDE_METRIC_SOURCE_VALUE, "Data source"),
                    ):
                        value = block.locator(selector).first
                        expect(value).to_be_visible()
                        assert (value.text_content() or "").strip(), (
                            f"Expected metric {metric_name!r}'s {label} value to be non-empty"
                        )
                        expect(value).to_have_css("color", GUIDE_VALUE_BLUE)

                # The honest generalisation of the case's "each metric section
                # shows ..." intent (#1950): both conditional branches are
                # referenced — a value node present exactly when its label is.
                for index in range(metric_count):
                    name = (
                        analytics_page.guide_metric_names.nth(index).text_content() or ""
                    ).strip()
                    assert name, f"Expected guide metric #{index} to render a non-empty name"
                    description_text = (
                        analytics_page.guide_metric_descriptions.nth(index).text_content() or ""
                    ).strip()
                    assert description_text, (
                        f"Expected guide metric {name!r} to render a non-empty description"
                    )
                    pairing = analytics_page.get_guide_metric_pairing(index)
                    assert pairing["calculation_label"] == bool(pairing["calculation_value"]), (
                        f"Metric {name!r} orphans its Calculation label/value: {pairing}"
                    )
                    assert pairing["source_label"] == bool(pairing["source_value"]), (
                        f"Metric {name!r} orphans its Data source label/value: {pairing}"
                    )

            with allure.step(
                "Step 5 — Verify the guide content is readable and not truncated: no "
                "description is ellipsised or clipped, and no section card clips its content"
            ):
                for index in range(metric_count):
                    description = analytics_page.guide_metric_descriptions.nth(index)
                    text_overflow = description.evaluate(
                        "el => window.getComputedStyle(el).textOverflow"
                    )
                    assert text_overflow != "ellipsis", (
                        f"Expected guide description #{index} not to be ellipsised, got "
                        f"text-overflow: {text_overflow!r}"
                    )
                    assert not analytics_page.is_element_clipped(description), (
                        f"Expected guide description #{index} not to be clipped by its own box"
                    )
                for index in range(section_count):
                    section = analytics_page.guide_sections.nth(index)
                    assert not analytics_page.is_element_clipped(section), (
                        f"Expected guide section #{index} "
                        f"({analytics_page.get_guide_section_titles()[index]!r}) not to clip its "
                        f"content"
                    )

            with allure.step("Step 6 — Verify no console errors were logged throughout"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()

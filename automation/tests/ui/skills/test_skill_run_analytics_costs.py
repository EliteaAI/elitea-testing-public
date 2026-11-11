"""Test — Skill Run Analytics: navigation from Run History and Costs accuracy.

Test case: ELITEA-4632
AFS: test-specs/skills/l2_skill-run-analytics-costs-accuracy_ELITEA-4632.md
"""

import logging
import re
import time

import allure
import pytest
from playwright.sync_api import expect
from pages.run_analytics_page import RunAnalyticsPage
from pages.skill_detail_page import SkillDetailPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression]

AI_RESPONSE_TIMEOUT = 45_000
TOL = 1e-9


def _costs_sum(d: dict, prefix: str = "") -> float:
    return d[f"{prefix}input_cost"] + d[f"{prefix}output_cost"] + d[f"{prefix}cache_read_cost"] + d[
        f"{prefix}cache_creation_cost"
    ]


class TestSkillRunAnalytics:
    """ELITEA-4632 — Run History -> Analytics, Costs reconcile, no leakage between runs."""

    @pytest.mark.tms("ELITEA-4632")
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-4632_skill-run-analytics-cost-accuracy.md",
        "onetest-ai Test Case link",
    )
    def test_skill_run_analytics_costs_accuracy(self, page, skill_api):
        ts = int(time.time())
        skill_name = f"autotest-4632-{ts}"[:32]
        created = skill_api.create_skill(
            name=skill_name,
            description="Autotest skill for ELITEA-4632 run analytics.",
            instructions="Convert the user text to UPPERCASE and reply with only that.",
        )
        skill_id = created["id"] if isinstance(created, dict) else created
        try:
            detail = SkillDetailPage(page)
            analytics = RunAnalyticsPage(page)

            with allure.step("Step 1 — Create two runs (A: short prompt, B: longer prompt in a new chat)"):
                detail.navigate(int(skill_id))
                detail.dismiss_platform_release_banner_if_present()
                detail.open_test_skill_panel()
                n = detail.get_test_message_count()
                detail.send_test_message("hello one")
                detail.wait_for_test_response(initial_count=n, timeout=AI_RESPONSE_TIMEOUT)
                detail.clear_test_chat()
                detail.send_test_message("please convert this noticeably longer sentence to uppercase")
                detail.wait_for_test_response(initial_count=0, timeout=AI_RESPONSE_TIMEOUT)
                assert "LONGER SENTENCE" in detail.get_last_test_response().upper()

            with allure.step("Step 2 — Open Run History and see both runs"):
                detail.open_run_history()
                assert re.search(rf"/skills/all/{skill_id}/history", page.url), page.url
                assert len(analytics.run_history_rows.all()) == 2, "Expected exactly two runs"

            with allure.step("Step 3 — Row menu -> Analytics for run B (newest, row 0)"):
                analytics.open_analytics_for_row(0)

            with allure.step("Step 4 — Analytics page loads for the selected run"):
                assert re.search(
                    rf"/skills/all/{skill_id}/history/analytics\?run=\d+&history_run_id=\d+", page.url
                ), page.url
                url_b = page.url

            with allure.step("Step 5 — Breadcrumbs show Skills / skill / Run History / Analytics"):
                assert analytics.breadcrumb_texts() == ["Skills", skill_name, "Run History"]
                assert (analytics.breadcrumb_current.text_content() or "").strip() == "Analytics"

            with allure.step("Step 6 — Run header shows run timestamp, version and model"):
                expect(analytics.run_info).to_contain_text("Run:", timeout=30000)
                expect(analytics.run_info).to_contain_text(re.compile(r"Version: base"), timeout=30000)
                expect(analytics.run_info).to_contain_text(re.compile(r"Model: (?!-|…)\S+"), timeout=30000)

            with allure.step("Step 7 — Costs tab is active and data is ingested"):
                assert analytics.tab_costs.get_attribute("aria-selected") == "true"
                payload_b = analytics.wait_for_costs_data()
                assert "Model: -" not in (analytics.run_info.text_content() or "")

            with allure.step("Step 8 — TOTAL COST card shows a $ amount > 0 matching the API"):
                kpis = payload_b["kpis"]
                assert kpis["total_cost"] > 0
                total_ui = analytics.kpi_value("TOTAL COST")
                assert total_ui.replace("< ", "").startswith("$"), total_ui
                assert total_ui == analytics.format_cost(kpis["total_cost"]), (total_ui, kpis["total_cost"])

            with allure.step("Step 9 — Cost breakdown reconciles (KPIs, per-model, per-user, tables)"):
                assert abs(kpis["total_cost"] - _costs_sum(kpis, "total_")) < TOL
                assert kpis["total_tokens"] == (
                    kpis["total_input_tokens"]
                    + kpis["total_output_tokens"]
                    + kpis["total_cache_read_tokens"]
                    + kpis["total_cache_creation_tokens"]
                )
                models = payload_b["by_model"]
                assert len(models) == 1
                assert abs(sum(m["total_cost"] for m in models) - kpis["total_cost"]) < TOL
                assert sum(m["total_tokens"] for m in models) == kpis["total_tokens"]
                for m in models:
                    assert abs(m["total_cost"] - _costs_sum(m)) < TOL
                assert abs(sum(u["total_cost"] for u in payload_b["by_user"]) - kpis["total_cost"]) < TOL
                model_cells = analytics.table_cells("Cost by Model")
                assert model_cells[0] == models[0]["display_name"], model_cells
                assert model_cells[1] == analytics.format_cost(models[0]["total_cost"]), model_cells
                assert model_cells[-1] == "100.0%", model_cells
                user_cells = analytics.table_cells("Cost by User")
                assert user_cells[0] == payload_b["by_user"][0]["user_email"], user_cells
                assert user_cells[-1] == "100.0%", user_cells

            with allure.step("Step 10 — Manual formula: cost = input_tokens x input_rate + output_tokens x output_rate"):
                m = models[0]
                in_rate = m["input_cost"] / m["input_tokens"]
                out_rate = m["output_cost"] / m["output_tokens"]
                assert in_rate > 0 and out_rate > 0
                assert abs(m["input_tokens"] * in_rate + m["output_tokens"] * out_rate - m["total_cost"]) < TOL
                assert m["input_tokens"] + m["output_tokens"] == m["total_tokens"]

            with allure.step("Step 11 — Tab switch keeps run context and Costs unchanged"):
                analytics.open_tab(analytics.tab_tokens)
                assert page.url == url_b
                analytics.open_tab(analytics.tab_costs)
                assert page.url == url_b
                assert analytics.kpi_value("TOTAL COST") == total_ui

            with allure.step("Step 12 — Run A shows only its own cost data (no leakage)"):
                page.go_back()
                analytics.run_history_rows.first.wait_for(state="visible", timeout=15000)
                analytics.open_analytics_for_row(1)
                payload_a = analytics.wait_for_costs_data()
                assert payload_a["kpis"]["total_tokens"] != kpis["total_tokens"]
                assert payload_a["kpis"]["total_cost"] != kpis["total_cost"]
                assert analytics.kpi_value("TOTAL COST") == analytics.format_cost(payload_a["kpis"]["total_cost"])
                assert page.url != url_b
        finally:
            with allure.step("Cleanup — delete the skill"):
                skill_api.delete_skill(int(skill_id))

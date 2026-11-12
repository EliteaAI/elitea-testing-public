"""Unit checks for RunAnalyticsPage.format_cost (mirror of the product's fmtCost tiers)."""

import pytest

from pages.run_analytics_page import RunAnalyticsPage

CASES = [
    (None, "-"),
    (float("nan"), "-"),
    (0, "$0.00"),
    (4e-6, "< $0.00001"),
    (-4e-6, "-< $0.00001"),
    (6.91e-5, "$0.00007"),
    (0.000512, "$0.0006"),
    (0.0003, "$0.0003"),
    (0.0042, "$0.0042"),
    (0.0051, "$0.0052"),
    (0.0061, "$0.0062"),
    (0.0079, "$0.0080"),
    (0.0099, "$0.0100"),
    (0.5, "$0.5000"),
    (12.345, "$12.35"),
    (2500, "$2.5K"),
    (3_400_000, "$3.4M"),
]


@pytest.mark.parametrize(("value", "expected"), CASES)
def test_format_cost_tiers(value, expected):
    assert RunAnalyticsPage.format_cost(value) == expected

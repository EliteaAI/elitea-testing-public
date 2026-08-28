"""Python ports of the Analytics surface's number formatters.

Every value the Settings -> Analytics surface renders — KPI card values, chart
hover-tooltip series values, table cells — goes through
``AnalyticCommonHelpers.fmtNum`` in EliteaUI
(``src/[fsd]/features/settings/lib/helpers/analyticsCommon.helpers.js``), unless
the call site passes an explicit ``formatter`` prop. A spec that asserts a
rendered value against the captured API response therefore has to apply the same
formatting to the raw number — ``3800`` renders as ``3.8K``.

Extracted here (from ``tests/ui/admin/test_analytics_overview_kpi_cards.py``,
its first consumer) when the ELITEA-2326/2327/2328/2329 chart-tooltip specs
took it past its third consumer — Hard Rule 7 (reuse before create): extract on
the third repetition rather than copy the literal a third time.
"""


def fmt_num(value) -> str:
    """Port of ``AnalyticCommonHelpers.fmtNum``.

    ``None`` renders as ``"-"`` (the product's own missing-data render),
    >= 1M as ``"{x}M"`` with one decimal, >= 1K as ``"{x}K"`` with one
    decimal, anything else as the plain number.
    """
    if value is None:
        return "-"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)

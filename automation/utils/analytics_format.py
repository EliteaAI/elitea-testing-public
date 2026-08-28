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

from decimal import ROUND_HALF_UP, Decimal
from math import isfinite


def _to_fixed(value: float, digits: int) -> str:
    """Port of JS ``Number.prototype.toFixed`` for this surface's magnitudes.

    Python's f-string and ``round()`` use banker's rounding (``1.25`` -> ``"1.2"``)
    while JS rounds a tie away from zero (``1.25`` -> ``"1.3"``). Quantizing the
    float's EXACT binary value with ``ROUND_HALF_UP`` reproduces the product's own
    output, so the expected string stays a mirror of the renderer rather than an
    approximation of it. ``:f`` forces fixed-point notation — ``str(Decimal)``
    switches to scientific below 1e-6, which the 8-decimal branch needs.
    """
    quantum = Decimal(1).scaleb(-digits)
    return f"{Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP):f}"


def fmt_cost(usd) -> str:
    """Port of ``AnalyticCommonHelpers.fmtCost``.

    Six magnitude branches plus an exact-zero branch, mirrored one-for-one from
    ``analyticsCommon.helpers.js``. Applying this to the value the SYSTEM
    returned is the same discipline as :func:`fmt_num` — the response stays the
    oracle, the mirror only renders it (`.agents/testing.md` § Fidelity policy).

    Non-numeric / missing / non-finite input renders ``"-"``, matching the JS
    ``usd == null || !Number.isFinite(usd)`` guard.
    """
    if isinstance(usd, bool) or not isinstance(usd, (int, float)) or not isfinite(usd):
        return "-"
    if usd == 0:
        return "$0.00"
    magnitude = abs(usd)
    sign = "-" if usd < 0 else ""
    if magnitude < 0.0001:
        return f"{sign}${_to_fixed(magnitude, 8)}"
    if magnitude < 0.01:
        return f"{sign}${_to_fixed(magnitude, 6)}"
    if magnitude < 1:
        return f"{sign}${_to_fixed(magnitude, 4)}"
    if magnitude < 1000:
        return f"{sign}${_to_fixed(magnitude, 2)}"
    if magnitude < 1_000_000:
        return f"{sign}${_to_fixed(magnitude / 1000, 1)}K"
    return f"{sign}${_to_fixed(magnitude / 1_000_000, 1)}M"


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

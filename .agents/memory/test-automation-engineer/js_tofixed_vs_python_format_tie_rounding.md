---
name: JS toFixed rounds ties away from zero, Python's :.1f rounds half to even
description: Porting a JS display formatter with an f-string silently diverges on exact ties — $1250 renders $1.3K, Python computes $1.2K.
aliases: [toFixed, fmtCost, fmtNum, banker's rounding, half-even, formatter port]
tags: [area/formatters, type/gotcha]
type: feedback
created: 2026-08-28
updated: 2026-08-28
---

## The trap

Asserting a rendered value against a captured API response means mirroring the product's
display formatter in Python. The naive port uses an f-string:

```python
f"{value / 1000:.1f}K"      # WRONG on ties
```

Python's format spec uses **round-half-to-even**; JS `Number.prototype.toFixed` rounds a tie
**away from zero**. `1250 / 1000 == 1.25` is exactly representable in binary, so:

| | 1.25 | renders |
|---|---|---|
| JS `(1.25).toFixed(1)` | half away | `"1.3"` |
| Python `f"{1.25:.1f}"` | half even | `"1.2"` |

The divergence only bites on specific live data, so a green run proves nothing about it —
which is exactly how it survives review.

## The fix

Quantize the float's EXACT binary value with `ROUND_HALF_UP`, and format with `:f`:

```python
from decimal import ROUND_HALF_UP, Decimal

def _to_fixed(value: float, digits: int) -> str:
    quantum = Decimal(1).scaleb(-digits)
    return f"{Decimal(value).quantize(quantum, rounding=ROUND_HALF_UP):f}"
```

`:f` matters independently: plain `str(Decimal)` switches to scientific notation below 1e-6,
which `fmtCost`'s 8-decimal branch needs (`$0.00000012`, not `$1.2E-7`).

Live in `automation/utils/analytics_format.py` (`fmt_cost`). ⚠️ `fmt_num` in that same module
still uses the naive `:.1f` — pre-existing, 3+ merged callers, reported rather than changed
inside a fix round.

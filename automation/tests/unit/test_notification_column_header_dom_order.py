"""Unit tests pinning that the Notifications Center column-header read is DOM-ordered.

Regression coverage for the fix-round-1 review finding on ELITEA-2255: the AFS
(step 5 / Coverage-Map Axis-1 row 7) claims the three data-column headers are
asserted to read "Type", "Notification", "Date & Time" **in that DOM order**,
but ``NotificationCenterPage.column_header_texts()`` originally read::

    return [self.column_header(field).inner_text().strip() for field in fields]

— one query per field, results emitted in the *caller's* order. That returns
``["Type", "Notification", "Date & Time"]`` for the caller's argument list no
matter how the DOM lays the columns out, so a swapped-column regression in
``NOTIFICATION_COLUMNS`` (EliteaUI ``src/pages/NotificationCenter/``) would sail
straight through the spec's ``== EXPECTED_COLUMNS`` comparison. The assertion
message said "in DOM order" while the code proved only label presence.

The fix reads all three headers through ONE comma-joined CSS union, which
Playwright matches with ``querySelectorAll`` semantics and therefore returns in
document order. These tests pin both halves of that contract without a browser:

1. **One query, not N** — the union shape is what carries the ordering guarantee.
2. **Argument order cannot leak into the result** — passing the fields reversed
   still yields DOM order. This is the assertion the old implementation fails.
"""

import types

import pytest
from pages.notification_center_page import NotificationCenterPage

#: DOM order the live Notifications Center renders (EliteaUI NOTIFICATION_COLUMNS).
DOM_FIELDS = ["event_type", "notification_text", "created_at"]
DOM_LABELS = ["Type", "Notification", "Date & Time"]

#: What each column header's testid resolves to, per field.
_LABEL_BY_SELECTOR = {
    NotificationCenterPage.NOTIFICATION_COLUMN_HEADER.format(field): label
    for field, label in zip(DOM_FIELDS, DOM_LABELS, strict=True)
}


class _FakeLocator:
    """Stand-in for a Playwright ``Locator`` over zero or more header cells.

    Models the one property under test: a CSS union resolves to its matches in
    **document order**, independent of how the selector's branches were ordered.
    """

    def __init__(self, selector: str):
        self._selector = selector
        branches = {part.strip() for part in selector.split(",")}
        # Document order — DOM_FIELDS, filtered to the branches actually asked for.
        self._texts = [
            f"  {_LABEL_BY_SELECTOR[sel]}  "  # padded: the helper must strip()
            for field in DOM_FIELDS
            if (sel := NotificationCenterPage.NOTIFICATION_COLUMN_HEADER.format(field)) in branches
        ]

    @property
    def first(self) -> "_FakeLocator":
        return self

    def wait_for(self, **_kwargs) -> None:
        return None

    def all_inner_texts(self) -> list[str]:
        return list(self._texts)

    def inner_text(self) -> str:
        # Present so the PRE-FIX per-field implementation runs against this fake
        # too — that is what lets these tests go red on the old code.
        return self._texts[0]


class _FakePage:
    """Records every selector the page object queries."""

    def __init__(self):
        self.selectors: list[str] = []

    def locator(self, selector: str) -> _FakeLocator:
        self.selectors.append(selector)
        return _FakeLocator(selector)


def _read(fields: list[str]) -> tuple[list[str], _FakePage]:
    """Invoke the real ``column_header_texts`` against a fake page."""
    page = _FakePage()
    page_object = types.SimpleNamespace(
        page=page,
        NOTIFICATION_COLUMN_HEADER=NotificationCenterPage.NOTIFICATION_COLUMN_HEADER,
        column_header=lambda field: page.locator(
            NotificationCenterPage.NOTIFICATION_COLUMN_HEADER.format(field)
        ),
    )
    texts = NotificationCenterPage.column_header_texts(page_object, fields)
    return texts, page


def test_column_header_texts_returns_dom_order_for_dom_ordered_argument():
    """Baseline: the happy path the spec exercises still reads correctly."""
    texts, _page = _read(DOM_FIELDS)
    assert texts == DOM_LABELS


@pytest.mark.parametrize(
    "fields",
    [
        pytest.param(list(reversed(DOM_FIELDS)), id="reversed"),
        pytest.param(["notification_text", "created_at", "event_type"], id="rotated"),
    ],
)
def test_argument_order_cannot_change_the_result(fields):
    """THE regression assertion — red on the pre-fix per-field implementation.

    The old body returned ``[label(f) for f in fields]``, i.e. the argument
    order verbatim, so a shuffled argument list produced a shuffled result and
    the spec's ``==`` comparison was blind to the DOM. The union read must
    return document order regardless.
    """
    texts, _page = _read(fields)
    assert texts == DOM_LABELS, (
        "column_header_texts() must report DOM order, not the caller's argument "
        f"order — passing {fields} returned {texts}"
    )


def test_headers_are_read_through_a_single_union_query():
    """The union query IS the ordering guarantee — N per-field queries are not.

    Pinned so a future 'simplification' back to a per-field loop (which reads
    identically at the call site) cannot silently drop the order coverage.
    """
    _texts, page = _read(DOM_FIELDS)
    assert len(page.selectors) == 1, (
        "Expected exactly one union query carrying the DOM-order guarantee, got "
        f"{len(page.selectors)}: {page.selectors}"
    )
    selector = page.selectors[0]
    for field in DOM_FIELDS:
        assert NotificationCenterPage.NOTIFICATION_COLUMN_HEADER.format(field) in selector, (
            f"Union selector is missing the {field!r} column header: {selector}"
        )

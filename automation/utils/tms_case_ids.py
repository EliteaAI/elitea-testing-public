"""TMS case-id reporting for Allure — the `@pytest.mark.tms(...)` marker.

A test declares the TMS case(s) it covers right in its source::

    @pytest.mark.tms("ELITEA-1950")
    def test_mcp_attach_via_tools_section(page):
        ...

The hooks below turn that marker into three things in the Allure report:

1. a **name prefix** — ``[ELITEA-1950] test_mcp_attach_via_tools_section``
2. an Allure **tag** per case id, so the report can be filtered by case
3. an Allure **link** per case id (``link_type=TEST_CASE``), rendered as a
   clickable TMS reference on the test-case page

Nothing here reads an index at runtime: the ids are hardcoded in the tests, so
a local run and a CI run produce identical names.

Several ids are allowed when one test covers several cases
(``@pytest.mark.tms("ELITEA-2149", "ELITEA-2461")`` → ``[ELITEA-2149 ELITEA-2461] …``).
When cases differ *per parameter*, mark the ``pytest.param`` instead of the
function::

    @pytest.mark.parametrize("prompt", [
        pytest.param("minimal", marks=pytest.mark.tms("ELITEA-1111")),
        pytest.param("detailed", marks=pytest.mark.tms("ELITEA-2222")),
    ])

Invariants worth knowing before changing this module:

* ``historyId`` / ``fullName`` / ``testCaseId`` are derived by allure-pytest from
  the pytest **nodeid**, never from the display name — so prefixing does not
  break Allure history, trends, retry grouping, or the TMS ``automation_test_id``
  correlation key (`.agents/test-automation.yaml` § backwrite_on_done).
* An explicit ``@allure.title(...)`` on a test always wins; it is never prefixed.
* The title is applied in ``runtest_call``/``runtest_teardown``, not in
  ``runtest_setup``: allure-pytest's own listener rewrites ``test_result.name``
  at the end of setup, so anything set earlier is discarded.
"""

import allure
import pytest
from allure_commons.types import LabelType, LinkType

#: Marker name tests use to declare their TMS case id(s).
TMS_MARKER = "tms"

#: Case ids are rendered as links to the TMS cases repo. The repo is private, so
#: the link only resolves for signed-in team members — the tag and the name
#: prefix carry the id for everyone else.
TMS_CASE_URL = "https://github.com/EliteaAI/onetest-ai-tm-Elitea/search?q={case_id}&type=code"


def tms_case_ids(item) -> list[str]:
    """Return the de-duplicated, sorted TMS case ids declared on ``item``.

    Collects from every ``tms`` marker in scope — function, class, module-level
    ``pytestmark``, and ``pytest.param(marks=...)`` — so class- and param-level
    declarations both work.
    """
    case_ids: list[str] = []
    for mark in item.iter_markers(name=TMS_MARKER):
        case_ids.extend(str(arg) for arg in mark.args)
    # dict.fromkeys de-duplicates while keeping it deterministic via sorted()
    return sorted(dict.fromkeys(case_ids))


def format_title(case_ids: list[str], test_name: str) -> str:
    """Build the prefixed Allure title: ``[ELITEA-1 ELITEA-2] test_name``."""
    return f"[{' '.join(case_ids)}] {test_name}"


def _apply_title(item) -> None:
    """Prefix the Allure display name, unless the test sets its own title."""
    case_ids = tms_case_ids(item)
    if not case_ids:
        return

    # An explicit @allure.title() is a deliberate human choice — leave it alone.
    test_function = getattr(item, "function", None)
    if getattr(test_function, "__allure_display_name__", None):
        return

    # item.name (not originalname) keeps the parametrize id: test_x[github].
    allure.dynamic.title(format_title(case_ids, item.name))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        f"{TMS_MARKER}(*case_ids): TMS case id(s) this test covers, "
        "e.g. tms('ELITEA-1950'). Surfaces in Allure as a name prefix, tag and link.",
    )


def pytest_collection_modifyitems(config, items):
    """Attach an Allure tag + link per declared case id."""
    for item in items:
        case_ids = tms_case_ids(item)
        if not case_ids:
            continue

        item.add_marker(pytest.mark.allure_label(*case_ids, label_type=LabelType.TAG))
        for case_id in case_ids:
            item.add_marker(
                pytest.mark.allure_link(
                    TMS_CASE_URL.format(case_id=case_id),
                    name=case_id,
                    link_type=LinkType.TEST_CASE,
                )
            )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    # Must run after setup: allure-pytest's listener rewrites test_result.name
    # at the end of pytest_runtest_setup, discarding anything set before that.
    _apply_title(item)
    yield


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_runtest_teardown(item, nextitem):
    # Skipped tests never reach runtest_call, but teardown runs for every
    # outcome — so this is what keeps skips prefixed too.
    _apply_title(item)
    yield

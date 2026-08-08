"""Pipeline Tags — Add and Filter UI test (ELITEA-2013).

Creates two disposable pipelines with tags via the create-pipeline form's
own Tags field (typing + Enter — the tag-add flow under test; the API
create payload has no ``tags`` kwarg), verifies the tag chips render both
in the form and on each dashboard card, then verifies the page-header Tags
filter panel narrows the grid to exactly the pipelines carrying the clicked
tag — for a single-match tag and a two-match shared tag — and that
"Clear all" restores the unfiltered grid and strips the ``tags`` URL param.

See test-specs/pipelines/l2_pipeline-tags-add-and-filter_ELITEA-2013.md
"""

import logging
import uuid
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipeline_form_page import PipelineFormPage
from pages.pipelines_list_page import PipelinesListPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000
FORM_SAVE_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.pipelines")


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/ELITEA-2013_pipeline-tags-add-and-filter.md",
    "onetest-ai Test Case link",
)
def test_pipeline_tags_add_and_filter(page, pipeline_api):
    """Create 2 pipelines with shared/unique tags; verify tag chips + filter narrowing.

    Steps (see AFS for full detail):
    1. Create Pipeline 1 (tags: regression, smoke) via the create form's Tags
       field; verify both chips render in the form.
    2. Create Pipeline 2 (tags: regression, integration); verify both chips
       render in the form.
    3. Navigate to the dashboard; verify both pipelines visible, each card
       showing its own tags.
    4. Filter by "smoke" — verify exactly Pipeline 1 is shown, URL carries
       ``tags=smoke``.
    5. Clear filter, filter by shared tag "regression" — verify exactly both
       pipelines are shown.
    6. Clear filter — verify URL reverts (no ``tags`` param) and the full
       list (including both disposable pipelines) is restored.
    7. Zero console errors across the whole flow.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    tag_regression = f"regression_{unique_suffix}"
    tag_smoke = f"smoke_{unique_suffix}"
    tag_integration = f"integration_{unique_suffix}"
    pipeline_1_name = f"tagged_pipe_1_{unique_suffix}"
    pipeline_2_name = f"tagged_pipe_2_{unique_suffix}"

    list_page = PipelinesListPage(page)
    form_page = PipelineFormPage(page)
    detail_page = PipelineDetailPage(page)

    created_pipeline_ids: list[int] = []

    # Console-error capture across the whole flow (tag creation + filtering),
    # mirroring test_skill_tag_filter.py's pattern (case's side-channel check).
    # Filters out the single known-and-not-filed cosmetic React dev-mode
    # warning ("Invalid value for prop `sx` on <svg>", fired from the shared
    # TagEditor's SvgCheckedIcon when selecting an existing tag from the
    # autocomplete dropdown — same component/warning already documented for
    # Skills, ELITEA-1740 AFS Known Defects #2) so a real regression isn't
    # masked by an expected, harmless warning.
    console_errors = []

    def _is_known_sx_svg_warning(msg) -> bool:
        text = msg.text
        return "Invalid value for prop" in text and "sx" in text and "svg" in text.lower()

    def _on_console(msg):
        if msg.type == "error" and not _is_known_sx_svg_warning(msg):
            console_errors.append(msg)

    page.on("console", _on_console)

    try:
        with allure.step(
            "Step 1 — Create pipeline 'tagged_pipe_1' with tags "
            "[regression, smoke]; verify both tag chips render in the form"
        ):
            list_page.navigate_to_create()
            form_page.wait_for_page_load()
            form_page.fill_form(
                name=pipeline_1_name,
                description="ELITEA-2013 pipeline tags add-and-filter test — pipeline 1",
            )
            form_page.add_tag(tag_regression)
            form_page.add_tag(tag_smoke)
            pipeline_1_form_tags = {
                (form_page.tags_chip.nth(i).text_content() or "").strip().lower()
                for i in range(form_page.tags_chip.count())
            }
            assert pipeline_1_form_tags == {tag_regression.lower(), tag_smoke.lower()}, (
                f"Pipeline 1's form should show tags {{{tag_regression!r}, {tag_smoke!r}}}, "
                f"got: {pipeline_1_form_tags!r}"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.wait_for_detail_page_load()
            pipeline_1_id = int(detail_page.get_pipeline_id())
            created_pipeline_ids.append(pipeline_1_id)
            logger.info("Pipeline 1 created — id=%s", pipeline_1_id)

        with allure.step(
            "Step 2 — Create pipeline 'tagged_pipe_2' with tags "
            "[regression, integration]; verify both tag chips render in the form"
        ):
            list_page.navigate_to_create()
            form_page.wait_for_page_load()
            form_page.fill_form(
                name=pipeline_2_name,
                description="ELITEA-2013 pipeline tags add-and-filter test — pipeline 2",
            )
            form_page.add_tag(tag_regression)
            form_page.add_tag(tag_integration)
            pipeline_2_form_tags = {
                (form_page.tags_chip.nth(i).text_content() or "").strip().lower()
                for i in range(form_page.tags_chip.count())
            }
            assert pipeline_2_form_tags == {tag_regression.lower(), tag_integration.lower()}, (
                f"Pipeline 2's form should show tags {{{tag_regression!r}, {tag_integration!r}}}, "
                f"got: {pipeline_2_form_tags!r}"
            )
            form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)
            detail_page.wait_for_detail_page_load()
            pipeline_2_id = int(detail_page.get_pipeline_id())
            created_pipeline_ids.append(pipeline_2_id)
            logger.info("Pipeline 2 created — id=%s", pipeline_2_id)

        with allure.step(
            "Step 3 — Navigate to Pipelines dashboard; verify both pipelines "
            "visible, each card showing its own tags"
        ):
            list_page.navigate()
            assert list_page.pipeline_exists_in_list(pipeline_1_name), (
                f"{pipeline_1_name!r} should be visible in the grid after creation"
            )
            assert list_page.pipeline_exists_in_list(pipeline_2_name), (
                f"{pipeline_2_name!r} should be visible in the grid after creation"
            )
            pipeline_1_card_tags = {t.lower() for t in list_page.get_card_tags(pipeline_1_name)}
            pipeline_2_card_tags = {t.lower() for t in list_page.get_card_tags(pipeline_2_name)}
            assert pipeline_1_card_tags == {tag_regression.lower(), tag_smoke.lower()}, (
                f"Pipeline 1's card should show tags {{{tag_regression!r}, {tag_smoke!r}}}, "
                f"got: {pipeline_1_card_tags!r}"
            )
            assert pipeline_2_card_tags == {tag_regression.lower(), tag_integration.lower()}, (
                f"Pipeline 2's card should show tags {{{tag_regression!r}, {tag_integration!r}}}, "
                f"got: {pipeline_2_card_tags!r}"
            )

        with allure.step(
            "Step 4 — Filter by tag 'smoke' — verify only 'tagged_pipe_1' "
            "appears; URL carries the tags query param"
        ):
            list_page.filter_by_tag(tag_smoke, timeout=UI_ELEMENT_TIMEOUT)
            assert list_page.get_card_names() == [pipeline_1_name], (
                f"'smoke' filter should show exactly [{pipeline_1_name!r}], "
                f"got: {list_page.get_card_names()!r}"
            )
            filtered_tags_param = parse_qs(urlparse(page.url).query).get("tags[]")
            assert filtered_tags_param == [tag_smoke], (
                f"URL should carry tags[]={tag_smoke!r} after filtering, got: {page.url}"
            )

        with allure.step(
            "Step 5 — Clear filter, then filter by shared tag 'regression' "
            "— verify both pipelines appear"
        ):
            list_page.clear_tag_filter(timeout=UI_ELEMENT_TIMEOUT)
            list_page.filter_by_tag(tag_regression, timeout=UI_ELEMENT_TIMEOUT)
            filtered_names = list_page.get_card_names()
            assert sorted(filtered_names) == sorted([pipeline_1_name, pipeline_2_name]), (
                f"'regression' filter should show exactly "
                f"[{pipeline_1_name!r}, {pipeline_2_name!r}], got: {filtered_names!r}"
            )

        with allure.step(
            "Step 6 — Remove tag filter — verify URL reverts and all "
            "pipelines (including both disposable ones) are listed again"
        ):
            list_page.clear_tag_filter(timeout=UI_ELEMENT_TIMEOUT)
            assert "tags" not in parse_qs(urlparse(page.url).query), (
                f"URL should not carry a tags param after clearing the filter, got: {page.url}"
            )
            assert list_page.pipeline_exists_in_list(pipeline_1_name), (
                f"{pipeline_1_name!r} should be visible again after clearing the filter"
            )
            assert list_page.pipeline_exists_in_list(pipeline_2_name), (
                f"{pipeline_2_name!r} should be visible again after clearing the filter"
            )

        with allure.step("Step 7 — Verify no console errors during the whole create/filter flow"):
            assert not console_errors, (
                "Expected no console errors during tag creation/filtering, got: "
                f"{[m.text for m in console_errors]}"
            )
    finally:
        try:
            page.remove_listener("console", _on_console)
        except Exception:
            pass
        for pid in created_pipeline_ids:
            try:
                pipeline_api.delete_pipeline(pid)
                logger.info("Cleanup: deleted pipeline id=%s", pid)
            except Exception as exc:
                logger.warning("Cleanup failed for pipeline id=%s (non-fatal): %s", pid, exc)

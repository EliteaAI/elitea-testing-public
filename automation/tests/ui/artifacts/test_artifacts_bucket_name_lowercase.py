"""UI Test for ELITEA-1812 — A Bucket Name Typed in UPPERCASE Is Stored and
Displayed in Lowercase.

Regression test for the bucket-name case-conversion axis, which no existing
spec touches: ELITEA-1808/1809/1810/1811/1817 all drive the same
``/artifacts/create-bucket`` form but every one of them types an
already-lowercase generated name, so nothing in the suite proves that what is
typed and what is stored can differ by case.

Test flow (6 case steps, 1:1 with the AFS's Test Steps):
1. Navigate to Artifacts.
2. Click the create-bucket folder icon — full page nav to
   ``/artifacts/create-bucket``, not a modal, and headed ``New Bucket``. That
   heading is the assertion that matters: the SAME route serves the edit form
   (``CreateBucket.jsx:214`` switches the heading off ``currentBucket``), so
   the URL alone cannot prove the case's "'New Bucket' form opens".
3. Type an ALL-UPPERCASE bucket name — the field preserves it verbatim
   (no client-side lowercasing; the yup schema explicitly allows A-Z).
4. Save — the creation POST returns 200 AND its response body's ``name`` is
   the all-lowercase form. The response is the storage layer's own statement
   and is the only honest oracle for the case's "stored lowercase" claim: the
   DOM alone cannot distinguish "stored lowercase" from "stored uppercase,
   rendered lowercased".
5. Click the sidebar's Artifacts entry — back at the Artifacts root.
6. The bucket is listed in lowercase: the lowercase-keyed row testid exists,
   the uppercase-keyed one does NOT (count 0 — without the negative half a UI
   rendering both forms would pass), and the row's own text is all-lowercase.

Where the conversion happens: the BACKEND. ``CreateBucket.jsx`` posts
``values.name.trim()`` verbatim — there is no ``toLowerCase()`` anywhere in
the form — so Step 3's "still uppercase in the input" assertion pins the
conversion to the server and fails loudly if a future release moves it into
the field.

Case-text divergences asserted as the LIVE contract (reverse-masking guard):
- The case's literal ``BUCKET-TEST`` is a placeholder — the same established
  convention as ELITEA-1808/1810/1832/1839. A unique uppercase name is
  generated per run and the expectation is DERIVED from it
  (``typed.lower()``), never hardcoded, so the assertion keeps meaning "the
  system lowercased it".

Fidelity: no substitution of any kind. The bucket is created through the real
UI (the ``artifact_bucket`` API fixture is deliberately NOT used — seeding via
the API would substitute the very producer whose case-handling this case
observes), and the "stored" assertion reads the real POST response.

AFS: test-specs/artifacts/l3_bucket-name-stored-lowercase-uppercase-input_ELITEA-1812.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p3: low priority (matches case priority "medium" / AFS l3)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_name_lowercase.py -v
"""

import logging
import re
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, rows
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
SAVE_RESPONSE_TIMEOUT = 20_000     # bucket-creation POST
# The project under test carries ~970 buckets (#636) and the left panel
# refetches the WHOLE list after a save, so the bucket-list waits get their own
# larger budget — still a condition wait on the row's own testid, never a sleep.
BUCKET_LIST_TIMEOUT = 45_000

# ---------------------------------------------------------------------------
# Form heading (ELITEA-1816's AFS Step 11 established this): the SINGLE route
# ``/artifacts/create-bucket`` serves BOTH flows — ``CreateBucket.jsx:214``
# renders ``currentBucket ? 'Edit bucket' : 'New Bucket'`` — so the URL alone
# does NOT prove the case's "'New Bucket' form opens". The heading text does.
# ---------------------------------------------------------------------------
CREATE_FORM_HEADING = "New Bucket"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation + Name Normalization")
class TestArtifactBucketNameLowercase:
    """ELITEA-1812 — an uppercase-typed bucket name is stored and displayed
    entirely in lowercase."""

    @pytest.mark.p3
    @allure.title(
        "A bucket name typed in UPPERCASE is stored (POST response) and "
        "displayed (bucket list) entirely in lowercase"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1812_bucket-name-always-stored-in-lowercase.md",
        "onetest-ai Test Case link",
    )
    def test_uppercase_bucket_name_is_stored_and_displayed_lowercase(
        self, page, artifact_api
    ):
        """Drive the case's 6 steps end-to-end against the live system."""
        typed_name = f"AUTOTEST-1812-{int(time.time())}"
        expected_name = typed_name.lower()

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)
        bucket_created = False

        try:
            with allure.step("Step 1 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click the create-bucket folder icon above the bucket "
                "list — verify it opens the 'New Bucket' form as a full page "
                "navigation, not a modal. The route is shared by the create "
                "and edit forms, so the heading text is what proves it is the "
                "CREATE form"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {page.url!r}"
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == CREATE_FORM_HEADING
                ), (
                    f"The form should be headed {CREATE_FORM_HEADING!r} — the "
                    "URL is shared with the Edit form "
                    "(CreateBucket.jsx:214 switches the heading off "
                    "`currentBucket`), so it cannot prove the case's "
                    "\"'New Bucket' form opens\" on its own"
                )

            with allure.step(
                f"Step 3 — Enter the bucket name in UPPERCASE ({typed_name!r}; "
                "the case's literal 'BUCKET-TEST' is a placeholder) — verify "
                "the field accepts and PRESERVES the uppercase input, i.e. no "
                "client-side lowercasing happens in the field"
            ):
                artifacts_page.fill_bucket_name(typed_name)
                assert artifacts_page.bucket_name_input.input_value() == typed_name, (
                    "The Name field should preserve the typed uppercase name "
                    f"{typed_name!r} verbatim (the conversion is server-side), "
                    f"got {artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                "Step 4 — Click Save — verify the bucket-creation POST returns "
                "200 AND its response body names the bucket in LOWERCASE (the "
                "'stored' half of the case; there is no toast on bucket save, "
                "and the DOM cannot distinguish stored-lowercase from "
                "rendered-lowercase)"
            ):
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=SAVE_RESPONSE_TIMEOUT
                )
                bucket_created = True
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got "
                    f"{create_response.status} for {create_response.url}"
                )
                stored_name = create_response.json()["name"]
                assert stored_name == expected_name, (
                    f"The backend should store the typed {typed_name!r} as "
                    f"{expected_name!r}; the creation response says "
                    f"{stored_name!r}"
                )
                # AFS drift, corrected here and amended in the AFS: the AFS's
                # Step 4 expected the save to land on
                # ``/artifacts?bucket=<stored name>`` (the form's
                # PENDING_BUCKET_SESSION_KEY auto-select). Live in this run the
                # save lands on the bare ``/artifacts`` root — 87 polls over
                # 45s never saw a ``?bucket=`` param — so asserting it would
                # have been asserting the analyst's probe rather than the
                # product. The case's own claim ("Bucket is saved") is carried
                # by the POST assertions above.
                expect(page).to_have_url(
                    re.compile(r"/artifacts(\?.*)?$"), timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 5 — Click 'Artifacts' in the left sidebar — verify the "
                "app is on the Artifacts root with the bucket list rendered. "
                "Save already landed on the bare /artifacts root (see Step 4), "
                "so this is a same-route navigation: the assertion is that the "
                "sidebar entry keeps us on the root with the list visible, NOT "
                "that a ?bucket= param was cleared"
            ):
                artifacts_page.sidebar_menu_item("artifacts").click()
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert page.url.rstrip("/").endswith("/artifacts"), (
                    "The sidebar entry should navigate to the Artifacts root "
                    f"(no ?bucket= param), got {page.url!r}"
                )

            with allure.step(
                f"Step 6 — Verify the bucket is listed as {expected_name!r} "
                "(all lowercase): the lowercase-keyed row exists, NO "
                "uppercase-keyed row exists, and the row's own text carries no "
                "uppercase character"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    expected_name, timeout=BUCKET_LIST_TIMEOUT
                )
                assert artifacts_page.count_bucket_rows(expected_name) == 1, (
                    f"Expected exactly one {expected_name!r} row in the bucket "
                    "list (the row testid is derived from the STORED name, so "
                    "its presence is itself a name assertion)"
                )
                assert artifacts_page.count_bucket_rows(typed_name) == 0, (
                    f"No row keyed by the typed uppercase name {typed_name!r} "
                    "should exist — without this negative half, a UI rendering "
                    "BOTH forms would pass"
                )
                row_text = (
                    artifacts_page.bucket_row(expected_name).text_content() or ""
                ).strip()
                assert row_text == expected_name, (
                    f"The bucket row should read exactly {expected_name!r}, got "
                    f"{row_text!r}"
                )
                assert row_text == row_text.lower(), (
                    f"The displayed bucket name must contain no uppercase "
                    f"character, got {row_text!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole create + list flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the bucket name "
                    f"lowercase flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Teardown — the bucket is this test's own mutation and the case
            # never deletes it, so it must not leak into a project already
            # carrying ~970 buckets (#636). The UI delete path is the one
            # confirmed working; ArtifactAPI.delete_bucket() 404s in this
            # environment (#636) and is only the fallback.
            if bucket_created:
                try:
                    artifacts_page.delete_bucket_via_menu(
                        expected_name, timeout=BUCKET_LIST_TIMEOUT
                    )
                    logger.info(
                        "Teardown: deleted bucket '%s' via the UI", expected_name
                    )
                except Exception as ui_exc:  # noqa: BLE001 - teardown must not mask
                    logger.warning(
                        "Teardown: UI delete of '%s' failed (%s) — falling back "
                        "to the API client", expected_name, ui_exc,
                    )
                    try:
                        artifact_api.delete_bucket(expected_name)
                    except Exception as api_exc:  # noqa: BLE001
                        logger.warning(
                            "Teardown: API delete of '%s' also failed (known "
                            "defect #636 — delete_bucket() 404s in dev "
                            "regardless): %s", expected_name, api_exc,
                        )

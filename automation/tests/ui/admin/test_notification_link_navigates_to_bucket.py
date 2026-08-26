"""UI test — Clicking a bucket retention-warning notification link navigates to the correct bucket.

Test case: ELITEA-2263
AFS: test-specs/settings-notifications/
     l2_notification-bucket-retention-link-navigates-to-bucket_ELITEA-2263.md

Read-only by construction: the flow is GET-only — clicking the in-message link
mutates neither the notification nor the bucket — so this spec seeds nothing and
cleans up nothing beyond closing the tab it opened.

Nothing is hardcoded
--------------------
The notification id, the bucket name, the project id and the expected URL all
come from the product's own list response and its own rendered ``href``. The DEV
account carries 41 retention warnings and most of them name autotest buckets the
very retention policy they announce has already deleted, so the spec DISCOVERS a
warning whose bucket still exists (probing the product's own artifacts API) and
fails loudly, never skips, when none is.

The link opens a NEW TAB
------------------------
``NotificationListItemMessage.jsx`` renders the segment as
``<Link target="_blank" rel="noopener noreferrer">`` with no ``onClick``, so the
click is awaited with ``context.expect_page()``; an in-tab ``wait_for_url``
would hang.

The URL alone is NOT the assertion
----------------------------------
Landing on ``/artifacts?bucket=<name>`` proves only that the href was followed.
A deleted bucket produces exactly that URL with no bucket row and no tree panel
(measured live on ``autotest-1816-1787504970``), so this spec additionally
requires the bucket to be LISTED and OPENED — its file tree rendered, either the
"No files in this bucket" empty label or a non-empty file list.

Substitution declaration
------------------------
ZERO substitution of the system under test — no ``page.route``, no
``route.fulfill``, no ``page.evaluate``, no monkeypatching, no stubbed client.
``ArtifactAPI.bucket_exists()`` is a TRANSIT read of the product's own artifacts
endpoint that only selects WHICH notification to exercise (a precondition); the
case's own observable — what clicking the link does — is still produced live by
the product.

Markers:
    - ui: requires browser
    - admin: notification-centre suite (matches its sibling specs)
    - p2: priority (AFS metadata l2 — case priority `medium`)
    - regression
"""

import logging
import re
import urllib.parse

import allure
import pytest
from api.client import ArtifactAPI
from config import settings
from pages.artifacts_page import ArtifactsPage
from pages.notification_center_page import PAGE_INFO_PATTERN, NotificationCenterPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression]

#: Template token every ``bucket_expiration_warning`` message carries. Fed to the
#: product's OWN server-side search field; the returned rows are still filtered on
#: ``event_type`` below, so a coincidental text match can never be selected.
RETENTION_SEARCH_TERM = "will start deleting files"

#: The notification ``event_type`` this case is about.
RETENTION_EVENT_TYPE = "bucket_expiration_warning"

#: Background resources documented as environmental noise on this DEV backend
#: (`.agents/testing.md` § Known issues / § Unconfirmed — the recurring
#: unrelated-resource console-error class). Neither is requested by the flow under
#: test: the first is the secrets probe every project mount fires, the second the
#: project-info fetch the project switcher fires.
#:
#: Each entry is a (status-text, URL-marker) PAIR and both halves must match —
#: the exact signature observed live on 2026-08-26 and recorded in this case's AFS
#: § Network Behavior. Scoping by URL alone would swallow every future status on
#: those two resources (a 500 on the secrets probe, a 404 on project-info), which
#: is masking, not noise handling — the same fix the credentials specs' `#554`
#: filter carries (`tests/unit/test_credentials_console_filters_scope.py`) and the
#: shape every sibling spec uses (`_is_known_secrets_403`, chat suite).
#: Everything else — any other status, any other resource, anything on the
#: endpoints this flow drives — still fails the test.
KNOWN_BACKGROUND_NOISE_SIGNATURES = (
    ("status of 403", "/secrets/secrets/default/"),
    ("status of 500", "/project_info/prompt_lib/"),
)

#: Substring shared by the artifacts REST calls the bucket page makes.
ARTIFACTS_URL_MARKER = "/artifacts/"

#: The project a bucket-page artifacts READ was scoped to. The UI's artifacts REST
#: calls carry it as a query param, not a path segment — observed live 2026-08-26:
#: ``/artifacts/s3/?project_id=399&format=json`` (bucket list) and
#: ``/artifacts/s3/{bucket}?project_id=399&format=json`` (bucket contents). Used to
#: prove the new tab rendered the artifacts of the NOTIFICATION's own project, which
#: the landing path alone cannot: when no project switch is required the product
#: serves the bare ``/artifacts`` form, naming no project at all.
ARTIFACTS_PROJECT_SCOPE_RE = re.compile(r"/artifacts/s3/[^?#]*\?(?:[^#]*&)?project_id=(\d+)")

#: Characters ``encodeURIComponent`` leaves untouched, so the expected href can be
#: rebuilt byte-for-byte from the notification's own ``meta.bucket_name``.
ENCODE_URI_COMPONENT_SAFE = "!~*'()-._"

#: URL shape of the popup's OWN project-scoped BUCKET-LIST read — the call whose
#: response the artifacts page needs before it can render ANY bucket row, and
#: therefore the condition Step 5 waits on instead of a magic element budget.
#: The LIST call carries an empty bucket segment (``/artifacts/s3/?project_id=399``);
#: the per-bucket CONTENTS call (``/artifacts/s3/{bucket}?project_id=399``) is a
#: different, later request and must NOT satisfy this gate.
#:
#: Why the gate exists (measured live 2026-08-26, gate failure of this spec):
#: ``Artifacts.jsx`` renders its EMPTY state ("Buckets: 0 / No buckets created yet")
#: for the whole in-flight window, because the ``?bucket=`` deep-link selection can
#: only resolve once ``allBuckets`` has loaded. In the DEV account's project 399
#: (1 049 buckets, ~205 KB) that list call alone measured 10.5-12.7 s from the API
#: client and 14.8-18.0 s end-to-end in a fresh tab on an IDLE machine, so a
#: fixed 20 s element budget left no margin at all and failed on a busy run.
BUCKET_LIST_READ_URL_RE_TEMPLATE = r"/artifacts/s3/\?(?:[^#]*&)?project_id={}(?:&|$|#)"

POPUP_URL_TIMEOUT = 30_000

#: Budget for the bucket-list READ above. Deliberately generous: the wait is
#: condition-based (it returns the instant the response event fires), it scales
#: with the project's bucket count, and an unused budget costs nothing.
BUCKET_LIST_READ_TIMEOUT = 120_000

#: Budget for RENDERING once that read has landed — a non-virtualized list of
#: ~1 000 rows plus the bucket tree. Raised from 20 s after the gate failure above:
#: 20 s was below the *fetch* cost alone, so it never measured rendering at all.
POPUP_ELEMENT_TIMEOUT = 60_000

#: Budget for resolving which of two MUTUALLY EXCLUSIVE tree outcomes rendered —
#: the "No files in this bucket" label (empty bucket) or file rows (non-empty one).
#: Kept at the original 20 s ON PURPOSE and deliberately NOT tied to
#: :data:`POPUP_ELEMENT_TIMEOUT`: by this point the page has already rendered (the
#: bucket-list read landed and the bucket row is visible), so this is a race
#: resolution, not a page-load wait — and every second of it is spent in full on
#: the non-empty branch before the file-count fallback runs.
BUCKET_TREE_PROBE_TIMEOUT = 20_000


def _is_known_background_noise(message: str) -> bool:
    """True only for an exact (status, resource) pair from
    :data:`KNOWN_BACKGROUND_NOISE_SIGNATURES`.

    *message* is a line rendered by ``utils.console_errors.format_console_message``
    (``"<type>: <text> @ <url>"``), so the status half matches the message TEXT
    ("...responded with a status of 403 ()") and the marker half the URL. Both must
    match: a 500 on the secrets probe, or a 403 on project-info, is NOT this noise
    and must fail the test.
    """
    return any(
        status in message and marker in message
        for status, marker in KNOWN_BACKGROUND_NOISE_SIGNATURES
    )


def _flow_console_errors(messages: list[str]) -> list[str]:
    """Drop the two documented background-resource noise signatures, keep everything else."""
    return [message for message in messages if not _is_known_background_noise(message)]


def _bucket_list_read_matcher(project_id) -> re.Pattern[str]:
    """Regex matching the popup's project-scoped bucket-LIST read for *project_id*.

    Built from :data:`BUCKET_LIST_READ_URL_RE_TEMPLATE`, so it matches
    ``/artifacts/s3/?project_id=<pid>&format=json`` and rejects both the
    per-bucket contents call (``/artifacts/s3/{bucket}?project_id=<pid>``) and any
    other project's list call — a prefix-collision-safe project match, not a
    substring one.
    """
    return re.compile(BUCKET_LIST_READ_URL_RE_TEMPLATE.format(re.escape(str(project_id))))


def _expected_retention_href(row: dict) -> str:
    """Rebuild the href ``resolveHref()`` must have produced for *row*.

    Mirrors ``notification.helpers.js`` for ``bucket_expiration_warning``:
    ``{base}/{notification.project_id}/artifacts?bucket={encodeURIComponent(meta.bucket_name)}``.
    Every component is the notification's OWN data, read out of the list response.
    """
    bucket_name = row["meta"]["bucket_name"]
    encoded = urllib.parse.quote(bucket_name, safe=ENCODE_URI_COMPONENT_SAFE)
    return f"{settings.app_base_url.rstrip('/')}/{row['project_id']}/artifacts?bucket={encoded}"


class TestNotificationBucketRetentionLinkNavigation:
    """ELITEA-2263 — the retention-warning link opens the bucket it names."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-notifications/ELITEA-2263_clicking-a-bucket-retention-warning-link-navigates-to-the.md",
        "onetest-ai Test Case link",
    )
    def test_bucket_retention_link_navigates_to_bucket(self, page, _browser_cookies):
        """A retention-warning notification's in-message link carries the href built
        from that notification's own metadata and opens a new tab on the named
        bucket — listed AND opened, not merely a URL that mentions it."""
        notif_page = NotificationCenterPage(page)
        console_errors = collect_console_errors(page.context)
        artifact_api_by_project: dict[str, ArtifactAPI] = {}

        def bucket_is_live(project_id, bucket_name: str) -> bool:
            """Transit read of the product's own artifacts endpoint."""
            key = str(project_id)
            if key not in artifact_api_by_project:
                artifact_api_by_project[key] = ArtifactAPI(
                    browser_cookies=_browser_cookies, project_id=key
                )
            alive = artifact_api_by_project[key].bucket_exists(bucket_name)
            logger.info(
                "Bucket liveness probe project=%s bucket=%s -> %s", project_id, bucket_name, alive
            )
            return alive

        try:
            with allure.step("Step 1 — Navigate to Settings -> Notifications"):
                notif_page.navigate_and_get_rows()
                expect(notif_page.table_body).to_be_visible()
                page_info = notif_page.get_page_info()
                assert PAGE_INFO_PATTERN.match(page_info), (
                    f"Pagination range label did not render in the expected "
                    f"'{{start}} - {{end}} of {{total}}' shape, got {page_info!r}"
                )

            with allure.step(
                'Step 2 — Find a "Bucket [bucket] will start deleting files..." notification '
                "whose bucket still exists"
            ):
                response = notif_page.search_notifications(RETENTION_SEARCH_TERM)
                candidates = [
                    row
                    for row in response.json()["rows"]
                    if row.get("event_type") == RETENTION_EVENT_TYPE
                    and (row.get("meta") or {}).get("bucket_name")
                ]
                assert candidates, (
                    f"No {RETENTION_EVENT_TYPE} notification carrying a bucket name was "
                    f"returned for search {RETENTION_SEARCH_TERM!r}. The precondition "
                    "'the account's notification history contains a bucket retention "
                    "warning' is not met."
                )
                logger.info("%d retention-warning candidate row(s) rendered", len(candidates))

                target = next(
                    (
                        row
                        for row in candidates
                        if bucket_is_live(row["project_id"], row["meta"]["bucket_name"])
                    ),
                    None,
                )
                assert target is not None, (
                    "No bucket_expiration_warning notification points at a surviving bucket "
                    f"— all {len(candidates)} candidate(s) name buckets the retention policy "
                    "has already deleted. The precondition 'at least one retention warning "
                    "whose bucket still exists' is not met on this account (missing test "
                    "data, not a product failure)."
                )

                notification_id = target["id"]
                project_id = target["project_id"]
                bucket_name = target["meta"]["bucket_name"]
                logger.info(
                    "Target notification %s -> project %s bucket %s",
                    notification_id, project_id, bucket_name,
                )

                assert notif_page.get_row_link_count(notification_id) == 1, (
                    f"Expected notification row {notification_id} to render exactly one "
                    f"in-message link, found "
                    f"{notif_page.get_row_link_count(notification_id)} — the row-scoped "
                    "link locator would be ambiguous"
                )
                link = notif_page.get_row_link_attributes(notification_id)
                expected_href = _expected_retention_href(target)
                assert link["href"] == expected_href, (
                    f"The rendered link href is not the one the notification's own metadata "
                    f"defines.\n  expected: {expected_href}\n  actual:   {link['href']}"
                )
                assert link["text"] == bucket_name, (
                    f"Expected the link's visible text to be the bucket name "
                    f"{bucket_name!r}, got {link['text']!r}"
                )
                assert link["target"] == "_blank", (
                    f"Expected the in-message link to open in a new tab "
                    f"(target='_blank'), got {link['target']!r}"
                )
                assert link["rel"] == "noopener noreferrer", (
                    f"Expected rel='noopener noreferrer' on the new-tab link, "
                    f"got {link['rel']!r}"
                )

            artifacts_responses: list[tuple[int, str]] = []
            page.context.on(
                "response",
                lambda resp: (
                    artifacts_responses.append((resp.status, resp.url))
                    if ARTIFACTS_URL_MARKER in resp.url
                    else None
                ),
            )

            bucket_list_read_re = _bucket_list_read_matcher(project_id)

            # Gate the bucket-page assertions on the popup's OWN bucket-list read
            # having LANDED — a framework wait on the real response event, registered
            # BEFORE the click so it cannot be missed, rather than an element timeout
            # racing a 10-18 s fetch (see BUCKET_LIST_READ_URL_RE_TEMPLATE).
            with page.context.expect_event(
                "response",
                predicate=lambda resp: bucket_list_read_re.search(resp.url) is not None,
                timeout=BUCKET_LIST_READ_TIMEOUT,
            ) as bucket_list_read:
                with allure.step("Step 3 — Click the bucket link inside the notification text"):
                    pages_before = len(page.context.pages)
                    popup = notif_page.click_message_link_expecting_popup(notification_id)
                    assert len(page.context.pages) == pages_before + 1, (
                        f"Expected exactly one new tab after clicking the link, page count went "
                        f"{pages_before} -> {len(page.context.pages)}"
                    )

                with allure.step("Step 4 — The new tab lands on the referenced artifact bucket"):
                    popup.wait_for_url(
                        re.compile(r"/artifacts\?.*bucket="), timeout=POPUP_URL_TIMEOUT
                    )
                    parsed = urllib.parse.urlparse(popup.url)
                    # The href carries the notification's own ``/{project_id}`` prefix.
                    # The project switcher CONSUMES that segment only when a switch is
                    # actually required — when the notification's project is already the
                    # selected one it stays in the URL (measured live 2026-08-26:
                    # ``/399/artifacts?bucket=…`` for project 399, the personal project,
                    # against ``/chat/5883`` for ELITEA-2261's project 406). Both shapes
                    # name the SAME page of the SAME project, so both are accepted and
                    # nothing else is.
                    accepted_paths = (
                        f"{settings.app_prefix}/artifacts",
                        f"{settings.app_prefix}/{project_id}/artifacts",
                    )
                    assert parsed.path in accepted_paths, (
                        f"The new tab did not land on the artifacts page of the "
                        f"notification's own project: expected one of {accepted_paths}, "
                        f"got {parsed.path!r} (full URL {popup.url!r})"
                    )
                    landed_bucket = urllib.parse.parse_qs(parsed.query).get("bucket", [None])[0]
                    assert landed_bucket == bucket_name, (
                        f"The new tab's bucket query param is {landed_bucket!r}, not the "
                        f"notification's own bucket {bucket_name!r}"
                    )

                with allure.step(
                    'Step 5 — The bucket page opens without a "not found" error, on the '
                    "correct bucket"
                ):
                    try:
                        bucket_list_response = bucket_list_read.value
                    except PlaywrightTimeoutError as exc:
                        raise AssertionError(
                            f"The new tab never completed its bucket-list read for the "
                            f"notification's project {project_id} within "
                            f"{BUCKET_LIST_READ_TIMEOUT} ms, so the artifacts page could not "
                            f"resolve the ?bucket= deep link and was still rendering its empty "
                            f"state. Artifacts responses observed: "
                            f"{[url for _status, url in artifacts_responses] or 'none'}"
                        ) from exc
                    logger.info(
                        "Popup bucket-list read landed: %s %s",
                        bucket_list_response.status, bucket_list_response.url,
                    )

                    popup_artifacts = ArtifactsPage(popup)
                    expect(popup_artifacts.bucket_row(bucket_name)).to_be_visible(
                        timeout=POPUP_ELEMENT_TIMEOUT
                    )
                    empty_label = popup_artifacts.bucket_tree_empty_label(bucket_name)
                    try:
                        empty_label.wait_for(
                            state="visible", timeout=BUCKET_TREE_PROBE_TIMEOUT
                        )
                        bucket_opened = True
                        logger.info("Bucket %s opened and is empty", bucket_name)
                    except Exception:
                        bucket_opened = popup_artifacts.get_file_count() > 0
                        logger.info(
                            "Bucket %s empty-label absent; rendered file rows: %s",
                            bucket_name, popup_artifacts.get_file_count(),
                        )
                    assert bucket_opened, (
                        f"Bucket {bucket_name!r} is listed but was never OPENED — neither its "
                        '"No files in this bucket" empty label nor any file row rendered. '
                        "Landing on the right URL is not enough; a deleted bucket produces "
                        "exactly this shape."
                    )

                    failed_artifacts_reads = [
                        (status, url) for status, url in artifacts_responses if status >= 400
                    ]
                    assert not failed_artifacts_reads, (
                        f"The artifacts/bucket listing failed on the backend: "
                        f"{failed_artifacts_reads}"
                    )

                    # The notification's OWN project — not merely "an artifacts page".
                    # The landing path cannot carry this proof: the `/{project_id}`
                    # segment survives only when no switch is required, so the bare
                    # `/artifacts` form names no project. The reads the popup actually
                    # issued do, and a same-named bucket in another project would show
                    # up here as a foreign project id.
                    observed_projects = {
                        match.group(1)
                        for _status, url in artifacts_responses
                        if (match := ARTIFACTS_PROJECT_SCOPE_RE.search(url))
                    }
                    # Vite serves the feature's own JS modules from paths containing
                    # "/artifacts/" too — only the REST reads carry a project.
                    artifacts_rest_urls = [
                        url for _status, url in artifacts_responses if "/src/" not in url
                    ]
                    assert observed_projects == {str(project_id)}, (
                        f"The new tab did not read the artifacts of the notification's own "
                        f"project {project_id}: the artifacts REST calls it issued were scoped "
                        f"to project(s) {sorted(observed_projects) or 'none'} "
                        f"(calls observed: {artifacts_rest_urls or 'none'})"
                    )

            with allure.step("Axis 2 — No console errors attributable to this flow"):
                popup.close()
                flow_errors = _flow_console_errors(console_errors)
                assert not flow_errors, f"Unexpected console errors: {flow_errors}"
        finally:
            for api in artifact_api_by_project.values():
                api.close()

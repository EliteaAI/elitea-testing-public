"""UI + API Tests for ELITEA-2493 and ELITEA-2494 — Bucket Permission API Enforcement.

Security tests: verify that bucket permissions set via UI are enforced at the API level.

Test cases:
- ELITEA-2493: No Access permission — all API operations (GET/POST/DELETE) return 403
- ELITEA-2494: Read-only permission — GET returns 200, POST/DELETE return 403

Test flow:
1. [UI Setup] Login as Admin, set User B's permission via Manage Permissions modal
2. [UI Verify] Verify bucket visibility in sidebar for User B
3. [API Test] Execute GET/POST/DELETE requests using User B's session
4. [Cleanup] Restore User B to default permissions (Read & Write)

Requirements:
- Two users configured in .env.test: Admin (TEST_USER_EMAIL) and User B (TEST_USER_B_EMAIL)
- User B must exist in the Team project
- Test bucket is auto-created if missing (cleaned up only if created by test)

Markers:
    - ui: requires browser
    - security: security-related test
    - p0: critical priority

Usage:
    cd automation
    pytest tests/ui/artifacts/test_bucket_permissions_api.py -v
"""

import logging

import allure
import pytest

from pages.artifacts_page import ArtifactsPage
from config import settings

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.security, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Test configuration
# ---------------------------------------------------------------------------

# Bucket and file used for permission testing
BUCKET_NAME = "permissionstest"
TEST_FILENAME = "permission_test_file.txt"
TEST_FILE_CONTENT = b"This file is used for bucket permission API enforcement tests."

# Permission values as displayed in the UI
# Add Exceptions modal: only "Read-only" and "No access" (default is Read/write)
# Edit Exception modal: "Read/write (default)", "Read-only", "No access"
PERMISSION_NO_ACCESS = "No access"
PERMISSION_READ_ONLY = "Read-only"
PERMISSION_READ_WRITE = "Read/write (default)"  # Only available when editing existing exception

# Timeout constants (ms)
UI_TIMEOUT = 15_000
MODAL_TIMEOUT = 10_000
API_TIMEOUT = 30_000


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def test_bucket(artifact_api_team_project):
    """Ensure test bucket exists with a test file in Team project.

    Uses Team project (not private) because bucket permissions feature
    is only available in Team projects.

    Creates the bucket and file if they don't exist. Tracks whether we created
    them so cleanup only removes data we created (preserves pre-existing data).

    Yields:
        dict with keys:
            - name: bucket name
            - filename: test file name
            - created_bucket: True if we created the bucket
            - created_file: True if we created the file
    """
    api = artifact_api_team_project
    created_bucket = False
    created_file = False

    # Check if bucket exists
    if not api.bucket_exists(BUCKET_NAME):
        logger.info("Test bucket '%s' not found — creating", BUCKET_NAME)
        api.create_bucket(BUCKET_NAME)
        created_bucket = True
        logger.info("Created test bucket '%s'", BUCKET_NAME)

    # Check if test file exists
    existing_files = api.list_bucket_files(BUCKET_NAME)
    if TEST_FILENAME not in existing_files:
        logger.info("Test file '%s' not found — uploading", TEST_FILENAME)
        api.upload_file(BUCKET_NAME, TEST_FILENAME, TEST_FILE_CONTENT)
        created_file = True
        logger.info("Uploaded test file '%s'", TEST_FILENAME)

    yield {
        "name": BUCKET_NAME,
        "filename": TEST_FILENAME,
        "created_bucket": created_bucket,
        "created_file": created_file,
    }

    # Cleanup: only delete what we created
    if created_bucket:
        logger.info("Cleanup: deleting test bucket '%s' (created by test)", BUCKET_NAME)
        try:
            api.delete_bucket(BUCKET_NAME)
        except Exception as e:
            logger.warning("Failed to delete test bucket: %s", e)
    elif created_file:
        # Bucket existed but we added the file — just delete the file
        logger.info("Cleanup: deleting test file '%s' (created by test)", TEST_FILENAME)
        try:
            api.delete_file_raw(BUCKET_NAME, TEST_FILENAME)
        except Exception as e:
            logger.warning("Failed to delete test file: %s", e)


@pytest.fixture
def admin_page(browser, auth_state):
    """Create a browser page authenticated as Admin (User A)."""
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        base_url=settings.elitea_url,
        storage_state=auth_state,
    )
    ctx.set_default_timeout(UI_TIMEOUT)
    ctx.set_default_navigation_timeout(UI_TIMEOUT)
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


@pytest.fixture
def user_b_page(browser, auth_state_user_b):
    """Create a browser page authenticated as User B."""
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        base_url=settings.elitea_url,
        storage_state=auth_state_user_b,
    )
    ctx.set_default_timeout(UI_TIMEOUT)
    ctx.set_default_navigation_timeout(UI_TIMEOUT)
    page = ctx.new_page()
    yield page
    page.close()
    ctx.close()


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


@allure.epic("Artifacts")
@allure.feature("Bucket Permissions")
class TestBucketPermissionsAPI:
    """ELITEA-2493, ELITEA-2494 — API permission enforcement for bucket access.

    Security tests verifying that permissions configured via UI are enforced
    at the API level. Tests the "No access" and "Read-only" permission types.
    """

    @pytest.mark.p0
    @allure.title("No Access: All API operations return 403 Forbidden")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/artifacts/bucket-permissions/ELITEA-2493_api-no-access-permission-enforcement.md", "Test Case")
    @allure.issue("https://github.com/EliteaAI/elitea_issues/issues/5832", "Requirement")
    def test_no_access_permission_blocks_all_api_operations(
        self,
        test_bucket,
        admin_page,
        user_b_page,
        artifact_api_user_b_team_project,
    ):
        """Verify that 'No access' permission blocks GET, POST, and DELETE API calls.

        ELITEA-2493: User B with 'No access' exception cannot access the bucket
        via direct API calls — all operations must return 403 Forbidden.

        Steps:
        1. Admin sets User B to 'No access' for the test bucket
        2. Verify User B cannot see bucket in sidebar (UI enforcement)
        3. Verify GET request returns 403 Forbidden
        4. Verify POST (upload) request returns 403 Forbidden
        5. Verify DELETE request returns 403 Forbidden
        6. Cleanup: Restore User B to default permissions
        """
        bucket_name = test_bucket["name"]
        filename = test_bucket["filename"]
        user_b_email = settings.test_user_b_email

        # ------------------------------------------------------------------
        # Step 1: Admin sets User B to "No access" via UI
        # ------------------------------------------------------------------
        with allure.step("Step 1: Admin sets User B to 'No access' permission"):
            admin_artifacts = ArtifactsPage(admin_page)
            admin_artifacts.navigate_to_artifacts()
            admin_artifacts.open_manage_permissions(bucket_name, timeout=MODAL_TIMEOUT)
            admin_artifacts.add_permission_exception(
                user_name_or_email=user_b_email,
                permission=PERMISSION_NO_ACCESS,
                timeout=MODAL_TIMEOUT,
            )
            admin_artifacts.close_manage_permissions_modal()
            logger.info("Admin set User B to 'No access' for bucket '%s'", bucket_name)

        try:
            # ------------------------------------------------------------------
            # Step 2: Verify bucket is NOT visible for User B
            # ------------------------------------------------------------------
            with allure.step("Step 2: Verify bucket is NOT visible in User B's sidebar"):
                user_b_artifacts = ArtifactsPage(user_b_page)
                user_b_artifacts.navigate_to_artifacts()
                bucket_visible = user_b_artifacts.bucket_exists(bucket_name, timeout=5000)
                assert not bucket_visible, (
                    f"Bucket '{bucket_name}' should NOT be visible for User B with 'No access' "
                    f"permission, but it was found in the sidebar"
                )
                logger.info("Confirmed: bucket '%s' is NOT visible for User B", bucket_name)

            # ------------------------------------------------------------------
            # Step 3: Verify GET returns 403 Forbidden
            # ------------------------------------------------------------------
            with allure.step("Step 3: API GET request returns 403 Forbidden"):
                get_response = artifact_api_user_b_team_project.get_file_raw(bucket_name, filename)
                assert get_response.status_code == 403, (
                    f"GET request should return 403 Forbidden for 'No access' user, "
                    f"got {get_response.status_code}: {get_response.text}"
                )
                logger.info("GET request correctly returned 403 Forbidden")

            # ------------------------------------------------------------------
            # Step 4: Verify POST (upload) returns 403 Forbidden
            # ------------------------------------------------------------------
            with allure.step("Step 4: API POST (upload) request returns 403 Forbidden"):
                post_response = artifact_api_user_b_team_project.upload_file_raw(
                    bucket_name,
                    "test_upload.txt",
                    b"test content",
                )
                assert post_response.status_code == 403, (
                    f"POST (upload) request should return 403 Forbidden for 'No access' user, "
                    f"got {post_response.status_code}: {post_response.text}"
                )
                logger.info("POST request correctly returned 403 Forbidden")

            # ------------------------------------------------------------------
            # Step 5: Verify DELETE returns 403 Forbidden
            # ------------------------------------------------------------------
            with allure.step("Step 5: API DELETE request returns 403 Forbidden"):
                delete_response = artifact_api_user_b_team_project.delete_file_raw(bucket_name, filename)
                assert delete_response.status_code == 403, (
                    f"DELETE request should return 403 Forbidden for 'No access' user, "
                    f"got {delete_response.status_code}: {delete_response.text}"
                )
                logger.info("DELETE request correctly returned 403 Forbidden")

        finally:
            # ------------------------------------------------------------------
            # Cleanup: Remove User B's exception to restore default permissions
            # ------------------------------------------------------------------
            with allure.step("Cleanup: Remove User B's exception (restores default Read & Write)"):
                admin_artifacts.navigate_to_artifacts()
                admin_artifacts.open_manage_permissions(bucket_name, timeout=MODAL_TIMEOUT)
                admin_artifacts.remove_permission_exception(
                    user_name_or_email=user_b_email,
                    timeout=MODAL_TIMEOUT,
                )
                admin_artifacts.close_manage_permissions_modal()
                logger.info("Cleanup: Removed User B's exception (default permissions restored)")

    @pytest.mark.p0
    @allure.title("Read-only: GET allowed, POST/DELETE return 403 Forbidden")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/artifacts/bucket-permissions/ELITEA-2494_api-read-only-permission-enforcement.md", "Test Case")
    @allure.issue("https://github.com/EliteaAI/elitea_issues/issues/5832", "Requirement")
    def test_read_only_permission_allows_get_blocks_write_operations(
        self,
        test_bucket,
        admin_page,
        user_b_page,
        artifact_api_user_b_team_project,
    ):
        """Verify that 'Read-only' permission allows GET but blocks POST and DELETE.

        ELITEA-2494: User B with 'Read-only' exception can read files (GET returns 200)
        but cannot write or delete (POST/DELETE return 403 Forbidden).

        Steps:
        1. Admin sets User B to 'Read-only' for the test bucket
        2. Verify User B CAN see bucket in sidebar (read access works)
        3. Verify GET request returns 200 OK with file content
        4. Verify POST (upload) request returns 403 Forbidden
        5. Verify DELETE request returns 403 Forbidden
        6. Cleanup: Restore User B to default permissions
        """
        bucket_name = test_bucket["name"]
        filename = test_bucket["filename"]
        user_b_email = settings.test_user_b_email

        # ------------------------------------------------------------------
        # Step 1: Admin sets User B to "Read-only" via UI
        # ------------------------------------------------------------------
        with allure.step("Step 1: Admin sets User B to 'Read-only' permission"):
            admin_artifacts = ArtifactsPage(admin_page)
            admin_artifacts.navigate_to_artifacts()
            admin_artifacts.open_manage_permissions(bucket_name, timeout=MODAL_TIMEOUT)
            admin_artifacts.add_permission_exception(
                user_name_or_email=user_b_email,
                permission=PERMISSION_READ_ONLY,
                timeout=MODAL_TIMEOUT,
            )
            admin_artifacts.close_manage_permissions_modal()
            logger.info("Admin set User B to 'Read-only' for bucket '%s'", bucket_name)

        try:
            # ------------------------------------------------------------------
            # Step 2: Verify bucket IS visible for User B
            # ------------------------------------------------------------------
            with allure.step("Step 2: Verify bucket IS visible in User B's sidebar"):
                user_b_artifacts = ArtifactsPage(user_b_page)
                user_b_artifacts.navigate_to_artifacts()
                bucket_visible = user_b_artifacts.bucket_exists(bucket_name, timeout=10000)
                assert bucket_visible, (
                    f"Bucket '{bucket_name}' should be visible for User B with 'Read-only' "
                    f"permission, but it was NOT found in the sidebar"
                )
                logger.info("Confirmed: bucket '%s' IS visible for User B", bucket_name)

            # ------------------------------------------------------------------
            # Step 3: Verify GET returns 200 OK with file content
            # ------------------------------------------------------------------
            with allure.step("Step 3: API GET request returns 200 OK with file content"):
                get_response = artifact_api_user_b_team_project.get_file_raw(bucket_name, filename)
                assert get_response.status_code == 200, (
                    f"GET request should return 200 OK for 'Read-only' user, "
                    f"got {get_response.status_code}: {get_response.text}"
                )
                assert len(get_response.content) > 0, (
                    "GET response should contain file content, but response body is empty"
                )
                logger.info(
                    "GET request correctly returned 200 OK with %d bytes",
                    len(get_response.content),
                )

            # ------------------------------------------------------------------
            # Step 4: Verify POST (upload) returns 403 Forbidden
            # ------------------------------------------------------------------
            with allure.step("Step 4: API POST (upload) request returns 403 Forbidden"):
                post_response = artifact_api_user_b_team_project.upload_file_raw(
                    bucket_name,
                    "test_upload.txt",
                    b"test content",
                )
                assert post_response.status_code == 403, (
                    f"POST (upload) request should return 403 Forbidden for 'Read-only' user, "
                    f"got {post_response.status_code}: {post_response.text}"
                )
                logger.info("POST request correctly returned 403 Forbidden")

            # ------------------------------------------------------------------
            # Step 5: Verify DELETE returns 403 Forbidden
            # ------------------------------------------------------------------
            with allure.step("Step 5: API DELETE request returns 403 Forbidden"):
                delete_response = artifact_api_user_b_team_project.delete_file_raw(bucket_name, filename)
                assert delete_response.status_code == 403, (
                    f"DELETE request should return 403 Forbidden for 'Read-only' user, "
                    f"got {delete_response.status_code}: {delete_response.text}"
                )
                logger.info("DELETE request correctly returned 403 Forbidden")

        finally:
            # ------------------------------------------------------------------
            # Cleanup: Remove User B's exception to restore default permissions
            # ------------------------------------------------------------------
            with allure.step("Cleanup: Remove User B's exception (restores default Read & Write)"):
                admin_artifacts.navigate_to_artifacts()
                admin_artifacts.open_manage_permissions(bucket_name, timeout=MODAL_TIMEOUT)
                admin_artifacts.remove_permission_exception(
                    user_name_or_email=user_b_email,
                    timeout=MODAL_TIMEOUT,
                )
                admin_artifacts.close_manage_permissions_modal()
                logger.info("Cleanup: Removed User B's exception (default permissions restored)")

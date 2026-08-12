"""UI test — Entry Point Node: Webhook Trigger Settings Modal.

TMS: ELITEA-2006
(test-specs/pipelines/l3_entry-point-webhook-trigger-settings-modal_ELITEA-2006.md)

Selects "Webhook" from the entry-point node's Trigger dropdown, verifies the
Webhook settings modal renders every required field/control once its
two-timing-wave population settles (Webhook Type radios defaulting to GitHub,
URL+copy, Secret masked field with a functional eye/copy/refresh, Payload
Format description, a type-specific Example Request block+copy, Cancel/
Apply), verifies switching Webhook Type live-updates the URL and description
with no network wait needed, applies the change, and confirms the webhook
trigger survives a full page reload.
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from tests.ui.pipelines.helpers import _navigate_to_canvas

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
MODAL_TIMEOUT = 10_000


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/pipelines/"
    "ELITEA-2006_entry-point-webhook-trigger-settings-modal.md",
    "onetest-ai Test Case link",
)
def test_webhook_trigger_settings_modal(page, pipeline_with_llm_id):
    """Webhook settings modal: full field inventory, type switching, and persistence."""
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

    with allure.step("Step 1 — Navigate to the fresh pipeline; verify single entry-point node"):
        pipeline_page = _navigate_to_canvas(page, pipeline_with_llm_id)
        # Capture every /pipeline_trigger/ request+response from here on — the
        # ONE endpoint this whole flow depends on — so the final full-flow
        # check below covers the entire test, including Step 7's reload.
        trigger_requests = pipeline_page.capture_requests_matching("/pipeline_trigger/")
        llm_node_id = pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_entrypoint_node_id() == llm_node_id, (
            "Pipeline should be ready with the LLM node as the single entry-point node"
        )
        assert pipeline_page.trigger_select.is_visible(), (
            "Trigger select should render on the entry-point node's card"
        )

    with allure.step('Step 2 — Select "Webhook" from the Trigger dropdown'):
        trigger_response = pipeline_page.select_trigger_type("webhook", timeout=UI_ELEMENT_TIMEOUT)
        assert trigger_response is not None, "Selecting Webhook should persist type=webhook server-side immediately"
        assert trigger_response.get("type") == "webhook", (
            f"Trigger-update response should confirm type=webhook, got {trigger_response!r}"
        )

    with allure.step(
        "Step 3 — Verify the Webhook settings modal opens with all required elements "
        "(waiting for the delayed field wave to settle)"
    ):
        pipeline_page.wait_for_webhook_settings_loaded(timeout=MODAL_TIMEOUT)

        assert pipeline_page.get_selected_webhook_type() == "github", (
            "GitHub should be the default-selected Webhook Type"
        )
        assert pipeline_page.webhook_type_description.is_visible(), "Webhook Type description should be visible"
        assert pipeline_page.webhook_url_input.is_visible(), "Webhook URL field should be visible"
        assert pipeline_page.webhook_url_copy_button.is_visible(), "Webhook URL copy button should be visible"
        assert pipeline_page.webhook_secret_input.is_visible(), "Secret Value field should be visible"
        assert pipeline_page.webhook_secret_toggle_button.is_visible(), (
            "Secret Value eye (show/hide) button should be visible"
        )
        assert pipeline_page.webhook_secret_copy_button.is_visible(), "Secret Value copy button should be visible"
        assert pipeline_page.webhook_secret_regenerate_button.is_visible(), (
            "Secret Value regenerate button should be visible"
        )
        assert pipeline_page.webhook_secret_helper_text.is_visible(), "Secret Value helper text should be visible"
        assert pipeline_page.webhook_payload_format_description.is_visible(), (
            "Payload Format description should be visible"
        )
        assert pipeline_page.webhook_example_request_block.is_visible(), (
            "Example Request code block should be visible"
        )
        assert pipeline_page.webhook_example_request_copy_button.is_visible(), (
            "Example Request copy button should be visible"
        )
        assert pipeline_page.webhook_modal_cancel_button.is_visible(), "Cancel button should be visible"
        assert pipeline_page.webhook_modal_apply_button.is_visible(), "Apply button should be visible"

        github_description = (pipeline_page.webhook_type_description.text_content() or "").strip()
        assert "hmac" in github_description.lower() or "signature" in github_description.lower(), (
            f"Description should reflect the GitHub-specific header, got {github_description!r}"
        )
        github_url = pipeline_page.get_webhook_url()
        assert github_url.endswith("/github"), (
            f"Webhook URL should target the github path by default, got {github_url!r}"
        )

    with allure.step("Step 3b — Verify the Secret Value eye toggle actually reveals the real secret"):
        masked_secret = pipeline_page.get_webhook_secret()
        assert masked_secret and set(masked_secret) == {"•"}, (
            f"Secret should be masked (all bullet chars) by default, got {masked_secret!r}"
        )

        pipeline_page.reveal_webhook_secret(timeout=UI_ELEMENT_TIMEOUT)
        revealed_secret = pipeline_page.get_webhook_secret()
        assert revealed_secret and "•" not in revealed_secret and revealed_secret != masked_secret, (
            f"Secret should reveal a real, unmasked value after clicking the eye toggle, got {revealed_secret!r}"
        )

    with allure.step("Step 4 — Switch Webhook Type to GitLab; verify URL and description update"):
        pipeline_page.select_webhook_type("gitlab", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_selected_webhook_type() == "gitlab"

        gitlab_url = pipeline_page.get_webhook_url()
        assert gitlab_url.endswith("/gitlab") and gitlab_url != github_url, (
            f"Webhook URL should update to the gitlab path, got {gitlab_url!r}"
        )
        gitlab_description = (pipeline_page.webhook_type_description.text_content() or "").strip()
        assert "gitlab" in gitlab_description.lower(), (
            f"Description should reflect the GitLab-specific header, got {gitlab_description!r}"
        )

    with allure.step("Step 5 — Switch Webhook Type to Custom; verify URL updates"):
        pipeline_page.select_webhook_type("custom", timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.get_selected_webhook_type() == "custom"

        custom_url = pipeline_page.get_webhook_url()
        assert custom_url.endswith("/custom") and custom_url != gitlab_url, (
            f"Webhook URL should update to the custom path, got {custom_url!r}"
        )
        custom_description = (pipeline_page.webhook_type_description.text_content() or "").strip()
        assert "webhook" in custom_description.lower(), (
            f"Description should reflect the Custom X-Webhook-Token header, got {custom_description!r}"
        )

    with allure.step('Step 6 — Click "Apply"; verify modal closes and Trigger shows "Webhook"'):
        apply_response = pipeline_page.apply_webhook_settings(timeout=MODAL_TIMEOUT)
        assert apply_response is not None and apply_response.get("webhook_type") == "custom", (
            f"Apply should persist webhook_type=custom server-side, got {apply_response!r}"
        )
        assert not pipeline_page.webhook_modal.is_visible(), "Modal should be closed after Apply"

        # Apply fires its own fresh updateTrigger mutation with the
        # currently-selected webhook type — reliable, but still poll rather
        # than read same-tick (auto-retrying expect, AFS § Quirks).
        expect(pipeline_page.trigger_select).to_have_text("Webhook", timeout=MODAL_TIMEOUT)

    with allure.step("Step 7 — Save is a no-op (disabled); reload; verify the Webhook trigger persists"):
        # Declared improvisation (role-overrides.md § Declared-improvisation
        # protocol, same as ELITEA-2005's Step 5): trigger/webhook config is a
        # separate server-side entity persisted immediately by its own PUT
        # calls in Steps 2/6, so the pipeline's own Formik-tracked form is
        # never dirtied and Save stays correctly DISABLED — confirmed live.
        assert not pipeline_page.is_save_enabled(), (
            "Save should be disabled — trigger/webhook config persists via its own "
            "endpoint, independent of the pipeline's own Formik-tracked form state"
        )

        canonical_url = page.url  # carries ?viewMode=owner
        page.goto(canonical_url)
        pipeline_page.wait_for_detail_page_load()
        pipeline_page.wait_for_canvas()
        pipeline_page.wait_for_node_on_canvas("llm", timeout=UI_ELEMENT_TIMEOUT)

        # currentTriggerType falls back to its "chat_message" default while
        # the post-reload GET .../trigger refetch is still in flight — poll
        # instead of reading same-tick (AFS § Quirks, same as ELITEA-2005).
        expect(pipeline_page.trigger_select).to_have_text("Webhook", timeout=UI_ELEMENT_TIMEOUT)

    # Full-flow checks (AFS Pass/Fail — "all steps complete without errors"):
    # both listeners have been live since Step 1, so these cover the entire
    # flow including Step 7's reload.
    failed_trigger_requests = [r for r in trigger_requests if r["status"] is not None and r["status"] >= 400]
    assert not failed_trigger_requests, (
        "No /pipeline_trigger/ request should fail across the whole webhook trigger flow, got: "
        f"{failed_trigger_requests}"
    )
    trigger_requests.stop()

    assert not console_errors, (
        "Configuring/reloading/persisting the webhook trigger should not introduce console errors "
        f"across the whole flow, got: {[m.text for m in console_errors]}"
    )

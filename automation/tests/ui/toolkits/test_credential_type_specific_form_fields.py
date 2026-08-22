"""Test for Credential — Type-Specific Form Fields.

Verifies that each supported credential type's create form renders exactly the
type-specific fields, auth-method radio options and Test-connection button
state the case specifies — asserted BI-DIRECTIONALLY: the expected handles are
asserted visible, and every handle in the closed union that the type must NOT
render is asserted ``to_have_count(0)``. The case's Fail criterion names
"incorrect, missing, or extra fields", and a presence-only check cannot see an
extra field.

Test case: ELITEA-1967
AFS: test-specs/toolkits-credentials/l2_credential-type-specific-form-fields_ELITEA-1967.md

Read-only (Hard Rule 10): nothing is created, filled, saved or deleted. The
observable is what the create form *renders* for a given type, which is fully
determined by the backend schema
(``GET /configurations/available/?section=credentials``) and reachable by
navigating straight to ``/credentials/create-credential/{type}``.

Fidelity: no substitution of any kind. Every asserted value — field presence,
radio labels, the ``Auto`` hosting default, the pre-filled
``https://api.github.com``, Postman's disabled Test-connection button — is
rendered by the product from a live backend schema response.
"""

import logging

import allure
import pytest
from pages.credential_create_page import CredentialCreatePage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.credentials,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

# Per-type expectation table — one entry per case step, in case order.
#
#   fields          plain (non-secret) schema property keys rendered by default
#   secret_fields   schema property keys rendered as a SecretField (which is
#                   what the case's "(Secret/Password toggle)" annotation means)
#   selects         enum dropdowns: {property key: expected displayed value}
#   prefilled       product-supplied default values: {property key: value}
#   auth            auth-method radio options, in rendered order:
#                   [(testid slug, visible label), ...] — empty means the type
#                   declares no auth section and renders NO radio at all
#   auth_default    the slug pre-selected on arrival
#   test_connection_enabled
#                   whether the Test connection button is enabled
TYPE_EXPECTATIONS: dict[str, dict] = {
    "github": {
        "step": 1,
        "title": "GitHub",
        "fields": ["base_url"],
        "secret_fields": [],
        "selects": {},
        "prefilled": {"base_url": "https://api.github.com"},
        "auth": [
            ("none", "Anonymous"),
            ("token", "Token"),
            ("password", "Password"),
            ("app-private-key", "App private key"),
        ],
        "auth_default": "none",
        "test_connection_enabled": True,
    },
    "sharepoint": {
        "step": 2,
        "title": "SharePoint",
        "fields": ["client_id", "site_url"],
        "secret_fields": ["client_secret"],
        "selects": {},
        "prefilled": {},
        "auth": [("app-only", "App-only"), ("delegated", "Delegated")],
        "auth_default": "app-only",
        "test_connection_enabled": True,
    },
    "ado": {
        "step": 3,
        "title": "ADO",
        "fields": ["organization_url"],
        "secret_fields": ["token"],
        "selects": {},
        "prefilled": {},
        "auth": [],
        "auth_default": None,
        "test_connection_enabled": True,
    },
    "gitlab": {
        "step": 4,
        "title": "GitLab",
        "fields": ["url"],
        "secret_fields": ["private_token"],
        "selects": {},
        "prefilled": {},
        "auth": [("gitlab-private-token", "GitLab private token")],
        "auth_default": "gitlab-private-token",
        "test_connection_enabled": True,
    },
    "confluence": {
        "step": 5,
        "title": "Confluence",
        "fields": ["base_url", "username"],
        "secret_fields": ["api_key"],
        "selects": {"hosting": "Auto"},
        "prefilled": {},
        "auth": [("basic", "Basic"), ("bearer", "Bearer")],
        "auth_default": "basic",
        "test_connection_enabled": True,
    },
    "jira": {
        "step": 6,
        "title": "Jira",
        "fields": ["base_url", "username"],
        "secret_fields": ["api_key"],
        "selects": {"hosting": "Auto"},
        "prefilled": {},
        "auth": [("basic", "Basic"), ("bearer", "Bearer")],
        "auth_default": "basic",
        "test_connection_enabled": True,
    },
    "figma": {
        "step": 7,
        "title": "Figma",
        "fields": [],
        "secret_fields": ["token"],
        "selects": {},
        "prefilled": {},
        "auth": [("token", "Token")],
        "auth_default": "token",
        "test_connection_enabled": True,
    },
    "postman": {
        "step": 8,
        "title": "Postman",
        "fields": ["base_url", "workspace_id"],
        "secret_fields": ["api_key"],
        "selects": {},
        "prefilled": {},
        "auth": [("api-key", "API Key")],
        "auth_default": "api-key",
        # The one type in this set whose schema carries
        # has_test_connection: false -> CredentialForm.jsx renders the button
        # disabled. Asserted, not skipped.
        "test_connection_enabled": False,
    },
    "langfuse": {
        "step": 9,
        "title": "Langfuse",
        "fields": ["base_url", "public_key"],
        "secret_fields": ["secret_key"],
        "selects": {},
        "prefilled": {},
        "auth": [],
        "auth_default": None,
        "test_connection_enabled": True,
    },
    "report_portal": {
        "step": 10,
        "title": "Report Portal",
        "fields": ["project", "endpoint"],
        "secret_fields": ["api_key"],
        "selects": {},
        "prefilled": {},
        "auth": [],
        "auth_default": None,
        "test_connection_enabled": True,
    },
}

# Fields that belong to an auth subsection which is NOT selected by default, so
# no type in this set renders them on arrival. Included in the absence union so
# a regression that renders a hidden subsection's fields eagerly is caught.
UNSELECTED_SUBSECTION_FIELDS = frozenset(
    {
        "access_token",  # github / Token
        "app_id",  # github / App private key
        "app_private_key",  # github / App private key
        "password",  # github / Password
        "oauth_discovery_endpoint",  # sharepoint / Delegated
        "scopes",  # sharepoint / Delegated
        "auto_refresh_token",  # sharepoint / Delegated
    }
)

# Closed unions the absence half of every step is computed from — derived from
# the table above so the two halves can never drift apart.
FIELD_UNION = frozenset(
    field
    for spec in TYPE_EXPECTATIONS.values()
    for field in list(spec["fields"]) + list(spec["secret_fields"])
) | UNSELECTED_SUBSECTION_FIELDS
SELECT_UNION = frozenset(key for spec in TYPE_EXPECTATIONS.values() for key in spec["selects"])
AUTH_SLUG_UNION = frozenset(slug for spec in TYPE_EXPECTATIONS.values() for slug, _ in spec["auth"])


def _is_known_554_warning(msg) -> bool:
    """Filter the pre-existing, already-filed elitea-testing-public#554 — an
    RTK-Query timing race in ``EliteaUI/src/api/toolkits.js``'s ``toolkitTypes``
    endpoint that fires before ``useSelectedProjectId()`` resolves, building the
    URL with an empty projectId segment (``.../toolkits/prompt_lib/``) which
    404s. Matched by ``msg.location.url``, not by a blanket 404 match, so a
    genuinely new failing request isn't masked.

    Deliberately NOT reused here: this suite's ``#518``
    ``<CredentialsList>``-crash filter. That component is never rendered by this
    case (it never visits ``/credentials/all``) and #518 is CLOSED as NOT
    REPRODUCIBLE — see ``tests/unit/test_credentials_console_filters_scope.py``.
    """
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


class TestCredentialTypeSpecificFormFields:
    """ELITEA-1967 — each credential type renders its own field set, auth
    options and Test-connection state."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1967_credential-type-specific-form-fields.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_type_specific_form_fields(self, page):
        """Assert the rendered form of all ten credential types the case names."""
        create_page = CredentialCreatePage(page)

        console_messages = []

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_554_warning(msg):
                console_messages.append(msg)

        page.on("console", _on_console)

        for credential_type, spec in TYPE_EXPECTATIONS.items():
            with allure.step(
                f"Step {spec['step']} — Create new credential type "
                f"\"{spec['title']}\": verify its type-specific fields, auth "
                f"options and Test connection state"
            ):
                create_page.open_type_form(credential_type)

                # --- Invariant fields present on every type -----------------
                expect(create_page.display_name_input).to_be_visible()
                expect(create_page.id_input).to_be_visible()
                # The case annotates "(disabled)" only on GitHub, but the ID
                # field live-mirrors Display Name through the same shared
                # renderer on every type — asserting the live contract, per the
                # reverse-masking guard.
                expect(create_page.id_input).to_be_disabled()

                # --- Type-specific fields: present --------------------------
                expected_fields = set(spec["fields"]) | set(spec["secret_fields"])
                for field_key in sorted(expected_fields):
                    expect(create_page.field(field_key)).to_be_visible()

                for field_key, expected_value in spec["prefilled"].items():
                    expect(create_page.field(field_key)).to_have_value(expected_value)

                # --- Secret fields render the Secret/Password toggle ---------
                for field_key in spec["secret_fields"]:
                    expect(create_page.secret_toggle(field_key, "secret")).to_be_visible()
                    expect(create_page.secret_toggle(field_key, "password")).to_be_visible()

                # --- Type-specific fields: no extras ------------------------
                for field_key in sorted(FIELD_UNION - expected_fields):
                    expect(create_page.field(field_key)).to_have_count(0)

                # --- Enum dropdowns (Hosting) -------------------------------
                for field_key, expected_text in spec["selects"].items():
                    expect(create_page.field_select(field_key)).to_be_visible()
                    expect(create_page.field_select(field_key)).to_have_text(expected_text)
                for field_key in sorted(SELECT_UNION - set(spec["selects"])):
                    expect(create_page.field_select(field_key)).to_have_count(0)

                # --- Auth-method radio options ------------------------------
                expected_slugs = {slug for slug, _ in spec["auth"]}
                for slug, label in spec["auth"]:
                    expect(create_page.auth_radio(slug)).to_be_visible()
                    expect(create_page.auth_radio(slug)).to_have_text(label)
                if spec["auth_default"] is not None:
                    expect(create_page.auth_radio(spec["auth_default"])).to_be_checked()
                for slug in sorted(AUTH_SLUG_UNION - expected_slugs):
                    expect(create_page.auth_radio(slug)).to_have_count(0)

                # --- Test connection button ---------------------------------
                expect(create_page.test_connection_button).to_be_visible()
                if spec["test_connection_enabled"]:
                    expect(create_page.test_connection_button).to_be_enabled()
                else:
                    expect(create_page.test_connection_button).to_be_disabled()

        with allure.step(
            "Pass criterion — all steps completed without errors (console side-channel)"
        ):
            page.remove_listener("console", _on_console)
            assert not console_messages, (
                "Unexpected console errors/warnings: "
                f"{[(m.type, m.text) for m in console_messages]}"
            )

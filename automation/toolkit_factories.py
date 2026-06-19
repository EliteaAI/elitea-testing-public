"""Credential and toolkit payload factory functions.

Each toolkit type has a unique API payload shape for both credential
creation and toolkit settings.  Factory functions encapsulate these
differences so the parameterized tests can create any toolkit type
using a simple function-name lookup.

Usage::

    from toolkit_factories import CREDENTIAL_FACTORIES, TOOLKIT_SETTINGS_FACTORIES

    payload = CREDENTIAL_FACTORIES["create_github_credential_payload"](
        display_name="My Cred", token="ghp_..."
    )
    settings = TOOLKIT_SETTINGS_FACTORIES["github_toolkit_settings"](
        credential_elitea_title="github_123"
    )
"""

import time

from config import settings


def _ts() -> str:
    return str(int(time.time()))


# ── Credential payload factories ──────────────────────────────────────


def create_github_credential_payload(display_name: str, token: str) -> dict:
    ts = str(int(time.time() * 1000))
    return {
        "type": "github",
        "elitea_title": f"github_{ts}",
        "label": display_name,
        "data": {
            "base_url": "https://api.github.com",
            "access_token": token,
        },
        "shared": False,
    }


def create_jira_credential_payload(display_name: str, token: str) -> dict:
    ts = str(int(time.time() * 1000))
    base_url = settings.jira_base_url
    username = settings.jira_username
    return {
        "type": "jira",
        "elitea_title": f"jira_{ts}",
        "label": display_name,
        "data": {
            "base_url": base_url,
            "api_key": token,
            "username": username,
        },
        "shared": False,
    }


def create_gitlab_credential_payload(display_name: str, token: str) -> dict:
    ts = str(int(time.time() * 1000))
    return {
        "type": "gitlab",
        "elitea_title": f"gitlab_{ts}",
        "label": display_name,
        "data": {
            "url": settings.gitlab_url,
            "private_token": token,
        },
        "shared": False,
    }


def create_bitbucket_credential_payload(display_name: str, token: str) -> dict:
    ts = str(int(time.time() * 1000))
    return {
        "type": "bitbucket",
        "elitea_title": f"bitbucket_{ts}",
        "label": display_name,
        "data": {
            "url": settings.bitbucket_url,
            "password": token,
            "username": settings.bitbucket_username,
        },
        "shared": False,
    }


def create_confluence_credential_payload(display_name: str, token: str) -> dict:
    ts = str(int(time.time() * 1000))
    base_url = settings.confluence_base_url
    username = settings.confluence_username
    return {
        "type": "confluence",
        "elitea_title": f"confluence_{ts}",
        "label": display_name,
        "data": {
            "base_url": base_url,
            "api_key": token,
            "username": username,
        },
        "shared": False,
    }


# ── Toolkit settings factories ────────────────────────────────────────


def github_toolkit_settings(credential_elitea_title: str) -> dict:
    return {
        "type": "github",
        "settings": {
            "github_configuration": {
                "elitea_title": credential_elitea_title,
                "private": True,
            },
            "repository": settings.github_repo,
            "active_branch": "main",
            "base_branch": "main",
        },
    }


def jira_toolkit_settings(credential_elitea_title: str) -> dict:
    return {
        "type": "jira",
        "settings": {
            "jira_configuration": {
                "elitea_title": credential_elitea_title,
                "private": True,
            },
            "cloud": True,
            "limit": 50,
            "api_version": "3",
            "verify_ssl": True,
        },
    }


def gitlab_toolkit_settings(credential_elitea_title: str) -> dict:
    return {
        "type": "gitlab",
        "settings": {
            "gitlab_configuration": {
                "elitea_title": credential_elitea_title,
                "private": True,
            },
            "repository": settings.gitlab_repository,
            "branch": settings.gitlab_base_branch,
        },
    }


def bitbucket_toolkit_settings(credential_elitea_title: str) -> dict:
    project = settings.bitbucket_project
    repository = settings.bitbucket_repository
    return {
        "type": "bitbucket",
        "settings": {
            "bitbucket_configuration": {
                "elitea_title": credential_elitea_title,
                "private": True,
            },
            "project": project,
            "repository": repository,
            "branch": "master",  # Bitbucket default
        },
    }


def confluence_toolkit_settings(credential_elitea_title: str) -> dict:
    return {
        "type": "confluence",
        "settings": {
            "confluence_configuration": {
                "elitea_title": credential_elitea_title,
                "private": True,
            },
            "space": settings.confluence_space,
            "cloud": True,
            "limit": 50,
        },
    }


# ── Factory registries ────────────────────────────────────────────────

CREDENTIAL_FACTORIES = {
    "create_github_credential_payload": create_github_credential_payload,
    "create_jira_credential_payload": create_jira_credential_payload,
    "create_gitlab_credential_payload": create_gitlab_credential_payload,
    "create_bitbucket_credential_payload": create_bitbucket_credential_payload,
    "create_confluence_credential_payload": create_confluence_credential_payload,
}

TOOLKIT_SETTINGS_FACTORIES = {
    "github_toolkit_settings": github_toolkit_settings,
    "jira_toolkit_settings": jira_toolkit_settings,
    "gitlab_toolkit_settings": gitlab_toolkit_settings,
    "bitbucket_toolkit_settings": bitbucket_toolkit_settings,
    "confluence_toolkit_settings": confluence_toolkit_settings,
}

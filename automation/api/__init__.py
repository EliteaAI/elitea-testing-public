"""Elitea API client package.

Re-exports the base client for convenient imports::

    from api import APIClient
"""

from api.client import (
    AgentAPI,
    APIClient,
    ArtifactAPI,
    ConversationAPI,
    CredentialAPI,
    NotificationAPI,
    PipelineAPI,
    SkillAPI,
    ToolkitAPI,
)

__all__ = [
    "APIClient",
    "AgentAPI",
    "ArtifactAPI",
    "ConversationAPI",
    "CredentialAPI",
    "NotificationAPI",
    "PipelineAPI",
    "SkillAPI",
    "ToolkitAPI",
]

"""Elitea API client package.

Re-exports the base client for convenient imports::

    from api import APIClient
"""

from api.client import (
    APIClient,
    AgentAPI,
    ArtifactAPI,
    ConversationAPI,
    CredentialAPI,
    PipelineAPI,
    ProjectAPI,
    SkillAPI,
    ToolkitAPI,
)

__all__ = [
    "APIClient",
    "AgentAPI",
    "ArtifactAPI",
    "ConversationAPI",
    "CredentialAPI",
    "PipelineAPI",
    "ProjectAPI",
    "SkillAPI",
    "ToolkitAPI",
]

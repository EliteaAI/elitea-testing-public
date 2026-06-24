"""Page object package for Elitea UI tests.

Re-exports page objects for convenient imports::

    from pages import BasePage
"""

from pages.base_page import BasePage
from pages.agent_page import AgentPage
from pages.artifacts_page import ArtifactsPage
from pages.pipelines_list_page import PipelinesListPage
from pages.pipeline_form_page import PipelineFormPage
from pages.pipeline_detail_page import PipelineDetailPage
from pages.support_assistant_page import SupportAssistantPage

__all__ = [
    "AgentPage",
    "ArtifactsPage",
    "BasePage",
    "PipelinesListPage",
    "PipelineFormPage",
    "PipelineDetailPage",
    "SupportAssistantPage",
]

"""Internal Tools enumeration and configuration.

Defines all available internal tools (built-in capabilities) that can be
toggled on/off in the Chat interface and Agent configuration.
"""

from enum import Enum
from typing import List


class ChatInternalTool(str, Enum):
    """Internal tools available in the Chat interface.

    These tools appear in the Modules panel accessed via the plus menu
    → "Modules" in the chat input area.

    Each value represents the exact display text in the UI, and the members are
    declared in the order the panel renders them.

    Titles are sourced from EliteaUI
    ``src/[fsd]/shared/lib/constants/internalTools.constants.js``; several were
    renamed by EliteaAI/EliteaUI@79fd2a55 ("[EL-6540] Standardize Module Order
    and Descriptions", merged 2026-09-08).
    """

    # Image generation from text prompts.
    # Gated per-project on the ImageGenServiceProvider_ImageGen toolkit — the
    # only member here that can be absent while the other nine render.
    IMAGE_CREATION = "Image Creation"

    # Data analysis and visualization
    DATA_ANALYSIS = "Data Analysis"

    # Agent & Pipeline Builder (replaces Elitea MCP Tools)
    AGENT_PIPELINE_BUILDER = "Agent & Pipeline Builder"

    # Builder for reusable skills
    SKILL_BUILDER = "Skill Builder"

    # Builder for the project-context knowledge base
    PROJECT_CONTEXT_BUILDER = "Project Context Builder"

    # Interactive user input request
    ASK_USER = "Ask User"

    # Task planning and breakdown
    PLANNER = "Planner"

    # Python code execution environment
    PYTHON_SANDBOX = "Python Sandbox"

    # Multi-agent collaboration mode
    SWARM_MODE = "Swarm Mode"

    # Automatic tool selection based on context
    SMART_TOOLS = "Smart Tools Selection"


# Canonical list of all Chat internal tools (for validation)
CHAT_INTERNAL_TOOLS: List[str] = [tool.value for tool in ChatInternalTool]


class AgentInternalTool(str, Enum):
    """Internal tools available in Agent configuration.

    These tools appear in the "INTERNAL TOOLS" section of the Agent detail page.
    Almost identical to Chat tools, but includes "Attachments".

    Each value represents the exact display text in the UI.
    """

    # File attachments (Agent-only, not in Chat)
    ATTACHMENTS = "Attachments"

    # Image generation from text prompts
    IMAGE_CREATION = "Image creation"

    # Data analysis and visualization
    DATA_ANALYSIS = "Data Analysis"

    # Task planning and breakdown
    PLANNER = "Planner"

    # Python code execution environment
    PYTHON_SANDBOX = "Python sandbox"

    # Interactive user input request
    ASK_USER = "Ask User"

    # Multi-agent collaboration mode
    SWARM_MODE = "Swarm Mode"

    # Automatic tool selection based on context
    SMART_TOOLS = "Smart Tools Selection"


# Canonical list of all Agent internal tools (for validation)
AGENT_INTERNAL_TOOLS: List[str] = [tool.value for tool in AgentInternalTool]


# Backwards compatibility alias
InternalTool = AgentInternalTool


# Map of tool enum to test ID (for future testid implementation)
INTERNAL_TOOL_TESTIDS = {
    AgentInternalTool.ATTACHMENTS: "internal-tool-attachments",
    AgentInternalTool.IMAGE_CREATION: "internal-tool-image-creation",
    AgentInternalTool.DATA_ANALYSIS: "internal-tool-data-analysis",
    AgentInternalTool.PLANNER: "internal-tool-planner",
    AgentInternalTool.PYTHON_SANDBOX: "internal-tool-python-sandbox",
    AgentInternalTool.ASK_USER: "internal-tool-ask-user",
    AgentInternalTool.SWARM_MODE: "internal-tool-swarm-mode",
    AgentInternalTool.SMART_TOOLS: "internal-tool-smart-selection",
}


def get_tool_testid(tool: AgentInternalTool) -> str:
    """Get the test ID for an internal tool.

    Args:
        tool: The internal tool enum value.

    Returns:
        The data-testid attribute value for the tool switch.
    """
    return INTERNAL_TOOL_TESTIDS.get(tool, f"internal-tool-{tool.value.lower().replace(' ', '-')}")

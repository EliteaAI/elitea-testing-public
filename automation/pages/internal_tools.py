"""Internal Tools enumeration and configuration.

Defines all available internal tools (built-in capabilities) that can be
toggled on/off in the Chat interface and Agent configuration.
"""

from enum import Enum
from typing import List


class ChatInternalTool(str, Enum):
    """Internal tools available in the Chat interface.

    These tools appear in the internal tools panel when clicking the
    "enable internal tools" button in the chat input area.

    Each value represents the exact display text in the UI.
    """

    # Image generation from text prompts
    IMAGE_CREATION = "Image creation"

    # Data analysis and visualization
    DATA_ANALYSIS = "Data Analysis"

    # Task planning and breakdown
    PLANNER = "Planner"

    # Python code execution environment
    PYTHON_SANDBOX = "Python sandbox"

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

"""Internal Tools enumeration and configuration.

Defines all available internal tools (built-in capabilities) that can be
toggled on/off in the Chat interface and Agent configuration.
"""

from enum import Enum
from typing import List


class ChatInternalTool(str, Enum):
    """Internal tools available in the Chat interface.

    These tools appear in the internal tools panel accessed via the plus menu
    → "Internal Tools" in the chat input area.

    Each value represents the exact display text in the UI.
    """

    # Image generation from text prompts
    IMAGE_CREATION = "Image creation"

    # Data analysis and visualization
    DATA_ANALYSIS = "Data Analysis"

    # Elitea MCP Tools integration
    ELITEA_MCP_TOOLS = "Elitea MCP Tools"

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


# Map of tool enum to test ID — matches data-testid added in ELITEA-5634.
# Testids are derived from the INTERNAL_TOOLS_LIST `name` field in the frontend
# (src/[fsd]/shared/lib/constants/internalTools.constants.js) with underscores
# replaced by hyphens: `internal-tool-{name.replace("_", "-")}`.
INTERNAL_TOOL_TESTIDS = {
    AgentInternalTool.ATTACHMENTS: "internal-tool-attachments",
    AgentInternalTool.IMAGE_CREATION: "internal-tool-image-generation",
    AgentInternalTool.DATA_ANALYSIS: "internal-tool-data-analysis",
    AgentInternalTool.PLANNER: "internal-tool-planner",
    AgentInternalTool.PYTHON_SANDBOX: "internal-tool-pyodide",
    AgentInternalTool.SWARM_MODE: "internal-tool-swarm",
    AgentInternalTool.SMART_TOOLS: "internal-tool-lazy-tools-mode",
}


def get_tool_testid(tool: AgentInternalTool) -> str:
    """Get the data-testid for the internal tool container box.

    The container box testid is `internal-tool-{name}`.
    The switch element inside has testid `internal-tool-{name}-switch`.

    Args:
        tool: The internal tool enum value.

    Returns:
        The data-testid attribute value for the tool container.
    """
    return INTERNAL_TOOL_TESTIDS.get(tool, f"internal-tool-{tool.value.lower().replace(' ', '-')}")

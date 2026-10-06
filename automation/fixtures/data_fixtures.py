"""Test data fixtures that create and cleanup test entities.

These fixtures use the API clients to create fresh test data for each test,
ensuring complete isolation between tests. Each fixture follows the pattern:
1. Create entity with unique name (based on test name)
2. Yield entity ID (or data dict) to test
3. Delete entity in teardown (even if test fails)

All fixtures are function-scoped, meaning each test gets a fresh entity.

Fixtures:
- conversation_id: Fresh conversation per test
- agent_id: Fresh agent per test
- pipeline_id: Fresh empty pipeline per test
- pipeline_with_llm_id: Fresh executable pipeline with LLM node
- pipeline_with_variable_task_llm_id: Fresh executable pipeline with LLM node,
  TASK mapped ``type: variable, value: input`` (forwards the user's message,
  incl. attachment reference, into the LLM node — ELITEA-2059)
- github_credential: GitHub API credential (skipped if GITHUB_TOKEN unset)
- github_toolkit: GitHub toolkit attached to a fresh credential
- github_toolkit_with_selected_tools: GitHub toolkit with settings.selected_tools
  set (required for the pipeline Toolkit node's Tool select to render)
"""
import logging
import time

import pytest
from api import AgentAPI, ArtifactAPI, ConversationAPI, CredentialAPI, PipelineAPI, ToolkitAPI
from config import settings

logger = logging.getLogger("elitea.automation.fixtures.data")

# Branch used to configure the GitHub toolkit and to verify toolkit responses.
_GITHUB_BRANCH = "main"


@pytest.fixture
def conversation_id(conversation_api: ConversationAPI, request):
    """Create a fresh conversation before the test and delete it afterwards.

    The conversation is created via the API with a unique name based on
    the test function name. This ensures complete isolation between tests.

    Yields the conversation ID as a string so tests can navigate to
    ``/chat/{conversation_id}`` or use it with the API.

    Args:
        conversation_api: ConversationAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        str: Numeric conversation ID as string

    Example:
        def test_send_message(page, conversation_id):
            chat = ChatPage(page)
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.send_message("Hello")
            # conversation is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    conv = conversation_api.create_conversation(name)
    conv_id = conv["id"]
    logger.info("Created conversation %s (%s) for %s", conv_id, name, request.node.name)

    yield str(conv_id)

    # Cleanup: delete conversation even if test fails
    try:
        conversation_api.delete_conversation(conv_id)
        logger.info("Deleted conversation %s", conv_id)
    except Exception as exc:
        logger.warning("Failed to delete conversation %s: %s", conv_id, exc)


@pytest.fixture
def agent_id(agent_api: AgentAPI, request):
    """Create a fresh agent before the test and delete it afterwards.

    The agent is created via the API with:
    - Unique name based on test function name
    - Basic description
    - Default instructions

    Yields the agent ID as an integer so tests can navigate to
    ``/agents/all/{agent_id}`` or use it with the API.

    Args:
        agent_api: AgentAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric agent ID

    Example:
        def test_agent_detail(page, agent_id):
            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)
            # agent is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    description = f"Auto-created for test {request.node.name}"
    agent = agent_api.create_agent(name, description, instructions="You are a test agent.")
    aid = agent["id"]
    logger.info("Created agent %s (%s) for %s", aid, name, request.node.name)

    yield aid

    # Cleanup: delete agent even if test fails
    try:
        agent_api.delete_agent(aid)
        logger.info("Deleted agent %s", aid)
    except Exception as exc:
        logger.warning("Failed to delete agent %s: %s", aid, exc)


@pytest.fixture
def pipeline_id(pipeline_api: PipelineAPI, request):
    """Create a fresh empty pipeline before the test and delete it afterwards.

    The pipeline is created via the API with a unique name based on the
    test function name. The pipeline starts empty (no nodes or connections).

    Yields the numeric pipeline ID so tests can navigate to
    ``/pipelines/all/{pipeline_id}`` or use it with the API.

    Args:
        pipeline_api: PipelineAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric pipeline ID

    Example:
        def test_pipeline_editor(page, pipeline_id):
            editor = PipelineEditorPage(page)
            editor.navigate(pipeline_id)
            editor.add_node("llm")
            # pipeline is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # API enforces 32-char max
    description = f"Auto-created for test {request.node.name}"
    pipeline = pipeline_api.create_pipeline(name, description)
    pid = pipeline["id"]
    logger.info("Created pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    # Cleanup: delete pipeline even if test fails
    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_with_llm_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline with a single LLM node connected to END.

    This pipeline can actually execute — it receives a user message via
    the LLM node and produces a response. Useful for testing pipeline
    execution, chat integration, and end-to-end flows.

    The pipeline structure:
    - START node
    - LLM node (connected to START)
    - END node (connected to LLM)

    Yields the numeric pipeline ID so tests can execute or navigate to it.

    Args:
        pipeline_api: PipelineAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        int: Numeric pipeline ID

    Example:
        def test_pipeline_execution(page, pipeline_with_llm_id):
            chat = ChatPage(page)
            chat.navigate_to_pipeline_chat(pipeline_with_llm_id)
            chat.send_message("Hello")
            chat.wait_for_ai_response()
            # pipeline is automatically deleted after test
    """
    name = f"autotest_{request.node.name}"[:32]  # Truncate to 32 chars
    description = f"Auto-created LLM pipeline for test {request.node.name}"
    pipeline = pipeline_api.create_pipeline_with_llm_node(name, description)
    pid = pipeline["id"]
    logger.info("Created LLM pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    # Cleanup: delete pipeline even if test fails
    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted LLM pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete LLM pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_with_fstring_llm_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline with a single LLM entry node whose TASK is an
    F-String template (``{input}``), connected directly to END.

    Satisfies the ELITEA-2017 precondition literally ("A pipeline with LLM
    node as entry point exists (TASK configured with F-String: '{input}')")
    — :func:`pipeline_with_llm_id` does NOT satisfy this as-is:
    ``PipelineAPI.create_pipeline_with_llm_node()`` hardcodes TASK as
    ``type: fixed, value: ''``, not an F-String (confirmed live, AFS
    ``l2_pipeline-execution-long-response-streaming_ELITEA-2017.md`` §
    Test Data). Built via the generic :meth:`PipelineAPI.create_pipeline_with_nodes`
    — the SAME helper :func:`pipeline_with_two_llm_nodes_id`/
    :func:`build_two_llm_nodes` already use for ELITEA-2452 — rather than
    adding a new parameter to ``create_pipeline_with_llm_node``.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2017_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created F-String LLM pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=[
            {
                "id": "LLM 1",
                "type": "llm",
                "input": [],
                "input_mapping": {
                    "chat_history": {"type": "fixed", "value": []},
                    "system": {"type": "fixed", "value": ""},
                    "task": {"type": "fstring", "value": "{input}"},
                },
                "output": [],
                "structured_output": False,
                "transition": "END",
            }
        ],
    )
    pid = pipeline["id"]
    logger.info("Created F-String LLM pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    # Cleanup: delete pipeline even if test fails
    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted F-String LLM pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete F-String LLM pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_with_variable_task_llm_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline with a single LLM entry node whose TASK is mapped
    ``type: variable, value: input`` (NOT the fixed/f-string shapes the
    sibling fixtures above use), connected directly to END.

    Satisfies the ELITEA-2059 precondition (AFS
    ``l2_pipeline-attach-files-in-chat_ELITEA-2059.md`` § Preconditions):
    :func:`pipeline_with_llm_id`'s TASK mapping is ``type: fixed, value: ''``
    (hardcoded by ``PipelineAPI.create_pipeline_with_llm_node()``), which
    never forwards the user's message text (or its attachment reference)
    into the LLM node — the response would always ignore whatever was
    typed/attached. Built via :meth:`PipelineAPI.create_pipeline_with_nodes`
    (same generic helper :func:`pipeline_with_fstring_llm_id` /
    :func:`pipeline_with_two_llm_nodes_id` already use) so the mapping is
    correct — and persisted — from creation, with no separate UI Save step
    needed. Uses the default ``gpt-5.2`` model (``_default_llm_settings()``'s
    fallback) — the DEV-backend default (Claude 4.5 Sonnet, on the shared
    ``test-pipeline`` UI fixture only) 400s with no configured LLM-provider
    fallback; AFS § Test Data records this as environment test data, not an
    Attach-Files defect.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2059_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created variable-TASK LLM pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=[
            {
                "id": "LLM 1",
                "type": "llm",
                "input": ["input"],
                "input_mapping": {
                    "chat_history": {"type": "fixed", "value": []},
                    "system": {"type": "fixed", "value": ""},
                    "task": {"type": "variable", "value": "input"},
                },
                "output": [],
                "structured_output": False,
                "transition": "END",
            }
        ],
    )
    pid = pipeline["id"]
    logger.info("Created variable-TASK LLM pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted variable-TASK LLM pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete variable-TASK LLM pipeline %s: %s", pid, exc)


def build_two_llm_nodes() -> list[dict]:
    """Build the ``LLM 1 -> LLM 2 -> END`` node list for ELITEA-2452.

    LLM 1 WRITES to ``messages`` (its ``output`` mapping); LLM 2 writes to
    nothing. The pipeline's two DEFAULT state variables (``input``,
    ``messages`` — no custom variable needed) exercise both observables the
    case requires: ``messages`` is modified at LLM 1 (not at LLM 2);
    ``input`` is populated once at pipeline entry and never modified again.
    Exact shape confirmed live this session (AFS ``l3_run-details-state-
    before-after-per-node_ELITEA-2452.md`` § Test Data, pipelines 7681/7682).
    """
    return [
        {
            "id": "LLM 1",
            "type": "llm",
            "input": [],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": "You are a helpful assistant."},
                "task": {"type": "fstring", "value": "User asked: {input}"},
            },
            "output": ["messages"],
            "structured_output": False,
            "transition": "LLM 2",
        },
        {
            "id": "LLM 2",
            "type": "llm",
            "input": ["messages"],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": "Reply with just OK."},
                "task": {"type": "fstring", "value": "Ack: {messages}"},
            },
            "output": [],
            "structured_output": False,
            "transition": "END",
        },
    ]


@pytest.fixture
def pipeline_with_two_llm_nodes_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> LLM 2 -> END`` (2 nodes, 2 default state
    variables) before the test and delete it afterwards. Satisfies the
    ELITEA-2452 precondition (2+ nodes, 2+ state variables, one node writes
    to a variable and one does not — see :func:`build_two_llm_nodes`).

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2452_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created 2-LLM-node pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_two_llm_nodes(),
    )
    pid = pipeline["id"]
    logger.info("Created 2-LLM-node pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted 2-LLM-node pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete 2-LLM-node pipeline %s: %s", pid, exc)


def build_three_llm_chain_nodes() -> list[dict]:
    """Build the ``LLM 1 -> LLM 2 -> LLM 3 -> END`` node list for ELITEA-2451.

    Three PLAIN (non-``structured_output``) LLM nodes chained in sequence —
    deliberately NOT the structured-output shape, which the ELITEA-2453
    sibling AFS found renders TWO timeline entries per execution (would break
    this case's own "entries == executed nodes" assertion). Exact shape
    confirmed live this session (AFS ``l3_run-details-timeline-steps-
    display_ELITEA-2451.md`` § Preconditions, pipeline id 8767).
    """
    return [
        {
            "id": "LLM 1",
            "type": "llm",
            "input": [],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": "You are a helpful assistant."},
                "task": {"type": "fixed", "value": "Say hello in exactly three words."},
            },
            "output": ["messages"],
            "structured_output": False,
            "transition": "LLM 2",
        },
        {
            "id": "LLM 2",
            "type": "llm",
            "input": ["messages"],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": "Reply with just OK."},
                "task": {"type": "fstring", "value": "Ack: {messages}"},
            },
            "output": [],
            "structured_output": False,
            "transition": "LLM 3",
        },
        {
            "id": "LLM 3",
            "type": "llm",
            "input": [],
            "input_mapping": {
                "chat_history": {"type": "fixed", "value": []},
                "system": {"type": "fixed", "value": "Reply with just DONE."},
                "task": {"type": "fixed", "value": "final ack"},
            },
            "output": [],
            "structured_output": False,
            "transition": "END",
        },
    ]


@pytest.fixture
def pipeline_three_llm_chain(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> LLM 2 -> LLM 3 -> END`` (3 plain LLM
    nodes) before the test and delete it afterwards. Satisfies the
    ELITEA-2451 precondition (3+ plain nodes, all `Completed` — see
    :func:`build_three_llm_chain_nodes`).

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2451_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created 3-LLM-chain pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_three_llm_chain_nodes(),
    )
    pid = pipeline["id"]
    logger.info("Created 3-LLM-chain pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted 3-LLM-chain pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete 3-LLM-chain pipeline %s: %s", pid, exc)


_TYPED_STATE_VARS_INSTRUCTIONS = """\
entry_point: LLM 1
state:
  custom_text:
    type: str
  custom_num:
    type: number
  custom_list:
    type: list
  custom_json:
    type: dict
nodes:
  - id: LLM 1
    type: llm
    input: []
    input_mapping:
      chat_history:
        type: fixed
        value: []
      system:
        type: fixed
        value: 'You populate structured state variables. Answer with a single JSON
          object and nothing else - no prose, no bullet lists, no markdown headings.
          The object must contain exactly these keys: custom_text (a short non-empty
          string), custom_num (a number), custom_list (a list of 3 short strings),
          custom_json (an object with 2 keys).'
      task:
        type: fstring
        value: '{input}'
    output: [custom_text, custom_num, custom_list, custom_json]
    structured_output: true
    transition: END
"""


@pytest.fixture
def pipeline_with_typed_state_vars_id(pipeline_api: PipelineAPI, request):
    """Create a pipeline with 4 CUSTOM state variables of 4 distinct types
    (``custom_text``/str, ``custom_num``/number, ``custom_list``/list,
    ``custom_json``/dict) plus the 2 built-in ``input``/``messages``
    variables, and a single LLM node with ``structured_output: true`` whose
    ``output`` mapping writes to all 4 custom variables. Satisfies the
    ELITEA-2453 precondition. Deletes the pipeline afterwards.

    Built via the GENERIC :meth:`PipelineAPI.create_pipeline` (raw YAML
    ``instructions`` string) rather than :meth:`create_pipeline_with_nodes`,
    which has no ``state:`` support -- confirmed live, AFS
    ``l3_run-details-multiple-state-variables-different-types_ELITEA-2453.md``
    § Preconditions.

    CRITICAL: ``messages`` is deliberately NOT included in this node's
    ``output`` list. Combining ``messages`` with `dict`/`list`-typed custom
    variables in a ``structured_output: true`` node's ``output`` mapping is a
    CONFIRMED product defect (``EliteaAI/elitea-testing-public#1274``) that
    makes the run fail with a raw backend error instead of populating state.

    The ``system`` prompt names the required answer FORM ("a single JSON
    object and nothing else"), not merely the values, because the state write
    only happens when the LLM's last call answers with a parseable JSON
    object; a prose/markdown answer writes NOTHING while the run still
    reports ``Completed`` (``EliteaAI/elitea-testing-public#2153``). Measured
    live on DEV 2026-09-10: 24/32 populated with the older value-only prompt
    vs 9/9 with this one. That is a MITIGATION, not a guarantee (n=9) — the
    consuming spec still guards the population explicitly and fails naming
    #2153 if it does not happen. This steers the real producer; it does not
    substitute it.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2453_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created typed-state-vars pipeline for test {request.node.name}",
        instructions=_TYPED_STATE_VARS_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created typed-state-vars pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted typed-state-vars pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete typed-state-vars pipeline %s: %s", pid, exc)


_CUSTOM_STATE_VAR_INSTRUCTIONS = """\
entry_point: LLM 1
state:
  custom_text:
    type: str
nodes:
  - id: LLM 1
    type: llm
    input: []
    input_mapping:
      chat_history:
        type: fixed
        value: []
      system:
        type: fixed
        value: ''
      task:
        type: fixed
        value: ''
    output: []
    structured_output: false
    transition: END
"""


@pytest.fixture
def pipeline_with_custom_state_var_id(pipeline_api: PipelineAPI, request):
    """Create a minimal pipeline with ONE custom state variable (``custom_text``,
    type ``str``) plus a single LLM node and an ``entry_point``. Deletes the
    pipeline afterwards.

    Satisfies the ELITEA-2026 precondition (pipeline with ≥1 node AND ≥1
    CUSTOM state variable). NOT the same as :func:`pipeline_with_llm_id` —
    that fixture's YAML has no ``state:`` key at all (confirmed live, AFS
    ``l2_pipeline-yaml-editor-view_ELITEA-2026.md`` § Preconditions clarifies
    that the case's own "any pipeline with nodes" wording does not, by
    itself, guarantee a ``state:`` key in the rendered YAML — only an
    explicit custom variable does).

    Built via the GENERIC :meth:`PipelineAPI.create_pipeline` (raw YAML
    ``instructions`` string), the same shape as
    :func:`pipeline_with_typed_state_vars_id` but with a single variable —
    that fixture's 4-variable recipe is unnecessarily rich for this case.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2026_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created custom-state-var pipeline for test {request.node.name}",
        instructions=_CUSTOM_STATE_VAR_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created custom-state-var pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted custom-state-var pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete custom-state-var pipeline %s: %s", pid, exc)


_LLM_READS_STATE_VIA_CODE_INSTRUCTIONS = """\
entry_point: LLM 1
state:
  user_info:
    type: str
  code_output:
    type: str
nodes:
  - id: LLM 1
    type: llm
    input: []
    input_mapping:
      chat_history:
        type: fixed
        value: []
      system:
        type: fixed
        value: You are a helpful assistant.
      task:
        type: fstring
        value: '{input}'
    output: [user_info]
    structured_output: false
    transition: Code 1
  - id: Code 1
    type: code
    code:
      type: fixed
      value: |
        result = elitea_state.get('user_info', '')
        {"code_output": f"Processed: {result}"}
    input: [user_info]
    output: [code_output]
    structured_output: true
    transition: END
"""


@pytest.fixture
def pipeline_llm_reads_state_via_code(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> Code 1 -> END`` with two CUSTOM state
    variables (``user_info``/str, ``code_output``/str): the LLM node writes
    its response into ``user_info``, the Code node reads it back via
    ``elitea_state.get('user_info', '')`` and writes a processed value into
    ``code_output``. Deletes the pipeline afterwards.

    Satisfies the ELITEA-2446 precondition. Built via the GENERIC
    :meth:`PipelineAPI.create_pipeline` (raw YAML ``instructions`` string)
    rather than :meth:`create_pipeline_with_nodes`, which has no ``state:``
    support -- confirmed live, AFS
    ``l3_code-node-read-elitea-state-variables_ELITEA-2446.md`` §
    Preconditions -- the SAME reason :func:`pipeline_with_typed_state_vars_id`
    uses this method.

    CRITICAL: the Code node's script ends with a bare dict-literal
    expression (``{"code_output": f"Processed: {result}"}``) as its LAST
    statement, NOT a plain assignment. A plain assignment (the case's own
    literal step-4 text) is CONFIRMED LIVE to silently produce no state
    update (AFS Known Defects CLARIFICATION #1,
    ``EliteaAI/elitea-testing-public#1383``) -- the dict-literal form is the
    live-correct one per ``.claude/skills/elitea-pipeline/references/
    yaml-schema.md``'s own documented Code Node rule.

    Also CRITICAL: this fixture wires the ``LLM 1 -> Code 1`` transition
    explicitly in the YAML, sidestepping a SEPARATE confirmed-live gotcha
    where building the same topology via the Flow Editor's "Add node"
    button does NOT auto-connect sequentially-added nodes (AFS Known Defects
    CLARIFICATION #2, ``EliteaAI/elitea-testing-public#1384``).

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2446_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created LLM-reads-state-via-code pipeline for test {request.node.name}",
        instructions=_LLM_READS_STATE_VIA_CODE_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created LLM-reads-state-via-code pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted LLM-reads-state-via-code pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete LLM-reads-state-via-code pipeline %s: %s", pid, exc)


_CODE_NODE_MULTI_VAR_DICT_RETURN_INSTRUCTIONS = """\
entry_point: STATE1
state:
  summary:
    type: str
  count:
    type: number
  tags:
    type: list
nodes:
  - id: STATE1
    type: state_modifier
    template: 'Draft summary text'
    variables_to_clean: []
    input: []
    output: [summary]
    transition: CODE1
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        data = elitea_state.get('summary', '')
        {'summary': data + ' [processed]', 'count': len(data.split()), 'tags': ['processed', 'automated']}
    input: [summary]
    output: [summary, count, tags]
    structured_output: true
    transition: END
"""


@pytest.fixture
def pipeline_code_node_multi_var_dict_return(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``STATE1 (state_modifier) -> CODE1 (code) -> END``
    with THREE custom state variables (``summary``/str, ``count``/number,
    ``tags``/list). STATE1 gives ``summary`` a deterministic starting value
    (a fixed Jinja template, no variables -- NOT an LLM node, so ``count``'s
    expected value stays a stable literal). CODE1 reads ``summary`` via
    ``elitea_state.get('summary', '')`` and, as its script's LAST statement,
    returns a bare THREE-key dict literal that updates ``summary`` (appended
    text), ``count`` (word count), and ``tags`` (a fixed list) -- all from
    the SAME single Code node execution.

    Satisfies the ELITEA-2447 precondition. Built via the GENERIC
    :meth:`PipelineAPI.create_pipeline` (raw YAML ``instructions`` string),
    same reason :func:`pipeline_llm_reads_state_via_code` /
    :func:`pipeline_with_typed_state_vars_id` use it --
    :meth:`create_pipeline_with_nodes` has no ``state:`` support.

    CONFIRMED LIVE (AFS ``l3_code-node-return-dict-multiple-state-vars_
    ELITEA-2447.md`` § Test Data): the Code node's Output multi-select
    accepts ``summary`` even though it is ALSO in that same node's own
    ``input`` list -- no validation error; Run Details correctly attributes
    the update to the single node that both read and wrote it.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2447_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created Code-node multi-var dict-return pipeline for test {request.node.name}",
        instructions=_CODE_NODE_MULTI_VAR_DICT_RETURN_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created Code-node multi-var dict-return pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted Code-node multi-var dict-return pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete Code-node multi-var dict-return pipeline %s: %s", pid, exc)


_CODE_NODE_ELITEA_CLIENT_USER_INFO_INSTRUCTIONS = """\
entry_point: Code 1
state:
  user_info:
    type: JSON
nodes:
  - id: Code 1
    type: code
    code:
      type: fixed
      value: |
        user_info = elitea_client.get_user_data()
        user_info
    input: []
    output: [user_info]
    structured_output: true
    transition: END
"""


@pytest.fixture
def pipeline_code_node_elitea_client_user_info(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``Code 1 (entry) -> END`` with ONE custom JSON-typed
    state variable (``user_info``). The Code node calls
    ``elitea_client.get_user_data()`` and writes the returned dict into
    ``user_info`` via a bare NAME-reference expression (``user_info``) as the
    script's LAST statement -- distinct from
    :func:`pipeline_llm_reads_state_via_code` /
    :func:`pipeline_code_node_multi_var_dict_return`'s bare dict-LITERAL
    convention, but confirmed live to work identically: both are
    non-assignment expression statements the runtime routes into the
    declared ``output:`` variable when ``structured_output: true``.

    Satisfies the ELITEA-2448 precondition. Built via the GENERIC
    :meth:`PipelineAPI.create_pipeline` (raw YAML ``instructions`` string),
    same reason :func:`pipeline_llm_reads_state_via_code` /
    :func:`pipeline_code_node_multi_var_dict_return` use it --
    :meth:`create_pipeline_with_nodes` has no ``state:`` support. This is the
    SIMPLEST fixture in the Code-node family -- one node, no chained
    transition, so the disconnected-edge build-method gotcha
    (``EliteaAI/elitea-testing-public#1384``) doesn't even apply here, but the
    raw-YAML build is kept for consistency with the sibling fixtures.

    CONFIRMED LIVE (AFS
    ``l3_code-node-elitea-client-user-info_ELITEA-2448.md`` § Test Data): the
    case's own literal script -- ``user_info = elitea_client.get_user_data()``
    followed by a bare ``user_info`` name reference -- works exactly as
    written; no CLARIFICATION needed.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2448_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created Code-node elitea_client user-info pipeline for test {request.node.name}",
        instructions=_CODE_NODE_ELITEA_CLIENT_USER_INFO_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created Code-node elitea_client user-info pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted Code-node elitea_client user-info pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete Code-node elitea_client user-info pipeline %s: %s", pid, exc)


_CODE_NODE_INPUT_FILTERING_INSTRUCTIONS = """\
entry_point: STATE_A
state:
  var_a:
    type: str
  var_b:
    type: str
  var_c:
    type: str
  result:
    type: str
nodes:
  - id: STATE_A
    type: state_modifier
    template: 'AAA'
    variables_to_clean: []
    input: []
    output: [var_a]
    transition: STATE_B
  - id: STATE_B
    type: state_modifier
    template: 'BBB'
    variables_to_clean: []
    input: []
    output: [var_b]
    transition: STATE_C
  - id: STATE_C
    type: state_modifier
    template: 'CCC'
    variables_to_clean: []
    input: []
    output: [var_c]
    transition: CODE1
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        available_keys = list(elitea_state.keys())
        has_var_c = 'var_c' in elitea_state
        result = f"Keys: {available_keys}, has_var_c: {has_var_c}"
        {"result": result}
    input: [var_a, var_b]
    output: [result]
    structured_output: true
    transition: END
"""


@pytest.fixture
def pipeline_code_node_input_filtering(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``STATE_A -> STATE_B -> STATE_C -> CODE1 -> END`` with
    THREE custom state variables (``var_a``/``var_b``/``var_c``, all str) plus
    a ``result`` output variable. The three ``state_modifier`` nodes (NOT LLM
    nodes -- deterministic literals) give ``var_a``/``var_b``/``var_c`` the
    fixed values ``'AAA'``/``'BBB'``/``'CCC'`` respectively, in that order,
    before CODE1 runs. CODE1's own ``input:`` DELIBERATELY lists only
    ``var_a``/``var_b`` -- ``var_c`` is excluded even though it was already
    set by STATE_C earlier in the SAME run. CODE1 reads
    ``list(elitea_state.keys())`` and checks ``'var_c' in elitea_state``,
    writing both into ``result`` as its script's LAST statement, a bare
    dict-literal expression (same confirmed-live-working convention as
    :func:`pipeline_llm_reads_state_via_code` / :func:`pipeline_code_node_multi_var_dict_return`).

    Satisfies the ELITEA-2449 precondition. Built via the GENERIC
    :meth:`PipelineAPI.create_pipeline` (raw YAML ``instructions`` string),
    same reason the sibling Code-node fixtures use it --
    :meth:`create_pipeline_with_nodes` has no ``state:`` support. The explicit
    ``transition:`` per node sidesteps the SAME disconnected-edge build-method
    gotcha (``EliteaAI/elitea-testing-public#1384``) already documented for
    ELITEA-2446/2447.

    CONFIRMED LIVE (AFS
    ``l3_code-node-input-filtering-selective-state-access_ELITEA-2449.md`` §
    Test Data): ``elitea_state`` inside the Code node's sandbox contains ONLY
    the variables listed in that node's own ``input:`` -- ``var_c``, though
    declared in the pipeline's ``state:`` and written by STATE_C earlier in
    THIS run, is completely absent from ``elitea_state.keys()``. ``var_c``'s
    own Run Details row still shows a real Before/After value (``"CCC"``) --
    that row's existence is orthogonal to whether CODE1 itself could read the
    variable via ``elitea_state``.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_2449_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline(
        name=name,
        description=f"Auto-created Code-node input-filtering pipeline for test {request.node.name}",
        instructions=_CODE_NODE_INPUT_FILTERING_INSTRUCTIONS,
    )
    pid = pipeline["id"]
    logger.info("Created Code-node input-filtering pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted Code-node input-filtering pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete Code-node input-filtering pipeline %s: %s", pid, exc)


_PARENT_CHILD_STATE_SHARING_CHILD_INSTRUCTIONS = """\
entry_point: CODE1
state:
  messages:
    type: list
  state_1:
    type: str
  state_2:
    type: number
nodes:
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        {"state_1": "child_value", "state_2": 99}
    input: [state_1, state_2]
    output: [state_1, state_2]
    structured_output: true
    transition: END
"""


def _build_parent_child_state_sharing_parent_instructions(child_pipeline_name: str) -> str:
    """Build the PARENT pipeline's YAML for :func:`pipeline_parent_child_state_sharing`.

    CODE1 sets ONLY ``state_1`` (never touches ``state_2``), then transitions
    to AGENT1, an ``agent``-type node whose ``tool:`` field names the already
    -created child pipeline. This pre-sets the YAML reference the AFS
    Preconditions describe -- the test itself still has to perform the
    Tools-section "+ Pipeline" attach (``PipelineDetailPage.open_pipeline_popper``/
    ``select_pipeline_in_popper``) before AGENT1 can resolve it; the bare
    ``tool:`` field is NOT sufficient by itself (confirmed live, ELITEA-2443
    AFS § Preconditions).

    Args:
        child_pipeline_name: Exact ``name`` of the already-created child
            pipeline (see :data:`_PARENT_CHILD_STATE_SHARING_CHILD_INSTRUCTIONS`).
    """
    return f"""\
entry_point: CODE1
state:
  messages:
    type: list
  state_1:
    type: str
  state_2:
    type: number
nodes:
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        {{"state_1": "parent_value"}}
    input: [state_1]
    output: [state_1]
    structured_output: true
    transition: AGENT1
  - id: AGENT1
    type: agent
    input: [input]
    output: [messages]
    input_mapping:
      task:
        type: fixed
        value: "Run the child pipeline and share state."
      chat_history:
        type: fixed
        value: []
    tool: {child_pipeline_name}
    transition: END
"""


@pytest.fixture
def pipeline_parent_child_state_sharing(pipeline_api: PipelineAPI, request):
    """Create a CHILD pipeline (``state_1``/``state_2``, one ``code`` node
    overwriting both -- ``{"state_1": "child_value", "state_2": 99}``) and a
    PARENT pipeline (same ``state_1``/``state_2`` names, CODE1 sets only
    ``state_1`` then transitions to AGENT1, an ``agent``-type node whose YAML
    ``tool:`` field already names the child pipeline). Satisfies the
    ELITEA-2443 precondition. Deletes BOTH pipelines afterwards (order
    -independent -- no FK constraint observed deleting the parent before the
    child, confirmed live during analysis).

    Built via the GENERIC :meth:`PipelineAPI.create_pipeline` (raw YAML
    ``instructions`` string) -- same technique as
    :func:`pipeline_with_typed_state_vars_id` -- :meth:`create_pipeline_with_nodes`
    has no ``state:`` support.

    CRITICAL (AFS Preconditions, confirmed live): the Agent node's ``tool:``
    field alone does NOT resolve the child pipeline -- an Agent node needs
    the child ALSO attached via the Tools section's "+ Pipeline" popper, or
    it renders "Agent not found -- select a replacement or delete this node"
    even though the YAML name is byte-correct. That attach is a real RUNTIME
    step the TEST itself must perform; this fixture only builds the two
    pipelines and pre-sets the YAML ``tool:`` field.

    Yields:
        dict: ``{"parent_id": int, "parent_name": str, "child_id": int,
        "child_name": str}``
    """
    child_name = f"autotest_2443c_{request.node.name}"[:32]
    child = pipeline_api.create_pipeline(
        name=child_name,
        description=f"Auto-created ELITEA-2443 child pipeline for test {request.node.name}",
        instructions=_PARENT_CHILD_STATE_SHARING_CHILD_INSTRUCTIONS,
    )
    child_id = child["id"]
    logger.info(
        "Created ELITEA-2443 child pipeline %s (%s) for %s", child_id, child_name, request.node.name
    )

    parent_name = f"autotest_2443p_{request.node.name}"[:32]
    parent = pipeline_api.create_pipeline(
        name=parent_name,
        description=f"Auto-created ELITEA-2443 parent pipeline for test {request.node.name}",
        instructions=_build_parent_child_state_sharing_parent_instructions(child_name),
    )
    parent_id = parent["id"]
    logger.info(
        "Created ELITEA-2443 parent pipeline %s (%s) for %s", parent_id, parent_name, request.node.name
    )

    yield {
        "parent_id": parent_id,
        "parent_name": parent_name,
        "child_id": child_id,
        "child_name": child_name,
    }

    try:
        pipeline_api.delete_pipeline(parent_id)
        logger.info("Deleted ELITEA-2443 parent pipeline %s", parent_id)
    except Exception as exc:
        logger.warning("Failed to delete ELITEA-2443 parent pipeline %s: %s", parent_id, exc)
    try:
        pipeline_api.delete_pipeline(child_id)
        logger.info("Deleted ELITEA-2443 child pipeline %s", child_id)
    except Exception as exc:
        logger.warning("Failed to delete ELITEA-2443 child pipeline %s: %s", child_id, exc)


_PARENT_CHILD_STATE_ISOLATION_CHILD_INSTRUCTIONS = """\
entry_point: CODE1
state:
  messages:
    type: list
  state_1:
    type: str
  state_3:
    type: str
nodes:
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        {"state_1": "child_value", "state_3": "child_only_value"}
    input: [state_1, state_3]
    output: [state_1, state_3]
    structured_output: true
    transition: END
"""


def _build_parent_child_state_isolation_parent_instructions(child_pipeline_name: str) -> str:
    """Build the PARENT pipeline's YAML for :func:`pipeline_parent_child_state_isolation`.

    CODE1 sets BOTH ``state_1`` AND ``state_2`` (unlike
    :func:`pipeline_parent_child_state_sharing`'s parent, which sets only
    ``state_1``), then transitions to AGENT1, an ``agent``-type node whose
    ``tool:`` field names the already-created child pipeline. Same Tools
    -section attach precondition as the sibling fixture (AFS ELITEA-2444
    § Preconditions, confirmed live) -- the bare ``tool:`` field alone does
    not resolve the child; the test itself still performs the "+ Pipeline"
    popper attach.

    Args:
        child_pipeline_name: Exact ``name`` of the already-created child
            pipeline (see :data:`_PARENT_CHILD_STATE_ISOLATION_CHILD_INSTRUCTIONS`).
    """
    return f"""\
entry_point: CODE1
state:
  messages:
    type: list
  state_1:
    type: str
  state_2:
    type: str
nodes:
  - id: CODE1
    type: code
    code:
      type: fixed
      value: |
        {{"state_1": "parent_value", "state_2": "parent_only_value"}}
    input: [state_1, state_2]
    output: [state_1, state_2]
    structured_output: true
    transition: AGENT1
  - id: AGENT1
    type: agent
    input: [input]
    output: [messages]
    input_mapping:
      task:
        type: fixed
        value: "Run the child pipeline and share state."
      chat_history:
        type: fixed
        value: []
    tool: {child_pipeline_name}
    transition: END
"""


@pytest.fixture
def pipeline_parent_child_state_isolation(pipeline_api: PipelineAPI, request):
    """Create a CHILD pipeline (``state_1``/``state_3``, NO ``state_2`` key at
    all) and a PARENT pipeline (``state_1``/``state_2``, NO ``state_3`` key at
    all) attached as a tool to the parent's Agent node. Satisfies the
    ELITEA-2444 precondition -- the defining difference from
    :func:`pipeline_parent_child_state_sharing` is that ``state_2`` and
    ``state_3`` are each declared in ONLY ONE of the two pipelines
    (non-common state), unlike that fixture's fully-shared
    ``state_1``/``state_2`` schema. Deletes BOTH pipelines afterwards
    (order-independent, confirmed live during analysis).

    Built via the GENERIC :meth:`PipelineAPI.create_pipeline` (raw YAML
    ``instructions`` string) -- :meth:`create_pipeline_with_nodes` has no
    ``state:`` support.

    CRITICAL (AFS Preconditions, confirmed live): the Agent node's ``tool:``
    field alone does NOT resolve the child pipeline -- an Agent node needs
    the child ALSO attached via the Tools section's "+ Pipeline" popper, or
    it renders "Agent not found -- select a replacement or delete this node"
    even though the YAML name is byte-correct. That attach is a real RUNTIME
    step the TEST itself must perform; this fixture only builds the two
    pipelines and pre-sets the YAML ``tool:`` field.

    Yields:
        dict: ``{"parent_id": int, "parent_name": str, "child_id": int,
        "child_name": str}``
    """
    child_name = f"autotest_2444c_{request.node.name}"[:32]
    child = pipeline_api.create_pipeline(
        name=child_name,
        description=f"Auto-created ELITEA-2444 child pipeline for test {request.node.name}",
        instructions=_PARENT_CHILD_STATE_ISOLATION_CHILD_INSTRUCTIONS,
    )
    child_id = child["id"]
    logger.info(
        "Created ELITEA-2444 child pipeline %s (%s) for %s", child_id, child_name, request.node.name
    )

    parent_name = f"autotest_2444p_{request.node.name}"[:32]
    parent = pipeline_api.create_pipeline(
        name=parent_name,
        description=f"Auto-created ELITEA-2444 parent pipeline for test {request.node.name}",
        instructions=_build_parent_child_state_isolation_parent_instructions(child_name),
    )
    parent_id = parent["id"]
    logger.info(
        "Created ELITEA-2444 parent pipeline %s (%s) for %s", parent_id, parent_name, request.node.name
    )

    yield {
        "parent_id": parent_id,
        "parent_name": parent_name,
        "child_id": child_id,
        "child_name": child_name,
    }

    try:
        pipeline_api.delete_pipeline(parent_id)
        logger.info("Deleted ELITEA-2444 parent pipeline %s", parent_id)
    except Exception as exc:
        logger.warning("Failed to delete ELITEA-2444 parent pipeline %s: %s", parent_id, exc)
    try:
        pipeline_api.delete_pipeline(child_id)
        logger.info("Deleted ELITEA-2444 child pipeline %s", child_id)
    except Exception as exc:
        logger.warning("Failed to delete ELITEA-2444 child pipeline %s: %s", child_id, exc)


@pytest.fixture
def github_credential(credential_api: CredentialAPI, request):
    """Create a GitHub API credential and yield its metadata.

    Skips the test if ``GITHUB_TOKEN`` is not set in the environment
    (loaded from ``.env.test``).

    Yields a dict with ``id`` and ``elitea_title`` keys.
    Deletes the credential in teardown even if the test fails.

    Args:
        credential_api: CredentialAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "elitea_title": str}``
    """
    if not settings.git_hub_token:
        pytest.skip("GIT_HUB_TOKEN not set in .env.test")

    name = f"autotest_gh_cred_{request.node.name}"[:32]
    cred = credential_api.create_github_credential(
        display_name=name,
        base_url=settings.github_base_url,
        token=settings.git_hub_token,
    )
    logger.info("Created GitHub credential %s (%s) for %s", cred["id"], name, request.node.name)

    yield {"id": cred["id"], "elitea_title": cred["elitea_title"]}

    try:
        credential_api.delete_credential(cred["id"])
        logger.info("Deleted GitHub credential %s", cred["id"])
    except Exception as exc:
        logger.warning("Failed to delete credential %s during teardown: %s", cred["id"], exc)


@pytest.fixture
def github_toolkit(github_credential: dict, toolkit_api: ToolkitAPI, request):
    """Create a GitHub toolkit linked to a fresh credential.

    Depends on ``github_credential`` — both are cleaned up after the test.
    The toolkit is configured against ``_GITHUB_REPO`` / ``_GITHUB_BRANCH``.

    Yields a dict with ``id``, ``name``, and ``branch`` keys so tests can
    assert that the known branch appears in toolkit responses without needing
    to import module-level constants.

    Args:
        github_credential: GitHub credential fixture (provides elitea_title)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "branch": str}``
    """
    name = f"autotest_gh_toolkit_{request.node.name}"[:32]
    toolkit = toolkit_api.create_github_toolkit(
        name=name,
        description=f"Auto-created for test {request.node.name}",
        credential_elitea_title=github_credential["elitea_title"],
        repository=settings.git_repo,
        active_branch=_GITHUB_BRANCH,
        base_branch=_GITHUB_BRANCH,
    )
    logger.info("Created GitHub toolkit %s (%s) for %s", toolkit["id"], name, request.node.name)

    yield {"id": toolkit["id"], "name": name, "branch": _GITHUB_BRANCH}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted GitHub toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s during teardown: %s", toolkit["id"], exc)


@pytest.fixture
def github_toolkit_with_selected_tools(github_credential: dict, toolkit_api: ToolkitAPI, request):
    """Create a GitHub toolkit with ``settings.selected_tools`` explicitly set.

    Sibling of :func:`github_toolkit` — that fixture does NOT set
    ``selected_tools``, which is fine for toolkit-attach/agent flows but is a
    load-bearing gap for the pipeline Toolkit node (ELITEA-2010 AFS §
    Preconditions / Automation Hints): a toolkit with no ``selected_tools``
    renders a Toolkit node with no Tool select at all (0 options, absent
    from the DOM, confirmed live) — the node's Tool dropdown reads the
    toolkit's own ``settings.selected_tools``, not a dynamic "discover all
    tools" call. This fixture selects ``search_issues`` (1 required param —
    SEARCH QUERY — plus 2 optional — MAX COUNT / REPO NAME), matching the
    AFS's Test Data.

    Depends on ``github_credential`` — both are cleaned up after the test.

    Yields a dict with ``id``, ``name``, and ``branch`` keys — same shape as
    :func:`github_toolkit`.

    Args:
        github_credential: GitHub credential fixture (provides elitea_title)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "branch": str}``
    """
    name = f"autotest_gh_tk_tools_{request.node.name}"[:32]
    toolkit = toolkit_api.create_github_toolkit(
        name=name,
        description=f"Auto-created for test {request.node.name}",
        credential_elitea_title=github_credential["elitea_title"],
        repository=settings.git_repo,
        active_branch=_GITHUB_BRANCH,
        base_branch=_GITHUB_BRANCH,
        selected_tools=["search_issues"],
    )
    logger.info(
        "Created GitHub toolkit %s (%s, selected_tools=['search_issues']) for %s",
        toolkit["id"], name, request.node.name,
    )

    yield {"id": toolkit["id"], "name": name, "branch": _GITHUB_BRANCH}

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted GitHub toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete toolkit %s during teardown: %s", toolkit["id"], exc)


# ---------------------------------------------------------------------------
# Artifact bucket + toolkit fixtures for ELITEA-1327
# ---------------------------------------------------------------------------


@pytest.fixture
def artifact_bucket(artifact_api: ArtifactAPI, request):
    """Create a fresh artifact bucket before the test and delete it afterwards.

    The bucket is created with a unique name based on the test function name
    and a millisecond timestamp to guarantee uniqueness across parallel or
    repeated runs.

    Yields a dict with ``name`` and ``id`` keys.

    Args:
        artifact_api: ArtifactAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"name": str, "id": str}``

    Example:
        def test_bucket_files(page, artifact_bucket):
            bucket_name = artifact_bucket["name"]
            # bucket is automatically deleted after test
    """
    ts = str(int(time.time() * 1000))[-6:]  # last 6 digits for brevity
    # Bucket names: lowercase, hyphens only, max ~63 chars
    raw = f"autotest-{request.node.name}"
    safe = raw.lower().replace("_", "-").replace("[", "").replace("]", "")[:40]
    name = f"{safe}-{ts}"

    bucket = artifact_api.create_bucket(name)
    logger.info("Created artifact bucket '%s' (id=%s) for %s", name, bucket.get("id"), request.node.name)

    yield {"name": name, "id": bucket.get("id", name)}

    try:
        artifact_api.delete_bucket(name)
        logger.info("Deleted artifact bucket '%s'", name)
    except Exception as exc:
        logger.warning("Failed to delete artifact bucket '%s': %s", name, exc)


@pytest.fixture
def artifact_toolkit(artifact_bucket: dict, toolkit_api: ToolkitAPI, request):
    """Create an Artifact toolkit connected to a fresh bucket.

    Depends on ``artifact_bucket`` — both are cleaned up after the test.

    Yields a dict with ``id``, ``name``, and ``bucket_name`` keys so tests
    can attach the toolkit to an agent by name and verify bucket contents.

    Args:
        artifact_bucket: Artifact bucket fixture (provides bucket name)
        toolkit_api: ToolkitAPI client (from api_fixtures)
        request: Pytest request object (provides test metadata)

    Yields:
        dict: ``{"id": int, "name": str, "bucket_name": str}``

    Example:
        def test_agent_creates_files(page, agent_id, artifact_toolkit):
            toolkit_name = artifact_toolkit["name"]
            bucket_name = artifact_toolkit["bucket_name"]
            # attach toolkit to agent via UI, then run assertions
    """
    ts = str(int(time.time()))
    raw = f"autotest-art-{request.node.name}"
    name = raw[:28] + f"-{ts[-4:]}"   # keep total ≤ 32 chars (API limit)

    bucket_name = artifact_bucket["name"]
    toolkit = toolkit_api.create_artifact_toolkit(
        name=name,
        description=f"Auto-created artifact toolkit for {request.node.name}",
        bucket_name=bucket_name,
    )
    logger.info(
        "Created artifact toolkit %s ('%s') → bucket '%s' for %s",
        toolkit["id"], name, bucket_name, request.node.name,
    )

    yield {
        "id": toolkit["id"],
        "name": name,
        "bucket_name": bucket_name,
        "project_id": int(toolkit_api.project_id),  # ELITEA-2203: slash-mention menu-item testids need it
    }

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted artifact toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete artifact toolkit %s: %s", toolkit["id"], exc)


# ---------------------------------------------------------------------------
# MCP toolkit + pipeline fixtures for ELITEA-1954
# ---------------------------------------------------------------------------

# Public, auth-free MCP endpoint used to provision a throwaway MCP toolkit
# with a real, non-empty tool list (3 tools: read_wiki_structure,
# read_wiki_contents, ask_wiki_question). Picked over the environment's
# pre-existing placeholder-URL MCPs (which return zero tools) and over
# "Remote Github" (whose live OAuth session is disconnected, though its
# CACHED tool list still renders) — see
# test-specs/pipelines/l2_mcp-node-change-toolkit-and-tool_ELITEA-1954.md
# § Test Data for the full rationale.
_MCP_DEEPWIKI_URL = "https://mcp.deepwiki.com/mcp"

# Second public, auth-free MCP endpoint (2 tools: resolve-library-id,
# query-docs) — provisions the INITIAL toolkit of the ELITEA-1954 precondition
# node. Replaced the environment's pre-existing "Remote Github" MCP (fixed id
# `remote_github_mcp_toolkit_id`), which doesn't exist on every environment
# (missing on stage2 → setup error). Its tool set is disjoint from DeepWiki's,
# so the test's "no stale tool leakage" check stays meaningful.
_MCP_CONTEXT7_URL = "https://mcp.context7.com/mcp"
_MCP_CONTEXT7_PREFERRED_TOOL = "resolve-library-id"


@pytest.fixture
def mcp_toolkit_with_tools(toolkit_api: ToolkitAPI, request):
    """Create a throwaway Remote MCP toolkit with a real, working tool list.

    Probes the public, auth-free ``mcp.deepwiki.com`` endpoint via
    ``ToolkitAPI.sync_mcp_tools`` (the same call the UI's "Load Tools"
    button makes) and bakes the result into the toolkit's
    ``settings.selected_tools`` / ``settings.available_mcp_tools`` at
    creation time, so a pipeline MCP node attached to this toolkit shows a
    real, non-empty Tool dropdown — a plain ``create_toolkit(type="mcp")``
    without a synced tool list does NOT populate the Tool dropdown (see
    ``ToolkitAPI.create_remote_mcp_toolkit`` docstring).

    Yields:
        dict: ``{"id": int, "name": str, "toolkit_name": str, "tools": list[str]}``
    """
    from api.helpers import sync_mcp_tools_with_retry

    name = f"autotest_mcp_{request.node.name}"[:32]

    # Use retry logic to handle transient pool saturation (503 errors)
    tools = sync_mcp_tools_with_retry(
        toolkit_api,
        _MCP_DEEPWIKI_URL,
        max_retries=3,
        initial_delay=5,
        timeout=60
    )
    assert tools, f"mcp_sync_tools returned no tools for {_MCP_DEEPWIKI_URL!r} — endpoint may be down"

    toolkit = toolkit_api.create_remote_mcp_toolkit(
        name=name,
        description=f"Auto-created MCP for test {request.node.name}",
        url=_MCP_DEEPWIKI_URL,
        tools=tools,
    )
    logger.info(
        "Created MCP toolkit %s (%s) with %d tools for %s",
        toolkit["id"], name, len(tools), request.node.name,
    )

    yield {
        "id": toolkit["id"],
        "name": name,
        "toolkit_name": toolkit.get("toolkit_name", name),
        "tools": [t["name"] for t in tools],
        "project_id": int(toolkit_api.project_id),  # ELITEA-2203: slash-mention menu-item testids need it
    }

    try:
        toolkit_api.delete_toolkit(toolkit["id"])
        logger.info("Deleted MCP toolkit %s", toolkit["id"])
    except Exception as exc:
        logger.warning("Failed to delete MCP toolkit %s: %s", toolkit["id"], exc)


@pytest.fixture
def mcp_pipeline_with_toolkits(
    mcp_toolkit_with_tools: dict, toolkit_api: ToolkitAPI, pipeline_api: PipelineAPI, request
):
    """Create a pipeline with an MCP node pre-configured with a Toolkit + Tool.

    Satisfies the ELITEA-1954 precondition: a pipeline with an MCP node
    already configured (Toolkit = a throwaway Context7 MCP, Tool =
    ``resolve-library-id``), with >=2 MCP toolkits attached in the pipeline's
    TOOLS section — both with real, non-empty, disjoint tool lists (the
    Context7 MCP created here, plus the DeepWiki ``mcp_toolkit_with_tools``
    fixture). Both toolkits are created and deleted by fixtures, so the
    precondition holds on any environment.

    Yields:
        dict: ``{"id": int, "name": str, "node_id": str, "toolkit_name": str,
        "tool": str, "other_toolkit_name": str, "other_tools": list[str]}``
        — the "other" fields describe the toolkit/tools the test switches TO.
    """
    from api.helpers import sync_mcp_tools_with_retry

    initial_name = f"autotest_mcp2_{request.node.name}"[:32]
    initial_tools = sync_mcp_tools_with_retry(
        toolkit_api,
        _MCP_CONTEXT7_URL,
        max_retries=3,
        initial_delay=5,
        timeout=60
    )
    assert initial_tools, f"mcp_sync_tools returned no tools for {_MCP_CONTEXT7_URL!r} — endpoint may be down"
    initial_tool_names = [t["name"] for t in initial_tools]
    assert not set(initial_tool_names) & set(mcp_toolkit_with_tools["tools"]), (
        f"Initial and switched-to MCPs must expose disjoint tools for the stale-leakage check, "
        f"got overlap {set(initial_tool_names) & set(mcp_toolkit_with_tools['tools'])!r}"
    )
    initial_tool = (
        _MCP_CONTEXT7_PREFERRED_TOOL if _MCP_CONTEXT7_PREFERRED_TOOL in initial_tool_names else initial_tool_names[0]
    )

    initial_toolkit = toolkit_api.create_remote_mcp_toolkit(
        name=initial_name,
        description=f"Auto-created MCP for test {request.node.name}",
        url=_MCP_CONTEXT7_URL,
        tools=initial_tools,
    )
    initial_toolkit_id = initial_toolkit["id"]
    initial_toolkit_name = initial_toolkit.get("toolkit_name", initial_name)
    logger.info(
        "Created MCP toolkit %s (%s) with %d tools for %s",
        initial_toolkit_id, initial_name, len(initial_tools), request.node.name,
    )

    pid = None
    try:
        initial_full = toolkit_api.get_toolkit(initial_toolkit_id)
        deepwiki_full = toolkit_api.get_toolkit(mcp_toolkit_with_tools["id"])

        name = f"autotest_pl_{request.node.name}"[:32]
        node_id = "MCP 1"
        pipeline = pipeline_api.create_pipeline_with_mcp_node(
            name=name,
            description=f"Auto-created MCP pipeline for test {request.node.name}",
            tools=[initial_full, deepwiki_full],
            toolkit_name=initial_toolkit_name,
            tool=initial_tool,
            node_id=node_id,
        )
        pid = pipeline["id"]
        logger.info("Created MCP pipeline %s (%s) for %s", pid, name, request.node.name)

        yield {
            "id": pid,
            "name": name,
            "node_id": node_id,
            "toolkit_name": initial_toolkit_name,
            "tool": initial_tool,
            "other_toolkit_name": mcp_toolkit_with_tools["toolkit_name"],
            "other_tools": mcp_toolkit_with_tools["tools"],
        }
    finally:
        if pid is not None:
            try:
                pipeline_api.delete_pipeline(pid)
                logger.info("Deleted MCP pipeline %s", pid)
            except Exception as exc:
                logger.warning("Failed to delete MCP pipeline %s: %s", pid, exc)
        try:
            toolkit_api.delete_toolkit(initial_toolkit_id)
            logger.info("Deleted MCP toolkit %s", initial_toolkit_id)
        except Exception as exc:
            logger.warning("Failed to delete MCP toolkit %s: %s", initial_toolkit_id, exc)


def _llm_node_dict(transition: str) -> dict:
    """Build the LLM 1 node dict shared by the canvas node/edge CRUD fixtures
    below (ELITEA-2018/2031/2032) — same shape confirmed live in the AFS
    exploration sessions for all three cases.

    Args:
        transition: The node's ``transition`` target (e.g. ``"Code 1"``,
            ``"Printer 1"``, ``"END"``).
    """
    return {
        "id": "LLM 1",
        "type": "llm",
        "input": [],
        "input_mapping": {
            "chat_history": {"type": "fixed", "value": []},
            "system": {"type": "fixed", "value": ""},
            "task": {"type": "fixed", "value": "hi"},
        },
        "output": ["messages"],
        "structured_output": False,
        "transition": transition,
    }


def build_delete_node_pipeline_nodes() -> list[dict]:
    """LLM 1 -> Code 1 -> END node list for ELITEA-2018 (Pipeline Canvas —
    Delete Node). Confirmed live (2026-08-03): produces exactly 3 nodes /
    2 edges on first canvas load, no manual UI wiring needed.
    """
    return [
        _llm_node_dict(transition="Code 1"),
        {
            "id": "Code 1",
            "type": "code",
            "input": [],
            "output": [],
            "code": "print('hi')",
            "transition": "END",
        },
    ]


@pytest.fixture
def pipeline_llm_code_end(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> Code 1 -> END`` (3 nodes, 2 edges) before
    the test and delete it afterwards. Satisfies the ELITEA-2018 precondition
    (see :func:`build_delete_node_pipeline_nodes`).

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_delnode_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created delete-node pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_delete_node_pipeline_nodes(),
    )
    pid = pipeline["id"]
    logger.info("Created delete-node pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted delete-node pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete delete-node pipeline %s: %s", pid, exc)


def _printer_node_dict(transition: str) -> dict:
    """Build the Printer 1 node dict shared by the edge-creation/-deletion
    fixtures below (ELITEA-2031/2032).

    Args:
        transition: The node's ``transition`` target (e.g. ``"END"``).
    """
    return {
        "id": "Printer 1",
        "type": "printer",
        "input_mapping": {"printer": {"type": "fixed", "value": "done"}},
        "transition": transition,
    }


def build_llm_printer_nodes(llm_transition: str) -> list[dict]:
    """Build an ``LLM 1`` + ``Printer 1`` node pair, parametrized on where
    ``LLM 1`` transitions to. Shared by the ELITEA-2031 (edge creation) and
    ELITEA-2032 (edge deletion) fixtures below — same node pair, differing
    only in whether LLM 1 already points at Printer 1.

    Args:
        llm_transition: ``LLM 1``'s ``transition`` value — ``"END"`` seeds
            two independently-terminating nodes (ELITEA-2031, so the edge
            under test doesn't pre-exist); ``"Printer 1"`` seeds the edge
            directly (ELITEA-2032, so the edge under test already exists).

    Returns:
        list[dict]: ``[LLM 1, Printer 1]`` node definitions.
    """
    return [
        _llm_node_dict(transition=llm_transition),
        _printer_node_dict(transition="END"),
    ]


@pytest.fixture
def pipeline_llm_printer_disconnected(pipeline_api: PipelineAPI, request):
    """Create a pipeline with ``LLM 1`` and ``Printer 1``, each independently
    ``transition: END`` (NOT connected to each other) before the test, and
    delete it afterwards. Satisfies the ELITEA-2031 precondition — omitting
    ``transition`` on both nodes entirely auto-defaults ``LLM 1`` to
    ``transition: Printer 1`` (the next node in the YAML list), which would
    pre-create the very edge this case tests the creation of; both must
    explicitly point at END.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_edgecreate_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created edge-creation pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_llm_printer_nodes(llm_transition="END"),
    )
    pid = pipeline["id"]
    logger.info("Created edge-creation pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted edge-creation pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete edge-creation pipeline %s: %s", pid, exc)


@pytest.fixture
def pipeline_llm_printer_connected(pipeline_api: PipelineAPI, request):
    """Create a pipeline ``LLM 1 -> Printer 1 -> END`` (the edge under test
    already exists) before the test, and delete it afterwards. Satisfies the
    ELITEA-2032 precondition.

    Yields:
        int: Numeric pipeline ID.
    """
    name = f"autotest_edgedelete_{request.node.name}"[:32]
    pipeline = pipeline_api.create_pipeline_with_nodes(
        name=name,
        description=f"Auto-created edge-deletion pipeline for test {request.node.name}",
        entry_point="LLM 1",
        nodes=build_llm_printer_nodes(llm_transition="Printer 1"),
    )
    pid = pipeline["id"]
    logger.info("Created edge-deletion pipeline %s (%s) for %s", pid, name, request.node.name)

    yield pid

    try:
        pipeline_api.delete_pipeline(pid)
        logger.info("Deleted edge-deletion pipeline %s", pid)
    except Exception as exc:
        logger.warning("Failed to delete edge-deletion pipeline %s: %s", pid, exc)

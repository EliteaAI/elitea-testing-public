---
name: Pipeline chat starters shares agent chip testid
description: Pipeline ChatPanel mounts the same ChatBox as AgentDetailPage — chat-conversation-starter-tile testid travels for free
type: project
---

ELITEA-2053 (Pipeline — Chat Starters) analysis, 2026-08-09.

`src/pages/Pipelines/Components/ChatPanel.jsx` (pipeline's embedded, right-side
chat panel) mounts the **exact same shared `ChatBox` component**
(`@/[fsd]/features/chat/ui`) that `AgentDetailPage`'s embedded chat mounts. Both
render `ChatConversationStarters.jsx` at the identical call site. This means the
`chat-conversation-starter-tile` testid ELITEA-1886 added to that call site
(EliteaAI/EliteaUI@afb48435, on `automation/testids` only as of this session —
still not on `origin/main`) **already applies to the pipeline surface with zero
extra `add-data-testid` work** — confirmed live via `browser_run_code_unsafe`
(count==1, exact text match) on a fresh pipeline detail page.

Same free-ride pattern as ELITEA-2052 found for `chat-message-list`/
`skill-test-last-response`/welcome-message seeding: the pipeline's embedded chat
and the agent's embedded chat are the SAME React component tree, just mounted
from two different page routes/page objects (`PipelineDetailPage` vs
`AgentDetailPage`, no shared ancestor besides `BasePage`). Before assuming a
pipeline-chat-panel element needs a fresh testid, check whether the Agent
surface's equivalent page object already has the field — if so, it's a
page-object-only addition (duplicate the `LocatorDescriptor`/class-constant
shape on `PipelineDetailPage`), not implementer `add-data-testid` work.

The "Chat starters" LEFT-PANEL section (`ConversationStarters.jsx`, the
add/edit form, distinct from the chat-panel CHIP above) is also a literally
shared component between `PipelineConfigurationForm.jsx` and
`ApplicationConfigurationForm.jsx` — all its testids carry the `agent-` prefix
despite being used on both surfaces (pre-existing tech debt, not a new
violation to fix opportunistically). One real gap found: the "delete starter"
button in that shared component has `aria-label="delete starter"` but NO
testid anywhere (`main` or `automation/testids`) — first case to need it is
ELITEA-2053's step 3.

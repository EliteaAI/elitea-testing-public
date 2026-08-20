---
name: Pipeline creation from chat fires async participant-add POST
description: Creating a pipeline via chat's + menu synchronously queues a second POST (add PIPELINES participant) that can resolve after the create response returns
type: reference
---

Source-traced (`EliteaUI/src/hooks/chat/usePipelineCreation.js`): the in-chat
"+ Create New Pipeline" canvas's create-mode Save success handler
(`onPipelineCreated`) unconditionally calls `addNewParticipants([pipelineParticipant])`
right after the pipeline-creation `201` resolves. That fires a SECOND POST —
`POST /api/v2/elitea_core/participants/prompt_lib/{projectId}/{conversationId}`
(`chat.api.js`'s `addParticipantIntoConversation` mutation) — adding the new
pipeline onto the conversation as a `PIPELINES` participant.

**Why it matters for a "zero network call" assertion downstream of Setup:**
this second POST is queued synchronously but its own response can resolve
*after* your Setup block's own `page.expect_response()` for the create call
has already returned — i.e. it races into whatever comes next. ELITEA-2078's
fix-round-1 hit this directly: a `write_requests` log cleared right after the
create-response assert still picked up the participant-add POST several
steps later, producing a false "network call fired during Discard" failure.

**Fix pattern:** await BOTH responses in one nested `page.expect_response(...)`
block around the Save click:
```python
with page.expect_response(create_predicate) as create_resp_info, \
     page.expect_response(participant_predicate) as add_participant_resp_info:
    pipeline_detail.save_button.click()
create_response = create_resp_info.value
add_participant_response = add_participant_resp_info.value  # settle it too
```
Then start any "zero further network calls" observation window (write-request
log clear, etc.) only after both are settled. Same mechanism as ELITEA-2076's
own AFS note about "no PIPELINES participant added" when Discard fires
*before* ever saving (create-mode discard) — in a case where Setup DOES save
first, the participant-add is Setup's own expected traffic, not a defect.

Relevant to any case whose Setup/Preconditions replicates the "+ Create New
Pipeline" flow and then asserts something about network quiescence in a later
step (ELITEA-2076/2077/2078/2079's shared precondition family).

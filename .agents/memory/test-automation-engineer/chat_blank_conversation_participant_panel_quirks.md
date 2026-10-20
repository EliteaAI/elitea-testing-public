---
name: chat blank conversation participant panel quirks
description: Blank-chat plus-menu participants: attention-card MCP has no row testid, no messages_list, no placeholder text
type: reference
---

In a brand-new unsent chat on DEV: `chat-message-list` is not rendered (close the plus popper via `ChatPage.close_plus_menu_popper_on_blank_chat`), "Type your message..." is absent from the DOM, and a disconnected remote MCP participant is an attention card (parent of `chat-participant-warning-icon`, found via `ChatPage.get_participant_attention_card(name)`) with no `chat-participant-row-*` testid, name resolved only after first Send. `agent_id`/`pipeline_id` fixtures share one name; create distinct ones when matching rows by text. Without `automation/.env.test` export `APP_PREFIX=/app`.

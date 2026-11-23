---
name: Agent modules Attachments row click and chat attach icon
description: Attachments module row centre-click doesn't toggle; agent chat attach icon is chat-attach-button gated by saved internal_tools
type: reference
---

On agent detail, `agent-module-menu-item-attachments` toggles only with a click at a left offset (e.g. position x=40,y=10) or Space; centre click lands on the (i) tooltip. The Test Agent panel's attach icon is `chat-attach-button` (disabled unless the SAVED version has `attachments` in internal_tools); OFF + drop gives toast "Attachments are not allowed." (ELITEA-4791). Details: test-specs/agents/_surface.md.

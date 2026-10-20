---
name: Chat export is encrypted on DEV
description: Conversation export downloads .json.enc (AES-256-GCM, server key); content cases (ELITEA-3775 family) are unobservable
type: project
---
Export via menu -> modal -> `export-chat-modal-export-button` yields `*.json.enc` (header `ELITEA-CHAT-ENC/1`),
API `conversation_export/prompt_lib/{pid}/{cid}` ignores encrypt=false. Any export-content case (message count,
order, JSON fields) is blocked unless a key/flag is supplied; round-trip via Import is the only content-level route.
Check this first for any sibling export-JSON cases in the chat-json-export batch.

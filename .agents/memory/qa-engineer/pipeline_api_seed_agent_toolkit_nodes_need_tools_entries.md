---
name: pipeline API seed of Agent/Toolkit nodes needs tools[] entries
description: create_pipeline_with_nodes with agent/toolkit nodes shows "not found" in panel unless version tools[] holds the toolkit object and an application entry
type: reference
---

Seeding `Agent`/`Toolkit` nodes via `pipeline_api.create_pipeline_with_nodes` renders "Agent not found / Toolkit not found — select a replacement" in the node panel unless `tools=[full toolkit obj (toolkit_api.get_toolkit), {"type":"application","name":<agent name>,"description":"d","settings":{"application_id":id,"application_version_id":versions[0].id}}]`. Toolkit node `toolkit_name` = `get_toolkit()["toolkit_name"]`. Node rename (panel Name) commits on Enter/blur; Save stays enabled when the name is invalid. Confirmed ELITEA-4715, 2026-11-18.

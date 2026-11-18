---
name: pipeline_node_yaml_panel_quirks
description: Pipeline node-panel YAML tab (ELITEA-4716/4717) automation gotchas - canvas edge drag, CodeMirror edits, Save state
type: reference
---

- Node YAML tab handles live in `PipelineDetailPage` (`node_yaml_*`, `set_node_yaml_line`, `replace_node_yaml_text`); CodeMirror needs click + `insert_text`.
- Node YAML is a one-item list (`- id: X`); page Yaml block = same lines indented by 2 more.
- Canvas drag of a NEW edge from a node that already has a transition is impossible: the 16px output handle is covered by `.react-flow__edgeupdater-source`; dragging the edge target end (reconnect) does not update the YAML transition (`onReconnect` only reconnects the edge). Leave step 8 of ELITEA-4716 unautomated.
- Save is enabled only when the pipeline is dirty; invalid node-YAML drafts never disable it.
- `connect_nodes` fails ("not hittable") on a configured LLM card; `.env.test` may be absent -> export `APP_PREFIX=/app`.

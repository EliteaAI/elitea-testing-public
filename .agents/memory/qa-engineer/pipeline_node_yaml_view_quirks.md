---
name: Pipeline node YAML view quirks
description: Node-panel YAML tab handles, errors, save-state drift, sandbox APP_PREFIX gotcha
type: reference
---

See test-specs/pipelines/_surface.md § Node panel YAML view. Key: Save is never disabled by a node-YAML error (only dirtiness); node YAML is a list item; appended keys need 2-space indent; sandbox lacks .env.test so export APP_PREFIX=/app (else DEV shows 404) and use `--reruns 0`; `connect_nodes` fails "not hittable" with the node panel/layout state.

---
name: MCP node toolkit picker lists all project MCPs (EL-7159)
description: Pipeline MCP/toolkit node pickers are ProjectToolkitPicker popovers listing every project MCP; assert inclusion + TOOLS-panel Used-by, never exact equality
type: project
---
Since EL-7159 the pipeline MCP node's Toolkit control is a popover picker (rows `pipeline-mcp-node-toolkit-select-option`, search `...-menu-search`) that lists EVERY project MCP, not just those attached in TOOLS. "Exactly the attached MCPs" assertions are unachievable; human ruling on #2858: assert inclusion and verify against the TOOLS card (`pipeline-tool-card-used-by` = node id, Show tools lists the configured tool). Container lacks automation/.env.test: run pytest with `APP_PREFIX=/app` or pipeline URLs 404 (looks like a timeout in wait_for_detail_page_load).

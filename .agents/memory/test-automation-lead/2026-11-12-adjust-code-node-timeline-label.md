# 2026-11-12 adjust-code-node-timeline-label (#2926)
- 4 Code-node specs now assert timeline label `endswith(<node id without spaces>)`; pyodide label was removed by EliteaUI#1406.
- Gotcha: factory container has no automation/.env.test; export APP_PREFIX=/app before pytest, else /pipelines/all/<id> shows the app's 404 page. I filed #2935 on that false alarm and a human (not me) spotted it first-hand cause only after I re-ran. Check env before filing a 404 bug.
- Browser MCP unavailable in container (no Chrome); use playwright python with -I and storage state for probes.

---
name: Vite dev server serves stale modules on OneDrive
description: New testids appear absent in the browser because Vite's fs-watch never fires on this OneDrive checkout — restart the server
type: project
aliases: [stale testid, testid not found, HMR not working, vite cache, dev server stale]
tags: [area/ui-automation, type/gotcha]
created: 2026-08-22
updated: 2026-08-22
---

## Symptom

A `data-testid` just added to `EliteaUI/src` (or `../elitea_assistant/src`) is correct on disk, but
`get_by_test_id(...)` times out and `document.querySelector('[data-testid=...]')` returns null in the
live page. HMR appears to have done nothing — and a full page reload does not help either.

## Cause

The repos sit on OneDrive. Vite's file watcher does not fire reliably there, so the dev server keeps
serving its cached transform of the pre-edit module. This is NOT a MUI prop-forwarding problem and NOT
a wrong testid name.

## Diagnose (one curl, no browser)

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/widgets/sidebar-root/ui/SidebarBody.jsx" | grep -c "<testid>"
# connected repo (aliased via VITE_ASSISTANT_LOCAL=1) is served under /@fs<abs-path>:
curl -s "http://localhost:5173/@fs/<abs>/elitea_assistant/src/components/chat/MessageInput.tsx" | grep -c "<testid>"
```

`0` ⇒ the server is stale; the JSX on disk is fine.

## Fix

```bash
pkill -f "npm run dev"; pkill -f "EliteaUI/node_modules/.bin/vite"
rm -rf ../EliteaUI/node_modules/.vite
cd ../EliteaUI && nohup npm run dev > /tmp/elitea-ui-dev.log 2>&1 &
# wait ~25s, then re-curl — expect 1
```

Always re-curl before re-running the spec: it costs one second and saves a full test rerun.

Related: [[support_assistant_launcher_click_quirk]]

---
name: Vite can serve a STALE transform of a just-edited testid file
description: A newly added data-testid that "doesn't render" is often the dev server, not the component — curl the module before debugging the test
type: feedback
aliases: [stale vite transform, testid not found after add, HMR missed the change, dev server stale module]
tags: [area/eliteaui, type/environment]
created: 2026-08-30
updated: 2026-08-30
---

## What happened

ELITEA-2245: added `data-testid="project-general-edit-icon-button"` to
`ProjectParamsHeader.jsx` on `automation/testids`, committed + pushed, dev server
already running. The spec failed `to_be_visible` on it. The element WAS in the DOM
(an `IconButton` with `data-testid: null`) — i.e. the browser was executing the
pre-edit module.

`touch`ing the file did **not** invalidate it. **Restarting `npm run dev` did.**

Two plausible causes, both present here: the tree lives on OneDrive (unreliable
fs events), and the source uses bracketed `[fsd]` directory names.

## The 5-second check, before debugging anything else

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/<path-to-component>.jsx" | grep -c "<your-testid>"
```

`0` ⇒ the dev server is stale; restart it. Non-zero ⇒ the testid really isn't
rendering, so go look at its render condition (a permission gate, a state branch).

⚠️ Do NOT grep with an alternation like `grep -c "my-testid\|EditIcon"` — the
second term matches and you will "confirm" the testid is served when it is not.
That mistake cost the extra rerun here.

## Cost

One full spec rerun plus a live browser investigation, for a one-command check.

Related: [[accordion_container_testid_to_be_enabled_is_vacuous]]

---
name: Support Assistant automation campaign (#1400)
description: How the support-assistant area got to 17/17 — waves, gates, the connected-repo two-hop promotion, and the shared-user pollution trap
type: project
aliases: [support assistant, elitea_assistant, connected repo testids, widget automation, 1400]
tags: [area/support-assistant, type/campaign]
created: 2026-08-22
updated: 2026-08-22
---

## Outcome

Area closed 2026-08-22: all 17 TMS support-assistant cases automated. This card
delivered 11 in two waves — w01 PR #1651 (ELITEA-2418/2419/2422/2423, plus
ELITEA-1797 already-covered), w02 PR #1665 (2420/2424/2425/2426 automated;
2421/2427 merged sanctioned-RED on #1653 / #1658+#1659).

## The connected repo is the load-bearing detail

`elitea_assistant` had **zero** `data-testid` attributes before this campaign.
All widget handles now live on ITS `automation/testids` branch, and promotion is
**two hops, not one**:

1. a human cherry-picks to `elitea_assistant` `main`, **then**
2. **EliteaUI must bump the `@eliteaai/elitea-assistant` git-dependency.**

Miss step 2 and the testids never reach a deployed env no matter what lands on
the assistant's main. Say this explicitly in every closure record for this surface.

## Traps that cost real time

- **Shared-test-user pollution (#1082 class).** Every support-assistant spec sends
  real messages as the same user and none tear down. Long invocations make later
  specs read counts earlier specs moved. A blast-radius run went red on exactly
  this and was NOT a regression — proved with 3 controls (specs alone on the
  trunk; same set on base; same set repeated). Always run the controls before
  believing a red blast radius here.
- **Every observable is a DELTA.** The widget restores the prior conversation on
  open, so absolute `to_have_count(n)` false-fails. Baseline then compare.
- **Reply latency 33–135s**, and `AI_RESPONSE_TIMEOUT = 120_000` is tight.
  A 6-spec gate run takes ~12 min — exceeds the 600s foreground Bash cap, so
  launch it detached and poll the log.
- **No token streaming.** `AnimatedMessage.tsx` is a CSS reveal of complete text.
  ELITEA-2426 was made automatable by asserting exactly ONE `support_predict`
  WebSocket frame across the expand, not by faking a stream.
- **Vite does not hot-reload under OneDrive** — fs-watch never fires, so a fresh
  testid is on disk but the server serves the pre-edit module. Reproduced 3×.
  Diagnose: `curl -s http://localhost:5173/src/<path> | grep -c <testid>`.

Related: [[synthetic_input_events_produce_false_bugs]]

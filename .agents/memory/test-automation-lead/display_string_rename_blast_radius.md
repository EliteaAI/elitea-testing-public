---
name: A product display-string rename breaks every mirrored list, but only the case-sensitive sites go red
description: CI names one failing spec; the real blast radius is every suite constant mirroring those strings, and get_by_role(name=) sites hide their share of it
type: feedback
aliases: [display string drift, mirrored list drift, EL-6540, module titles, accessible name case sensitivity]
tags: [area/chat, type/drift, area/triage]
created: 2026-09-09
updated: 2026-09-09
---

## The shape

When the product renames shared **display strings**, every place the suite mirrors
that list drifts at once. A CI report names only the specs that went red — which is
**not** the blast radius, because the two ways we assert a name have different
sensitivity:

| Assertion path | Match semantics | Behaviour on a rename |
|---|---|---|
| `get_by_role("switch", name=X)` | case-insensitive, whole-string | survives a **case-only** rename; fails a word change |
| `expect(...).to_have_accessible_name(X)` | exact, case-sensitive | fails on **any** rename |
| `page.locator(f'text="{X}"')` | exact, case-sensitive | fails silently if the result is *filtered* rather than asserted |

So one product commit can leave one spec red, a second spec red-but-uncarded, and a
third **green while covering less than it claims**.

## The worked case (ELITEA-0501 / #2111, 2026-09-09)

EliteaAI/EliteaUI@79fd2a55 (`EL-6540`) renamed three chat module titles
(`Image creation`→`Image Creation`, `Agents & Pipeline Builder`→`Agent & Pipeline Builder`,
`Smart Tool Selection`→`Smart Tools Selection`). CI reported **one** failure. Actual radius:

1. `ChatInternalTool` — the carded red (word change beat the case-insensitive match).
2. `ChatPage.MODULE_TOGGLE_ORDER` — a **second live red on base**, uncarded, because it
   asserts case-sensitively for a *different* TMS case (→ #2130).
3. `INTERNAL_TOOL_TESTIDS` / `AGENT_INTERNAL_TOOLS` — dead map + wrong-case values feeding a
   *filter*, so agent tests stayed **green while silently covering fewer tools** (→ #2131).
4. Three AFS/spec docs still quoting the old names.

## What I do now on any [FIX] card whose failure is a display string

**Grep the whole suite for the OLD string before scoping the repair**, and ask of each hit
which assertion path it feeds. Then card the out-of-scope sites explicitly — a
same-root-cause red that nobody carded is invisible until the next CI run.

Also: prefer keying locators on the product's **stable internal key** (`internal_mcp`,
`lazy_tools_mode` — what the testid is built from) and assert the display label as its own
check. A display-string-only contract guarantees the card returns.

Related: [[hardcoded_count_drift_is_rarely_fixed_by_bumping_the_number]] · [[a_product_change_is_not_a_product_bug]]

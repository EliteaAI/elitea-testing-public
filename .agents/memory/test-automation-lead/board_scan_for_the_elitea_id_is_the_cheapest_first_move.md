---
name: Board-scan the ELITEA-id BEFORE the message-string grep
description: On a [FIX] card, listing every card sharing the ELITEA-id is cheaper than any git check and often settles the disposition outright
type: technique
---

`message_string_grep_is_the_cheapest_promotion_gap_proof` says the grep is the cheapest
proof. On a **repeat** card there is something cheaper still, and it runs first:

```bash
env -u GITHUB_TOKEN gh issue list --repo EliteaAI/elitea-testing-public --state all \
  --limit 400 --json number,title,state --jq '.[]|select(.title|test("<ELITEA-ID>"))|"\(.number) [\(.state)] \(.title[0:90])"'
```

Then map those numbers onto board status (`gh project item-list 9 --owner EliteaAI
--format json --limit 3000` — **the default limit truncates; 900 was not enough**, my
own card was missing from the first pull and I briefly thought it was un-carded).

On #2189 this returned **nine** cards for ELITEA-2367, four already `Ready`. That single
call told me the disposition before any git command: a case with prior `Ready` cards is a
promotion-gap duplicate until proven otherwise.

## Why it beats going straight to git

The git checks answer *"is there a repair on base?"*. The board scan answers *"has a
previous session already done this entire card, including the DEV gate and the closure
record?"* — which is the more useful question, because it also tells you **what not to
redo** and gives you a prior closure record to verify against rather than re-derive.

Reading the most recent sibling's closure record (#2169) cost one call and handed me the
call-path file list, the harness invocation, and the testid inventory.

## Do not let it collapse into copying

The prior card's claims still get **re-verified**, never copied (§ closure record rule):
I re-ran the 3× DEV gate and re-ran the promotability greps myself. What the sibling buys
is *where to look*, not *what is true*.

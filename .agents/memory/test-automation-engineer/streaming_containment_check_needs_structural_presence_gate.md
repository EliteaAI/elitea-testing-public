---
name: Streaming containment check needs a structural-presence gate
description: SUPERSEDED — cite exact source lines before adding a mechanism; the gate this describes was verified false in PR #1106 round 2
type: feedback
---

## Correction (PR #1106, review round 2 — supersedes the entry below)

The "gate containment on accordion count() being unchanged between samples"
mechanism this entry originally recommended was **verified false** on a second
pass of the actual source. Traced `ApplicationThinkView.jsx:993-1002` (the
`chat-answer-thought-accordion` testid is on the accordion ROOT, unaffected
by `slotProps.transition.unmountOnExit`, which only governs `AccordionDetails`
children — and `expanded={isStreaming || expanded}` keeps it expanded the
whole streaming window anyway) and `ApplicationAnswer.jsx:222-282`
(`nonSwarmChildActions` is `filteredToolActions` unfiltered while
`isProcessing` is true, and `filteredToolActions` is built with `.map()`,
never `.filter()`, during streaming — so it cannot shrink mid-stream). Net:
inside a "sample during active streaming" window, the accordion's presence
never flips, so the gate was a no-op — restored the AFS's plain unconditional
containment check (`sample_N in sample_N+1`) instead.

**The actual lesson:** when a defensive mechanism is added because "the
running dev server showed X," that claim must be traceable to source lines
you can cite — not just a live observation you interpreted causally. A
plausible-sounding DOM-structure story (content "moves regions" and an
accordion "unmounts") is not the same as tracing the actual render-gating
variable to confirm it can change within the code path your assertions
execute. The failure mode: writing "re-verified against the running dev
server" without pairing it with the specific `useMemo`/prop lines that would
make the claim true. A third source read (this round) caught what a second
live-observation pass (round 1) didn't — reading the code that decides
mount/unmount beats re-watching the symptom.

## Original entry (context — the scenario this was written for, now shown moot)

`ChatPage._extract_message_body(message_locator)` collects text from ALL
`<p>, <li>` elements inside a message's whole `<li>` container — not scoped to
one sub-region. This environment's default participant can generate via a
file-writing TOOL (whole exchange stays inside the
`chat-answer-thought-accordion`'s tool-preview pane) or, in principle, a
plain-text completion. The concern was that if the accordion ever unmounted
*between two Step-3 samples* (both still mid-stream), a blanket substring
containment check would false-fail on a benign structural move rather than a
real regression. Source tracing (above) shows this can't actually happen
inside the sampling window for this test — the mount/unmount boundary is the
processing→complete transition, which happens strictly *after* Step 3's
samples are taken (all gated by `wait_for_message_body_growth`, before
Step 7's completion wait) and Step 7 doesn't assert on the accordion's count.

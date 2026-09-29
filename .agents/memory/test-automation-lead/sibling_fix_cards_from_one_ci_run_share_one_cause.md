---
name: Sibling [FIX] cards from one CI run usually share one product commit
description: Read the other [FIX] cards from the same CI run before triaging yours — one product commit fans out into several, and a traced cause transfers verbatim
type: feedback
aliases: [sibling fix cards, same CI run, one commit many cards, FIX card triage order, EL-6687, 471b753c, open_file_in_editor]
tags: [area/triage, area/artifacts, type/lesson]
created: 2026-09-29
updated: 2026-09-29
---

## Rules

1. **Before triaging a `[FIX]` card, read the sibling `[FIX]` cards filed from the
   same CI run.** A nightly runs `main`, so ONE product commit takes down every
   spec that touches the changed component — and the cards land separately, each
   naming a different test and a different (usually wrong) subsystem. Lived
   2026-09-29: EliteaAI/EliteaUI@`471b753c` ("fix: [EL-6687] Fixed Artifacts
   section UI issues", 2026-09-23, **empty commit body**) produced **#2377**
   (`ArtifactTableToolbar.jsx` — toolbar wrapped in `{!isEmptyFiles && (`) and
   **#2376** (`PreviewHeader.jsx:215` — Save/Discard gate changed from
   `{canPreview && (` to `{canPreview && !isImageFileType && (`) from run #197.
   The second card cost ~1 hour instead of a full hypothesis cycle purely because
   the first card's thread already named the commit. Cheapest possible first move:
   `gh issue list --label … --state all` for cards filed the same day, then read
   their threads.

2. **A shared page-object "is it open?" signal mislocates the failure.** The red
   fires where the signal waits, not where the stale assertion lives.
   `artifacts_page.py open_file_in_editor()` treats
   `artifacts-preview-save-button` becoming visible as "the editor opened", so
   after EL-6687 an image file dies at **Steps 3-4** (`Locator.wait_for` →
   `broken`) while the assertion that actually became wrong is **Step 6**
   ("present and BOTH DISABLED"). Expect the intake card to name the wrong
   subsystem, and expect the repair to be wider than the spec: every image-file
   caller of that method needs a new anchor. Unconditional survivors on that
   header: `artifacts-preview-close-button`, `artifacts-preview-file-path`.

3. **When the repair flips an assertion's MEANING, it is a human decision — file a
   `question`, do not declare your way past it.** "Present but disabled" →
   "structurally absent" changes *what the case verifies*, which the
   declared-improvisation ceiling reserves for a human; the TMS case text usually
   needs amending too; and an empty commit body means intent is **inferred**, not
   stated. Give both options + a recommendation and park `Blocked`. (#2380 for
   ELITEA-1862; sibling #1693 is the same family on the Preview-Not-Available
   panel — answer such families consistently.)

4. **Check the sibling cards' dedup surface too.** Three planned question cards
   collapsed to one because a 400-issue real-time `gh issue list` (never
   `--search`) showed two findings already filed (#2096/#2071 locator-instruction
   conflict, #1938 PR-base conflict) and the environment blocker already carried
   by #2378. A real duplicate found BEFORE filing is a comment on the existing
   issue, not a new card — and corroborating a sibling's open question with
   independent evidence from a different spec is worth more than a fresh card.

Related: [[dev_drift_red_diff_main_before_grepping_testids]] · [[ui_drift_bracket_by_pass_fail_dates]]

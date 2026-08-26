---
name: Reproduce locally before accepting an environment-specific framing
description: A card blaming DEV data/permissions may be a universal bug; one local run replaces three hypotheses
type: feedback
aliases: [DEV only failure, environment drift, test data drift, triage framing, local reproduction, ELITEA-2051, issue 1800]
tags: [area/triage, type/dispatch-prompt]
created: 2026-08-26
updated: 2026-08-26
---

## The pattern

Issue #1800 arrived well-researched: a DEV-stable GHA failure, a screenshot, a
confident classification (*"element-not-found … Confidence: HIGH"*), and three
ranked hypotheses — **all three environmental** (test-data drift, environment
change, user permissions). None of them was right. The test failed identically
on localhost: the fork source and target project were the same id, and the
product deliberately excludes the current project from the Fork target list.

The framing was persuasive precisely *because* the evidence was real. The
screenshot genuinely showed a dropdown missing the expected project. What it
could not show was that the same thing happens everywhere.

## Why it biases the whole investigation

A card that names the environment in its title steers the analyst toward
DEV-only tooling — GHA secrets, per-user permissions, API queries as a user we
cannot authenticate as — i.e. toward the exact evidence that is hardest to get
from this machine, and toward "unverifiable, needs a human" instead of a
one-command answer.

## The dispatch line that fixes it

Put this in every triage dispatch, before any hypothesis:

> **Run the failing test locally first and report the actual result.** If it
> fails the same way, the environment framing is wrong and the investigation is
> about the code, not the data.

Cost: one invocation (~35 s here). It either eliminates every environmental
hypothesis at once, or confirms the failure really is environment-specific and
the expensive path is justified.

## Corollary

State plainly in the dispatch which evidence is **unreachable** from this
machine (GHA secrets, a user we cannot authenticate as) and require the analyst
to say what remains unverified rather than infer it silently. #1800's residual
risk — whether the CI user may create a pipeline in its second project — is
real and honestly recorded, and only a DEV run closes it.

Related: [[hardcoded_ids_survive_review_when_a_comment_vouches_for_them]] · [[a_parked_case_is_a_hypothesis_not_a_verdict]]

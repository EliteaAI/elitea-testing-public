---
name: MUI Dialog unmount verifies mount-time-prop claims
description: how to independently check a "this prop is fixed at mount, not per-render" declared-improvisation reasoning for a state-conditional testid fix, using MUI Dialog's default unmount-on-close behavior
type: feedback
---

Seen on PR #571/ELITEA-1893 R2 review: implementer replaced a state-conditional
`data-testid={isForking ? 'a' : 'b'}` with one unconditional testid, justifying
it as "isForking is a mount-time prop, not runtime-toggled state on an
already-mounted node — each context (Fork vs Import) only ever encounters this
dialog in its own single context."

Don't take that claim on faith — it's checkable in ~2 minutes:

1. Find the `<Dialog open={...}>` (or equivalent MUI/framework modal) wrapping
   the component in question.
2. Check for a `keepMounted` prop (or the framework's equivalent). Absent (the
   default) means children are NOT rendered/mounted while `open === false` —
   MUI's `Modal` internals skip rendering `children` entirely in that state
   (no DOM node), so a closed→reopen cycle is a real unmount+remount, not a
   prop update on a live instance.
3. Trace where the conditional prop's *source* value changes (here:
   `state.importWizard.isForking` in a Redux slice, read once at
   `MainSidebar.jsx`). If the modal must close before that source value can
   change again (i.e. you can't flip Import→Fork mode while the dialog stays
   open), the "mount-time not per-render" framing holds — the component
   never observes its own prop changing mid-life.

This generalizes beyond this one PR: any "we removed a state-conditional
testid because the state is actually fixed per-mount" claim in a review
should be checked this way (no `keepMounted` + trace the state source) rather
than accepted from the PR narrative alone.

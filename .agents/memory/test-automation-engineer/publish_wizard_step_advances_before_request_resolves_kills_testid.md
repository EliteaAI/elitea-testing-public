---
name: Publish wizard step advances before request resolves, kills testid
description: PublishWizardModal Publish button loses its testid the moment publish_skill/publish is rejected — usePublishSkill/usePublishVersion hooks.js advance `step` before the request resolves
type: feedback
---

## What happens

`PublishWizardModal.jsx` (shared by Agent + Skill Publish flows,
`src/[fsd]/entities/version/ui/`) renders the "Publish" button with testid
`agent-publish-confirm-button` ONLY when `step === PUBLISH_STEPS.VALIDATION`.
Both `usePublishSkill.hooks.js` and (very likely, unverified) the agent
equivalent's `handlePublish()` unconditionally call `setStep(PUBLISH_STEPS.PUBLISHING)`
**before** awaiting the `publish`/`publish_skill` mutation result — so the
instant you click Publish, `step` becomes `PUBLISHING`, regardless of whether
the request ultimately succeeds or fails.

On a REJECTED publish (e.g. `validation_token_invalid` — stale/expired
token), the modal then renders a **second, separate JSX node** for the
`PUBLISHING && publishError` branch — a hard-`disabled` Button with (until
ELITEA-2597) **no testid at all**. So `is_enabled()`-style assertions against
`agent-publish-confirm-button` time out post-rejection: the element the
Validation step used is simply gone, replaced by an untestid'd twin.

## Fix

Added `data-testid="agent-publish-confirm-button"` to the SECOND branch too
(`EliteaAI/EliteaUI@c9c1f29e`) — same testid on two mutually-exclusive JSX
blocks (never both mounted, since `step` is one value at a time). This is the
canon-#277 "same-element conditional pair" pattern applied across two
separate `{cond && <X/>}` blocks instead of one ternary — declare it as an
improvisation in the LocatorDescriptor docstring when you do this.

## When this bites you

Any test asserting Publish-button DISABLED state (or presence at all) AFTER
a publish attempt that can fail — not just ELITEA-2597's stale-token case.
If a NEW publish-failure-mode test starts on Agent's Publish wizard, check
whether `AgentDetailPage.publish_confirm_button` needs the same treatment —
it wasn't touched by this fix (Skill-only PR), and the underlying
`PublishWizardModal.jsx` is shared, so the bug is very likely present there
too, just never exercised by an existing agent test.

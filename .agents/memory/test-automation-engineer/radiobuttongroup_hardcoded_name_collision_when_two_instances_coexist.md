---
name: RadioButtonGroup hardcoded name collision when two instances coexist
description: Shared Checkbox.RadioButtonGroup hardcodes native input name="radio-buttons-group" — two instances on one page break each other's native checked state even though testids/CSS are correct
type: feedback
---

## What happened (ELITEA-2006, issue #2411, 2026-10-07)

`test_pipeline_webhook_trigger_settings_modal.py` failed at Step 4
(`get_selected_webhook_type() == "gitlab"` → `None == 'gitlab'`), reproduced
locally too (not CI-only — ruled out class D immediately).

Live DOM evidence (Playwright, direct `.evaluate("e => e.checked")` on every
`input[name="radio-buttons-group"]` on the page after selecting GitLab):

```
radio[0] value='github'        checked_prop=False
radio[1] value='gitlab'        checked_prop=False
radio[2] value='custom'        checked_prop=False
radio[3] value='secret_token'  checked_prop=True
radio[4] value='signing_token' checked_prop=False
```

Root cause: `EliteaUI/src/[fsd]/shared/ui/checkbox/RadioButtonGroup.jsx` line 25
hardcodes `name="radio-buttons-group"` on the native `<input>` for **every**
instance of the component — it's not derived from the `testId` prop or any
per-instance key. `PipelineWebhookModal.jsx` renders the "Webhook Type" group
AND, only when `selectedWebhookType === "gitlab"`, a second "Authentication"
group (`secret_token`/`signing_token`) — both instances, so now 5 native
`<input type="radio">` elements share one `name`. The browser's native
"only one checked per name" semantics then apply ACROSS both logical groups:
the Authentication group's default-checked `secret_token` radio steals the
native checked state from every other radio sharing that name, including the
just-selected GitLab radio.

**The visual/React state is NOT wrong** — `Mui-checked` CSS class is on the
right wrapper, the webhook URL and description both correctly show
`.../gitlab` and the GitLab text. Only the native `<input>` `.checked`
IDL property (what `Locator.is_checked()` and `:checked` CSS/ARIA actually
read) is broken. This is why screenshots look completely correct while the
assertion fails — don't let a correct-looking screenshot talk you out of
checking the raw DOM property.

Classified **class B (new product bug)** — confirmed via source read, not
present in the original AFS (ELITEA-2006 AFS predates the Authentication
section entirely — it was added later and never re-verified against the
older webhook-type-only flow). No existing `bug` issue in this repo covered
it (`gh issue list --label bug` returned 0 for this repo at the time).
Reported to the lead for filing; test left untouched (no assertion weakening,
per the no-masking rule) since class B instructs "do NOT adjust."

## Why this is worth remembering

`RadioButtonGroup` is reused elsewhere (`MaxTokensSection.jsx`,
`HumanScoreControl.jsx`, `ToolSection.jsx`). Any page/modal that renders **two
instances of it simultaneously** is exposed to the same collision — it's a
component-level bug, not specific to the webhook modal. If a radio-group
assertion fails with a visually-correct screenshot elsewhere in the suite,
dump every `input[name="radio-buttons-group"]`'s `.checked` property before
assuming it's a locator/testid problem — that's the fastest way to confirm or
rule out this exact class of defect.

---
name: SecretField Secret/Password toggle testids exist only on automation/testids
description: toolkit-field-<k>-input-toggle-secret/-password come from Toggle.jsx testIdPrefix (EL-1967) which is NOT on EliteaUI main — verify by grepping the TEMPLATE, not the composed testid
type: reference
aliases: [secret view toggler testid, testIdPrefix, Toggle.jsx, toggle-secret, toggle-password, ELITEA-1932 provenance]
tags: [area/toolkits, area/credentials, type/quirk]
created: 2026-08-24
updated: 2026-08-24
---

## The fact (verified 2026-08-24, after `git fetch origin` in ../EliteaUI)

`toolkit-field-client_secret-input-toggle-secret` / `-toggle-password` (and the same pair on
every SECRET schema field, credentials included) are emitted by
`src/components/Toggle.jsx` from a `testIdPrefix` prop that `SecretField.jsx` passes as
``${inputProps['data-testid']}-toggle``.

**That wiring exists ONLY on `origin/automation/testids`** — added by
EliteaAI/EliteaUI@5892ae48 (`test: [EL-1967] add credential-form test-connection, enum-select
and secret-toggle testids`). On `origin/main`, `src/components/Toggle.jsx` carries **no testids
at all** and `testIdPrefix` appears nowhere outside `flow-editor/`. Any case whose test clicks
that toggle is therefore **not deployed-env-promotable** until a human cherry-picks 5892ae48.

Contrast, all confirmed present on `origin/main`:
`toolkit-field-<k>-input` / `-input-field` (`ToolBaseProperty.jsx:281`, `SecretField.jsx:77`),
`-editor` / `-editor-content` (`ToolBaseProperty.jsx:339-340`),
`<dataTestId>-combobox` (`SingleSelect.jsx:661`), `select-option-<value>` (`SingleSelect.jsx:416`),
`select-group-header-<group>` (`SingleSelect.jsx:383`), `toolkit-configuration-show-more`,
`toolkit-detail-save-button`, `toolkit-form-view-toggle`, `toolkit-detail-title`.

## How to check a runtime-composed testid's provenance

Grepping the composed string (`git grep toolkit-field-client_secret-input-toggle-secret`) returns
**no** on BOTH refs and tells you nothing — the string is built at render time. Grep the
**template / prop** instead:

```bash
cd ../EliteaUI && git fetch origin
git grep -n 'testIdPrefix'        origin/main -- src/          # the wiring
git grep -n 'toolkit-field-'      origin/main -- src/          # the template literal
git show origin/main:'src/[fsd]/shared/ui/secret-field/SecretField.jsx' | grep -n 'testId'
```

This is the concrete instance of the caveat in `.agents/workflow.md` § Closure record
("stage 1 cannot see runtime-composed testids at all — diff the component file instead").
An AFS PROVENANCE row that says `on-main ✓` for a composed testid without doing this is a
guess, and it propagates into the closure record.

Related: [[afs_provenance_rows_are_inherited_not_rederived]]

---
name: Reviewing a config-parameterised repair — prove the CI env actually sets the value
description: A fix keyed on settings.X is only a fix if the failing environment really sets X; follow workflow_call delegation to the reusable workflow
type: feedback
---

## The check that decides the verdict

When a repair replaces a hardcoded literal with `settings.<something>`, the fix is
correct **only if the environment that produced the red actually sets that value**.
If it doesn't, the parameterised expression collapses back to the default and the
assertion fails identically — a fix that looks right and changes nothing.

Worked case: PR #1918 / ELITEA-2020. `assert path == f"{settings.app_prefix}/pipelines/create"`.
`app_prefix` defaults to `""` in `automation/config.py:71`.

## Do not stop at a top-level grep of the workflow that ran

`grep -rn APP_PREFIX .github/workflows/` showed the variable in **only one** file
(`test-ui-custom.yml`), and NOT in `test-ui-dev-*.yml` / `test-ui-next.yml` /
`test-ui-stage2.yml` — which reads exactly like "the fix won't work on dev".

It was wrong. Those files are thin wrappers:

```yaml
test:
  uses: ./.github/workflows/test-ui-custom.yml   # ← workflow_call delegation
```

All deployed runs execute the callee's `Run UI tests` step, whose `env:` hardcodes
`APP_PREFIX: '/app'` (`test-ui-custom.yml:534`, unconditional). So the value IS set.

**Follow `uses:` before concluding an env var is missing.** A per-file grep does not
see through `workflow_call`.

## Second half of the same check

`.env.test` beats process env (`config.py` orders dotenv first), so also confirm CI
does **not** write one — `grep -niE 'env\.test|dotenv'` on the callee returned nothing,
so the process env wins. If CI had written `.env.test`, the workflow `env:` would have
been shadowed.

## Prefix-safety triage for URL assertions (reusable)

Not every URL handle needs parameterising. These are already prefix-tolerant and are
NOT findings:

- `page.wait_for_url("**/pipelines/create*")` — leading `**/` glob
- `re.compile(r".*/pipelines/all/\d+")` — unanchored `.*`
- `window.location.pathname.includes('/pipelines/all/')` — substring
- `.endswith("/pipelines/all")` / `"x" in path` — suffix/containment
- `super().navigate("/pipelines/all")` — `BasePage.navigate` prepends `settings.app_base_url`

Only **exact equality** on a path and a **`^`-anchored** regex are prefix-unsafe.
Grep the whole test body plus its page-object call graph for those two shapes before
accepting "there is no third anchor".

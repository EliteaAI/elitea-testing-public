---
name: testid-only locator policy scope is our own app source, not third-party redirect destinations
description: A test that follows an external link (Help Center resource cards, toolkit docs links, etc.) off EliteaUI onto a third-party host (docs.elitea.ai, videoportal.epam.com, learn.epam.com, ...) is NOT bound by the testid-only locator policy on that destination page — we can't add data-testid to a site we don't own. Use ordinary Playwright role/title locators there; declare it explicitly (role-overrides.md § Declared-improvisation protocol) since the reviewer's mechanical get_by_role/get_by_text grep will flag the line regardless of target.
type: feedback
---

## What happened (ELITEA-2220/2221/2222/2223/2224, combined analyst+implementer, 2026-08-14)

Automating Help Center resource-card links required asserting content on the
destination pages after clicking (docs.elitea.ai page titles, an EPAM SSO
redirect's final host, docs.elitea.ai's own nav-link count). All of these are
completely outside `EliteaUI`/`elitea_assistant` — third-party sites we have
zero source access to. `.agents/testing.md` § Locator policy and
`.agents/role-overrides.md`'s testid-only mandate are written assuming the
locator's TARGET is our own app; neither doc explicitly scopes "our own app"
vs "any page a test happens to touch," so this reads ambiguous on a first
pass.

## The resolution

The testid-only policy's own stated rationale is coverage measurement via
`data-testid` PRESENCE in `EliteaUI`/`elitea_assistant` source — a metric
that is meaningless (and unenforceable) on a page we don't control. Treated
this as scope-by-rationale: the policy governs locators against OUR OWN app;
a redirect destination is out of scope by definition, and ordinary
`get_by_role`/`get_by_title`/`to_have_title` locators against it are
compliant.

**This is still a canon gap** (no prior AFS/PR explicitly says so) — declared
it per `role-overrides.md` § Declared-improvisation protocol in the AFS
Automation Hints, a code comment at the call site, AND the PR description
(named the exact grep hits it produces), so the reviewer sees the reasoning
instead of reflexively blocking on the mechanical grep hit. The mechanical
grep (`get_by_role|get_by_text|...`) has no way to distinguish "our app" from
"third-party page" — it will always flag these lines; the declaration is what
keeps a spirit-compliant choice from being misread as an undeclared
violation.

## Reusable pattern for the next case that follows an external link

1. Identify whether the assertion target is `EliteaUI`/`elitea_assistant`
   source (testid-only, no exceptions) or a genuinely external host reached
   via `href`/redirect (role/title/text locators fine).
2. If external: use the most stable available Playwright locator on that
   site (role-based preferred, same ladder as `spec-format.md`'s generic UI
   example — it's the RIGHT tool here, testid-only was never meant to reach
   this far).
3. Declare it in the AFS (Automation Hints), a code comment, and the PR
   description — don't rely on the reviewer inferring the scope boundary
   themselves.

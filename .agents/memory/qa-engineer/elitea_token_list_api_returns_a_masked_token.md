---
name: Elitea token list API returns an ALREADY-MASKED token
description: GET /api/v2/auth/token/ returns token pre-masked; the table masks it again. Full JWT exists only in the generation dialog — never assert a "reveal" path.
type: project
aliases: [personal token masked, token value cell, authToken, mask of a mask]
tags: [area/settings, area/api, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## The fact (ELITEA-2285/2289/2291, verified live 2026-08-27)

`GET /api/v2/auth/token/` returns each token's `token` field **already
masked** — e.g. `"...jdGrGvQ"`. `TokensTable.jsx:119` then masks it a
**second** time for display: `'...' + row.token.substring(row.token.length - 4)`
→ `"...rGvQ"`. A mask of a mask.

The real value is a **226-char JWT** starting `eyJhbGciOiJI`, and it appears
in exactly one place in the whole product: the "New token generated!" dialog
(`generated-token-dialog-token-value`). Once that dialog closes, the full
string is in neither `document.body.innerText` nor the full
`documentElement.innerHTML`.

## Why it matters, in three places

1. **Never write a case/AFS asserting a "reveal the token" path.** ELITEA-2285's
   case text claimed the eye icon retrieves the full token; it does not
   (clarification #1886). The product is *stricter* than the case — asserting
   the case text as written is reverse-masking.
2. **The generation dialog is the only oracle.** Any test needing the real
   token must create the token itself and capture the value before closing the
   dialog. A pre-existing row's real token is unknowable.
3. **It leaks into generated IDE configs.** Both `onIdeSettingsDownload`
   (`PersonalTokens.jsx`) and `SettingsPreview.getVSCodeSettings` pass
   `row.token` straight into `eliteacode.authToken`, so the downloaded
   `settings.json` embeds the mask and cannot authenticate (bug #1884). When a
   case says "references the correct token", assert the **correct** value with
   `expect.soft()` — asserting the masked form would encode the bug as the
   contract and go green forever.

Surface detail lives in `test-specs/settings-personal-tokens/_surface.md`.

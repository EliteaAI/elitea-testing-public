---
name: Credential ID field mirrors rename — reverse-masking trap
description: elitea_title (ID) field is NOT frozen at creation; it live-regenerates from Display Name on every save including rename — case text that assumes it's frozen is stale, not the product
type: feedback
---

Confirmed live twice, independently (ELITEA-1972 and ELITEA-1963): the
Credential ID field (`elitea_title`, disabled/read-only input) is **not**
frozen at creation time. It regenerates from the Display Name on every
edit — including a plain rename — both as a client-side live preview
*before* Save and as the persisted value *after* Save + reload. The only
thing that genuinely stays stable across a rename is the **numeric URL id**
(`/credentials/all/{numeric_id}`), not the `elitea_title` string.

**Why this matters:** any TMS case text (or a future case in this same
family) that says "verify the ID field remains unchanged after rename" is
almost certainly wrong/stale — this is intentional product behavior, proven
correct by ELITEA-1972's dedicated ID-auto-generation test
(`test_credential_id_auto_generation.py`). Don't file it as a Bug — file it
as a CLARIFICATION (reverse-masking guard) and substitute the numeric URL
id as the corrected "stays unchanged" assertion in the AFS, using
`CredentialDetailPage.get_credential_id_from_url()`.

Applies to any credential type, not just Github (both prior confirmations
used Github credentials, but the mirroring logic lives in the shared
`ToolBaseProperty` renderer, not a type-specific code path).

---
name: Localhost CAN run chat image generation (VITE_DEV_TOKEN is sufficient)
description: The user_token corollary in testing.md § Merge gate does not apply to the Image Creation internal tool
type: project
---

# Localhost can gate chat image-generation specs

**Verified live 2026-09-09** (ELITEA-0679, `http://localhost:5173`, project 399).

`.agents/testing.md` § Merge gate carries a corollary that some flows **cannot** be gated on
localhost because the `VITE_DEV_TOKEN` identity has no `user_token` (the publish wizard's AI
gate returns `400 ai_validation_failed … Please create user_token`). It is tempting to assume
any LLM/internal-tool flow is in that bucket.

**It is not.** The chat **Image Creation** internal tool ran to completion on localhost:
default model `Anthropic Claude 4.5 Sonnet` → `ImageGen: generate_image` → a real rendered
`<img>`, **0 console errors**, no 400. End to end **~110-140 s** (send 17:50:56Z, image
17:52:43Z, rendered by 17:53:13Z).

Consequences:

- Image-generation specs can take their 3x merge gate on **localhost**; DEV is not mandatory.
- Budget ~2-2.5 min **per parameter**. `IMAGE_GENERATION_TIMEOUT = 180000` covers it with a
  modest margin — **do not lower it**.
- General rule this establishes: the `user_token` gap is **per-endpoint**, not "any AI call".
  Establish it empirically for the flow you are actually gating rather than inheriting the
  publish-wizard verdict.

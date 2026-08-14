---
name: AI Providers page is not "AI Configuration"
description: TMS cases naming "AI Configuration" mean the "AI Providers" settings page; tabs claim is a different page entirely
type: project
---

ELITEA-2392 asked to test a "Settings → AI Configuration" page with LLM
Models/Embedding/Vector Storage/etc. sections AND "AI Configuration"/"OpenAI
Template" tabs at the top. Neither claim matches a single real page:

- The section list (LLMs, Embedding Models, Vector Storage, Image
  Generation, Speech Recognition (ASR), Text to Speech (TTS), AI Credentials)
  lives on the **"AI Providers"** page (`/settings/ai-providers`,
  `AIProvidersContent.jsx` → `ConfigurationsPanel.jsx`). No tabs on this page
  at all.
- The "AI Configuration"/"OpenAI Template" tabs described in the case
  actually exist on a totally different page — Settings → General
  (`/settings/project-general`) → "AI Configurations" accordion
  (`ProjectAIConfigurations.jsx`) — and are literally labelled **"Basic"** /
  **"OpenAI Template"**, not "AI Configuration".
- `ConfigurationSection.jsx` hides a section entirely (`return null`) when
  its `configurations` array is empty — Vector Storage and AI Credentials
  are both empty on the shared `Private`/399 test project, so they never
  render there. Confirmed via network capture (both `200`, `items: []`) —
  correct empty-state behaviour, not a defect. Any future case touching
  these two sections needs seeded data or a conditional (API-response-based)
  assertion instead of an unconditional visibility check.
- Filed as clarification: EliteaAI/elitea-testing-public#1250. AFS + full
  digest: `test-specs/settings-ai-providers/`.
- Zero testids anywhere in the `ai-providers` component tree as of
  2026-08-06; `DrawerPageHeader.jsx`'s missing `titleTestId` prop-thread gap
  (previously flagged by the `settings-personal-tokens` analyst) still
  applies here too — `AIProviders` was already named as a pending consumer
  in that digest.

---
name: "Settings → AI Configuration is TWO different surfaces"
description: TMS cases saying "Settings → AI Configuration" split between /settings/ai-providers and the AI Configurations accordion on /settings/project-general
type: reference
aliases: [ai configuration, ai-configurations accordion, openai template tab, ai providers page identity]
tags: [area/settings, type/surface-map]
created: 2026-08-29
updated: 2026-08-29
---

## The split

No page or nav item called "AI Configuration" exists. A TMS case naming it means
one of two unrelated surfaces — decide by what the case asserts:

| Case mentions | Surface |
|---|---|
| LLM / Embedding / Vector Storage / Image Generation / ASR / TTS / **AI Credentials** sections, the "+" provider create flow | Settings → **AI Providers**, `/settings/ai-providers` |
| **Basic / OpenAI Template** tabs, `OpenAI-BaseURL` / `Server URL` / `OpenAI-Project` / `Project ID`, the code template | Settings → **General**, `/settings/project-general` → the `data-testid="ai-configurations"` accordion |

Digests: `test-specs/settings-ai-providers/_surface.md` and
`test-specs/settings-ai-configurations/_surface.md`.

## Gotchas worth remembering

- The accordion's left tab is **"Basic"** — cases calling it "AI Configuration"
  are stale (clarification #1981; family drift #1250/#1772/#1906).
- `OpenAI-Project` is the **default LLM model's** project id (observed `1`),
  NOT the selected project (`Project ID`, observed `400`). Never assert equality.
- Tab state is component-local `useState` — a reload resets to Basic, no URL
  reflection. A tab switch fires **no network request**.
- `FieldWithCopy` already accepts a `testId` prop; `Tab.TabGroupButton` items take
  `buttonProps: { 'data-testid': … }` (precedent `project-context-mode-edit-button`).
  Both mean zero component plumbing for the testids these cases need.

Related: [[browser_fetch_on_localhost_logs_cors_console_errors]]

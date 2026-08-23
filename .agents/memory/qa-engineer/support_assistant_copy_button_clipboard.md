---
name: Support Assistant copy-to-clipboard button
description: The widget's copy button confirms with a 2s SVG swap (no tooltip change) and copies raw markdown, not rendered text
type: reference
aliases: [copy to clipboard, CopyButton, support assistant clipboard, data-copied]
tags: [area/support-assistant, type/handle]
created: 2026-08-22
updated: 2026-08-22
---

## What it is

`../elitea_assistant/src/components/shared/CopyButton.tsx`, rendered from
`src/components/chat/MessageItem.tsx:73` for `role === 'assistant' && content && !isStreaming
&& !isAnimating`. No `data-testid` as of 2026-08-22; raw handle
`button[aria-label="Copy to clipboard"]`.

## The three things that cost time

1. **Confirmation is an SVG `path` swap only.** `CopyIcon` -> `CheckIcon`, reverting after exactly
   2000 ms (`setTimeout` in `handleCopy`). `aria-label` and `className` do NOT change, and the
   tooltip stays `"Copy to clipboard"` — it never says `"Copied"`. Nothing in the DOM names the
   state, so a `data-copied="true|false"` attribute has to be added to assert it at all.
2. **The clipboard gets `message.content` — RAW MARKDOWN.** `**bold**`, `---` and friends. It does
   NOT equal the bubble's `inner_text()`. Compare normalised (strip `[*_`#]`, drop rule lines,
   collapse whitespace). The paste round-trip *is* exact, so `to_have_value(clipboard)` after
   `Ctrl/Cmd+V` is a safe strict assertion.
3. **The copy button is the reply-COMPLETE signal** on this surface — wait on
   `count > baseline`, and remember a "New chat" already has 1 (the greeting).

Clipboard permissions are pre-granted in `automation/conftest.py:303`;
`BasePage.get_clipboard_text()` reads it; clearing before the click is hygiene, not substitution
(precedent `pages/help_center_page.py:130`).

Related: [[project_briefing]]

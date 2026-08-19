---
name: Scoped content-read vs new-locator mechanical grep risk
description: .locator('p, span')-style content extraction scoped inside a testid'd parent will hit the reviewer's non-testid-handle grep even though it's compliant precedent
type: feedback
---

ELITEA-2206 (chat `#`-search dropdown, `NewParticipantCard.jsx`) needed to read a
card's type subtitle text (`agent`/`pipeline`), icon presence, and the literal
`"Public"` chip — all scoped INSIDE an already-testid'd item card
(`chat-hash-search-item-{}_{}`).

These calls (`item.locator('p, span')`, `item.locator('img, svg, .MuiAvatar-root')`,
`item.get_by_text("Public")`) DO surface in the reviewer's mechanical grep
(`.agents/role-overrides.md` § Reviewer slot: `get_by_role|get_by_label|get_by_text|
...|page\.locator|\.locator\(`) — the grep is a first-pass filter, not the verdict.
Read literally, the "compliant only if `[data-testid=` or an UPPER_CASE
`[data-testid=` constant" rule would flag them, but there IS established project
precedent for exactly this shape when the selector never stands alone and only
ever runs scoped inside a testid-identified parent, for CONTENT EXTRACTION (not
locating a new independently-addressable element):

1. `.claude/rules/mui-patterns.md` § Extracting Message Text — `_extract_message_body()`
   uses `message_locator.locator('p')` / `.locator('.MuiTypography-bodyMedium')`,
   explicitly marked ✅ CORRECT, scoped inside an already-identified message row.
2. `chat_page.py`'s ELITEA-2196 `get_attachment_chip_computed_style()` —
   `has_file_icon` structural presence check scoped inside the testid'd
   `chat-attachment-chip-{i}` parent.

**Action when this pattern recurs:** cite both precedents explicitly in the new
helper method's docstring (not just the class-constant comment) so the reviewer's
one-hop check has something to follow — a grep hit with no citation reads as an
unexplained violation even when the underlying pattern is sound. Don't invent a
testid for pure text/structural content that will never need one (many dynamic
rows, no independent addressing use).

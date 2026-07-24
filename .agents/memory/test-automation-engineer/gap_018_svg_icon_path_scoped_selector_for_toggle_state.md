---
name: GAP-018 SVG icon-path scoped selector for toggle-button state
description: Testid-policy-compliant technique for reading a two-state icon button's rendered state (e.g. Play/Stop) via a scoped `[data-testid="X"] path` class constant, when no separate app testid exists on the icon itself.
type: feedback
---

## The situation

GAP-018 (voice mini-player Play/Stop toggle) needed to assert which of two SVG
icons `chat-voice-play-stop-button` currently renders (`play.svg` when idle,
`stop_record.svg` while `isPlaying`). The AFS's own Concrete Handles table
recommended "SVG `<path d="...">` comparison" as the state-read technique, but
naively chaining `.locator("path")` off the existing `voice_play_stop_button`
`LocatorDescriptor` field would violate `.claude/rules/page-objects.md`'s
"don't chain a raw selector off an existing field" anti-pattern AND fail the
reviewer's mechanical grep (`.locator(` hit whose string isn't `[data-testid=`).

Two policy-compliant options existed: (a) add a new `data-*` state attribute
to the button in EliteaUI JSX (the sanctioned "state via data-* attribute"
pattern), or (b) define a class-level UPPER_CASE constant containing
`[data-testid="…"]` that reaches one level deeper via a descendant combinator,
matching `.agents/testing.md`'s own "Scoped sub-selectors: UPPER_CASE class
constants containing `[data-testid="…"]` only" wording (which doesn't
restrict the selector to being *only* the bare testid string).

## What I did

Chose (b) — no EliteaUI JSX change needed, AFS already said "no new testids
required," and the icon SVG's `d` attribute is a stable identity (only two
fixed path strings ever render, one per state):

```python
# class-level constant — the pattern stays in the greppable testid inventory
VOICE_PLAY_STOP_ICON_PATH = '[data-testid="chat-voice-play-stop-button"] path'
_PLAY_ICON_PATH_PREFIX = "M13 8C13.0003"   # EliteaUI/src/assets/play.svg
_STOP_ICON_PATH_PREFIX = "M12 4.72727"     # EliteaUI/src/assets/stop_record.svg

def is_play_stop_showing_stop_icon(self, timeout=5000) -> bool:
    icon = self.page.locator(self.VOICE_PLAY_STOP_ICON_PATH)
    icon.wait_for(state="attached", timeout=timeout)
    path_data = icon.get_attribute("d") or ""
    if path_data.startswith(self._STOP_ICON_PATH_PREFIX):
        return True
    if path_data.startswith(self._PLAY_ICON_PATH_PREFIX):
        return False
    raise AssertionError(f"Unrecognized play/stop icon path data: {path_data!r}")
```

Self-check grep on the diff (`git diff HEAD~1 -- automation/pages/chat_page.py
... | grep -nE '^[+].*(...|page\.locator|\.locator\()'`) surfaced exactly
this one line; verified compliant per the one-hop rule (the constant's own
class-level definition literally starts with `[data-testid=`).

Also deliberately did NOT assert the button's tooltip text ("Start speaking"/
"Stop speaking") — no testid-compliant handle exists for MUI's hover-only
tooltip popper content (`get_by_role("tooltip")` is banned outright by the
locator policy, and the tooltip only renders in the DOM while actually
hover-open). Documented the omission explicitly in the method docstring
rather than silently skipping it — the icon-path check plus the correlated
`chat-voice-settings-button`'s native `disabled={isPlaying}` attribute
together cover the full `isPlaying` state surface without a forbidden handle.

## Generalizable lesson

When a two-state icon button (Play/Stop, Expand/Collapse-as-different-icons,
etc.) has NO separate testid on its icon and the state-encoding attribute
(SVG path data, icon class name, etc.) is a fixed, finite set of known
values — a scoped `[data-testid="<button>"] <descendant-selector>` UPPER_CASE
class constant is the compliant pattern, not a raw `.locator()` chained off
the field. Reach for the "add a data-* state attribute in EliteaUI" route
(sanctioned pattern in `.agents/testing.md`) only when no such deterministic
DOM signal already exists, or when the AFS's own analyst already asked for
one. Cross-reference: another correlated, ALREADY-testid'd sibling element
(here, `chat-voice-settings-button`'s `disabled` state, which mirrors the
same boolean) is often available as a second, zero-extra-locator proof of
the same state — use it to strengthen coverage instead of trying to force a
single locator to prove everything.

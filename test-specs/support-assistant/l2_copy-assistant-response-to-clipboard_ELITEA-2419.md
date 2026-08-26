# Test Case: Copy assistant response to clipboard

## Metadata
- **TMS ID**: ELITEA-2419
- **Source case**: `.agents/automation/support-assistant-w01/cases/ELITEA-2419.md` (intake snapshot)
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`,
  `../elitea_assistant` @ `b8a287b` aliased in via `VITE_ASSISTANT_LOCAL=1`, dev backend via `VITE_DEV_TOKEN`)
- **User set**: `${TEST_USER}` (auto-authenticated on localhost via dev token)
- **Analyst**: qa-engineer (Sage)
- **Analysed**: 2026-08-22 (live, headless Playwright scratch probe, 1 run, reply latency 69.6 s)
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/support-assistant/_surface.md`

## Classification

**Status: `ready-for-automation`**

All six case steps execute exactly as authored against the live product: the widget opens, the message
sends, the assistant replies, a **"Copy to clipboard"** button is present on the assistant's response
bubble (and only there), clicking it swaps the icon to a check mark for ~2 s **and** writes the response
to the real OS clipboard, and pasting into the widget input reproduces the clipboard content byte for
byte. No defects. No blockers. No substitutions.

Two things the implementer must know before writing a line (details below):

1. **The clipboard receives the RAW MARKDOWN source, not the rendered text.** Observed clipboard
   contained `**Need more help?**` and `---` where the bubble renders bold text and a horizontal rule.
   A naive `clipboard == bubble.inner_text()` assertion **will fail**. § Implementation Notes gives the
   assertion recipe.
2. **The visual confirmation is an SVG icon swap that self-reverts after exactly 2000 ms.** There is
   nothing in the DOM today that names that state — hence the `data-copied` state attribute requested in
   § Handles Reference. Assert it promptly after the click.

Not covered anywhere today: `grep -rn -i "copy" automation/tests/ui/support_assistant/` → 0 hits;
no `test-specs/support-assistant/*` file mentions clipboard. `chat_page.py`'s `chat-copy-button` /
`message-copy-button` belong to the **main Chat surface** (`tests/ui/chat/`), a different component in a
different repo — not coverage for this case.

## Preconditions

- User logged in (localhost: auto-authenticated via `VITE_DEV_TOKEN`; deployed envs: `auth_state` fixture)
- Browser context granted `["clipboard-read", "clipboard-write"]` — already the default in
  `automation/conftest.py:303`, no fixture work needed
- On any page where the sidebar Support Assistant launcher is visible (`/chat` used here)

## Test Data

| Field | Value |
|---|---|
| Prompt | `Explain in one sentence what an AI agent is` |

No seeded data, no cleanup. The test starts a **New chat** so it does not depend on restored history.

## Execution Evidence

Executed 2026-08-22 via a throwaway Playwright script driving the real browser
(`../.venv/bin/python`, `headless=True`, `permissions=["clipboard-read","clipboard-write"]`).
Values below are verbatim from that run's JSON dump.

### Step 1 — Open the Support Assistant widget

**Action:** real pointer click on the sidebar launcher `[data-testid="sidebar-support-assistant-button"]`
(a click on `button.elitea-assistant-button` is intercepted — see the digest's quirk 1).

**Observed:** `[data-testid="support-assistant-widget"]` visible. ✓ Then clicked
`button[aria-label="New chat"]` for a clean session — after which **1 copy button was already present**
(the assistant posts a greeting message on a new chat). Baseline, not zero.

### Step 2 — Send the message "Explain in one sentence what an AI agent is"

**Action:** `fill()` on `[data-testid="support-assistant-message-input"]`, then click
`[data-testid="support-assistant-send-button"]`.

**Observed:** message accepted; user bubble rendered with the exact prompt text:
`<div class="elitea-assistant-message elitea-assistant-message--user">Explain in one sentence what an AI agent is</div>`

### Step 3 — Wait for the assistant response to appear

**Observed:** reply complete after **69.6 s**. Completion signalled by the copy-button count going
1 → 2 (the copy button only renders when `!isStreaming && !isAnimating` —
`MessageItem.tsx:70-73`), which is the *correct* wait condition for this case, not a message-count delta.

Rendered bubble text (`.elitea-assistant-message--assistant` → `innerText`):

```
In ELITEA, an AI agent is a customizable virtual assistant that can independently use instructions,
toolkits, and integrations to make decisions and complete specific tasks or workflows.

💡 Need more help? Ask a follow-up or describe what you'd like to do next.

🤝 For human support: SupportAlita@epam.com
```

Bubble HTML shows the markdown was rendered: `<strong>Need more help?</strong>`, `<hr>`, and a
`<a href="mailto:...">` — all of which are **absent** from the clipboard payload (see Step 6).

### Step 4 — Locate the "Copy to clipboard" button on the assistant's response bubble

**Observed** — verbatim `outerHTML` of the button:

```html
<button class="elitea-assistant-header-action" aria-label="Copy to clipboard" type="button">
  <svg viewBox="0 0 14 14" ...><path d="M4.66667 4.66667V2.33333C4.66667 ..."></path></svg>
</button>
```

- **No `data-testid`.** Parent is `<div class="elitea-assistant-tooltip-trigger">`, which sits **inside**
  the assistant bubble `div.elitea-assistant-message--assistant`.
- Source: `../elitea_assistant/src/components/shared/CopyButton.tsx`, rendered from
  `src/components/chat/MessageItem.tsx:73`.
- **The user's own bubble has no copy button** — observed `outerHTML` of the last user bubble is a bare
  `<div class="… --user">Explain in one sentence what an AI agent is</div>` with no children. The
  affordance is assistant-response-only, matching the case title.
- Hovering the button shows a tooltip `.elitea-assistant-tooltip` with text **"Copy to clipboard"**.

### Step 5 — Click it and verify a visual confirmation appears

**Action:** cleared the clipboard first (`navigator.clipboard.writeText('')`), then a real click.

**Observed, 250 ms after the click** — same button, same `aria-label`, **different SVG path**:

```html
<button class="elitea-assistant-header-action" aria-label="Copy to clipboard" type="button">
  <svg viewBox="0 0 14 14" ...><path d="M11.6667 3.5L5.25 9.91667L2.33333 7"></path></svg>
</button>
```

That path is the **check mark** (`CheckIcon`) replacing `CopyIcon` — this **is** the "icon change" the
case offers as its first example of visual confirmation. ✓

**Observed, 2.2 s later:** the button's SVG had reverted to the original copy-icon path. Source
confirms: `CopyButton.tsx:11-15` — `setCopied(true); setTimeout(() => setCopied(false), 2000)`.

**Tooltip does NOT change.** After the click, the tooltip text was still `"Copy to clipboard"` — never
`"Copied"`. See § Known Deviations; this is not a defect (the case offers icon change *or* tooltip as
alternatives, and the icon change is present).

**Screenshot:** `automation/test-results/screenshots/ELITEA-2419-step-05-copied-icon.png`

### Step 6 — Paste the clipboard content and verify it matches the assistant response

**Observed clipboard content** (verbatim, `navigator.clipboard.readText()`):

```
In ELITEA, an AI agent is a customizable virtual assistant that can independently use instructions, toolkits, and integrations to make decisions and complete specific tasks or workflows.

---

💡 **Need more help?** Ask a follow-up or describe what you'd like to do next.

🤝 For human support: **SupportAlita@epam.com**

---
```

**Action:** clicked the widget input, pressed `ControlOrMeta+V`.

**Observed:** `input_value()` of `[data-testid="support-assistant-message-input"]` was **byte-identical**
to the clipboard string above, including the `**` markers, the `---` rules and the emoji. ✓
Input cleared afterwards (`fill("")`) so no message is left staged.

**Note the discrepancy the case does not anticipate:** the clipboard carries `message.content` — the raw
markdown source (`CopyButton.tsx:12` → `navigator.clipboard.writeText(text)` where
`text = message.content`, `MessageItem.tsx:73`). The bubble carries the *rendered* HTML. They agree in
meaning, not in bytes.

### Side channels

`page.on("console")` filtered to `type == "error"` → **0 errors** across the whole run.
(The digest's known `Module "stream" has been externalized…` line is a *warning*, correctly filtered out.)

## Handles Reference

Locator policy is **testid-only** (`.agents/testing.md` § Locator policy). Every row below is a
class-level `LocatorDescriptor(testid=…)` field or an UPPER_CASE `[data-testid="…"]` class constant on
`automation/pages/support_assistant_page.py`. Provenance verified 2026-08-22 with
`git fetch origin` in `../elitea_assistant` and `../EliteaUI`.

| # | Element | Handle | Provenance |
|---|---|---|---|
| 1 | Sidebar launcher | `sidebar-support-assistant-button` | on `EliteaAI/EliteaUI` `automation/testids` only (EliteaAI/EliteaUI@37176b46) — awaiting human promotion to `main`. Page-object field `sidebar_launcher` already exists. |
| 2 | Widget window | `support-assistant-widget` | on `EliteaAI/elitea_assistant` `automation/testids` only (EliteaAI/elitea_assistant@b8a287b). Field `widget` exists. |
| 3 | Message input | `support-assistant-message-input` | same commit as (2). Field `message_input_field` exists. |
| 4 | Send button | `support-assistant-send-button` | same commit as (2). Field `send_message_button` exists. |
| 5 | Message item wrapper | `support-assistant-message-item` | same commit as (2). Field `message_items` exists. |
| 6 | **Copy-to-clipboard button on a response** | `support-assistant-message-copy-button` | **ADDED during implementation** — EliteaAI/elitea_assistant@216da01 on `automation/testids` (`src/components/shared/CopyButton.tsx`, caller-supplied `testId` prop wired at `MessageItem.tsx`). Field `message_copy_buttons`. |
| 7 | Copied-state flag on that same button | `data-copied="true" \| "false"` | **ADDED during implementation** — same commit / element as (6). Constants `MESSAGE_COPY_BUTTON_COPIED` / `_IDLE`. |
| 8 | Assistant/user message bubble | `support-assistant-message-bubble` | **ADDED during implementation** — EliteaAI/elitea_assistant@216da01 (`MessageItem.tsx`). Field `message_bubbles`, constant `MESSAGE_BUBBLE`. |
| 9 | Role flag on the message item wrapper | `data-role="assistant" \| "user"` | **ADDED during implementation** — same commit; same element as (5). Constants `ASSISTANT_MESSAGE_ITEM` / `USER_MESSAGE_ITEM`. |

### How rows 6–9 must be added (canon-compliant shapes — do not improvise)

Repo: **`../elitea_assistant`** on its own `automation/testids` branch. This is a **connected
first-party repo** (canon #705, `.agents/workflow.md` § Connected repos) — *not* a #579 third-party
waiver. Commit + push there is the terminal step; a human cherry-picks to its `main`.

**Row 6 + 7 — `CopyButton.tsx` (a `src/components/shared/` component ⇒ caller-supplied `testId` prop,
never a hardcoded feature-scoped testid):**

```tsx
const CopyButton: React.FC<{ text: string; testId?: string }> = memo(props => {
  const { text, testId } = props;
  ...
      <button
        className="elitea-assistant-header-action"
        onClick={handleCopy}
        aria-label="Copy to clipboard"
        type="button"
        data-testid={testId}
        data-copied={copied ? 'true' : 'false'}
      >
```

and at the call site, `MessageItem.tsx:73`:

```tsx
!message.isAnimating && <CopyButton text={message.content} testId="support-assistant-message-copy-button" />}
```

- The `testId` **prop** (not `dataTestId`) is the shape `.agents/testing.md` § Locator policy mandates
  for shared components — the `{section}-…` prefix names the CALL SITE's feature, not the component.
- `data-copied` is the mandated **state-as-`data-*`-attribute** shape (PR #581 ruling). It reflects the
  already-existing `copied` state — **no new hook, no new DOM node, no new state**. Never encode this
  state by flipping the testid value.

**Row 8 + 9 — `MessageItem.tsx`, attributes only, zero structural change:**

```tsx
<div
  className={`elitea-assistant-message-wrapper elitea-assistant-message-wrapper--${message.role}`}
  data-testid="support-assistant-message-item"
  data-role={message.role}                                   // ← row 9
>
...
    <div
      className={`elitea-assistant-message elitea-assistant-message--${message.role}${...}`}
      data-testid="support-assistant-message-bubble"          // ← row 8
    >
```

Every one of these is an added attribute (plus one optional prop). Nothing is replaced, no element is
introduced, no hook is added — the § Zero-functional-impact reviewer greps must come back clean.

### Page-object shape expected on `SupportAssistantPage`

**As shipped** on `automation/pages/support_assistant_page.py` (additive — the legacy
`fallback=` fields are untouched for their existing callers):

```python
message_copy_buttons = LocatorDescriptor(testid="support-assistant-message-copy-button", ...)
message_bubbles      = LocatorDescriptor(testid="support-assistant-message-bubble", ...)

# UPPER_CASE class constants for the scoped / state-filtered forms
MESSAGE_COPY_BUTTON        = '[data-testid="support-assistant-message-copy-button"]'
MESSAGE_COPY_BUTTON_COPIED = '[data-testid="support-assistant-message-copy-button"][data-copied="true"]'
MESSAGE_COPY_BUTTON_IDLE   = '[data-testid="support-assistant-message-copy-button"][data-copied="false"]'
ASSISTANT_MESSAGE_ITEM     = '[data-testid="support-assistant-message-item"][data-role="assistant"]'
USER_MESSAGE_ITEM          = '[data-testid="support-assistant-message-item"][data-role="user"]'
MESSAGE_BUBBLE             = '[data-testid="support-assistant-message-bubble"]'
```

Helpers shipped alongside them: `get_copy_button_count()`, `last_assistant_item()`,
`last_user_item()`, `copy_button_in(item)`, `bubble_in(item)`, `send_message_via_testid(text)`,
plus `BasePage.clear_clipboard()`.

No raw selector may be chained off these. Nothing is constructed in a method body except
`self.page.locator(self.CONSTANT)`, which is the sanctioned dynamic/scoped shape.

## Implementation Notes

### Waiting for the response — wait on the COPY BUTTON, not the message count

The copy button renders only when the assistant message is finished
(`message.content && !isStreaming && !isAnimating`, `MessageItem.tsx:70-73`). So:

**As shipped** — a plain auto-retrying assertion, no `wait_for_function`, no `page.evaluate`
(the analyst's original JS recipe is unnecessary: exactly one reply is expected, so the target
count is known):

```python
copy_baseline = support_page.get_copy_button_count()   # NOT zero — the New-chat greeting has one
expect(support_page.message_copy_buttons).to_have_count(copy_baseline + 1, timeout=180_000)
```

- **Baseline, never absolute.** A fresh chat already shows 1 copy button (the greeting). Digest quirk 2.
- **Use 180 s, not the 120 s default.** Observed latency 69.6 s; the digest records 33–135 s on this
  surface, so 120 s is *tight*, not generous. There is no token streaming — the message appears atomically.
- Never a `sleep`.

### The 2000 ms confirmation window is the one real timing constraint

`data-copied` flips to `"true"` synchronously in the click handler and back to `"false"` 2000 ms later.
Assert it as the **first thing after the click**:

```python
copy_btn.click()
expect(page.locator(MESSAGE_COPY_BUTTON_COPIED)).to_have_count(1)   # polls; passes immediately
```

Do **not** read the clipboard first and then assert the icon — the clipboard read plus a paste round-trip
can easily burn the 2 s. Assert the state, then read the clipboard. Optionally assert the revert
afterwards with `expect(...COPIED).to_have_count(0)` (Playwright polls up to its timeout, so no sleep).

### Asserting "the clipboard matches the response" — the clipboard is the ORACLE

Fidelity: the assistant's answer is nondeterministic, so **capture what the system produced and assert
the UI against it** (`.agents/testing.md` § Fidelity policy → "How to test a nondeterministic producer").
Never hand-write an expected string.

Three assertions, in this order:

1. **Something was copied, and it was the response.**
   Clear the clipboard *before* the click (shipped as `BasePage.clear_clipboard()`, which wraps the
   exact `page.evaluate("() => navigator.clipboard.writeText('')")` pattern `help_center_page.py:130`
   already uses), then after the click assert the clipboard
   is non-empty and is **not** the user's prompt:
   ```python
   clip = support_assistant.get_clipboard_text()      # BasePage.get_clipboard_text(), line 468
   assert clip.strip(), "clipboard empty after clicking Copy to clipboard"
   assert clip.strip() != PROMPT
   ```
2. **Content correspondence — markdown-tolerant, never byte-equality against `inner_text()`.**
   The clipboard holds raw markdown; the bubble holds rendered text. Compare on a normalised basis:
   ```python
   def _plain(s: str) -> str:
       s = re.sub(r"[*_`#]", "", s)             # emphasis / code / heading markers
       s = re.sub(r"^\s*-{3,}\s*$", "", s, flags=re.M)   # horizontal rules
       return re.sub(r"\s+", " ", s).strip()

   bubble_text = <assistant item>.locator(MESSAGE_BUBBLE).inner_text()
   first_para  = bubble_text.split("\n")[0].strip()      # the substantive answer sentence
   assert _plain(first_para) in _plain(clip)
   ```
   The first-paragraph anchor is deliberate: it is the actual answer and is always plain prose for this
   prompt, whereas the trailing boilerplate ("Need more help?…") is markdown-heavy and its exact
   decoration is not this case's subject. Asserting the whole bubble byte-for-byte would be a flaky
   assertion about the *renderer*, not about copy.
3. **Step 6's literal observable — the paste round-trip is exact.**
   ```python
   input_field.click()
   page.keyboard.press("ControlOrMeta+V")
   expect(input_field).to_have_value(clip)       # byte-identical — confirmed live
   input_field.fill("")                          # leave nothing staged
   ```
   This one **is** exact equality and it is deterministic, because both sides came from the system.

`get_clipboard_text()` uses `page.evaluate("navigator.clipboard.readText()")`. That is an **observation
channel reading a value the product wrote**, not a substitution — see § Fidelity Declaration.

### Cleanup

None required beyond clearing the input. The test starts a **New chat**, so it neither depends on nor
pollutes prior history. Do not delete the conversation (no such affordance is exercised by this case).

### Markers

`@pytest.mark.p2`, `@pytest.mark.support_assistant`, `@pytest.mark.regression`, `@pytest.mark.ui`.
Not `smoke` — a ~70 s live LLM round trip is not a critical-path fast test.
Steps wrapped in `with allure.step("Step N — …")`, one block per Coverage-Map Axis-1 row.

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result (case) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | localhost dev-token auth (`auth_state`) | fixture | covered |
| Step 1 — Open the Support Assistant widget | Target page/section loads | Click `sidebar-support-assistant-button`; `support-assistant-widget` visible | Step 1 | covered |
| Step 2 — Send "Explain in one sentence what an AI agent is" | Completes without error | Fill `support-assistant-message-input`, click `support-assistant-send-button`; user bubble shows the exact prompt | Step 2 | covered |
| Step 3 — Wait for the assistant response | Wait completes; state ready | `wait_for_function` on copy-button count > baseline (180 s); assistant bubble non-empty | Step 3 | covered |
| Step 4 — Locate the "Copy to clipboard" button on the response bubble | Present, no error | `message_copy_buttons.last` visible; `aria-label == "Copy to clipboard"`; it is a descendant of the **assistant** message item | Step 4 | covered |
| Step 5 — Click it; verify a visual confirmation (icon change / tooltip "Copied") | Control responds; next state shown | `data-copied` flips `"false"` → `"true"`, then back after ~2 s | Step 5 | covered (via the **icon change** limb; the tooltip limb does not occur — § Known Deviations) |
| Step 6 — Paste the clipboard content; verify it matches the response text | Field accepts input and displays it | Clipboard non-empty ≠ prompt; first-paragraph correspondence; `to_have_value(clip)` after `Ctrl/Cmd+V` | Step 6 | covered |
| Expected Final State — pasted content matches the assistant response | — | Same as Step 6 | Step 6 | covered |
| Pass criterion — "all steps complete without errors" | — | Console assertion filtered to `type == "error"` (0 observed) | teardown | covered |

Nothing from the case is dropped, deferred or weakened.

### Axis 2 — observables asserted BEYOND the case

| Extra observable | Why it is grounded |
|---|---|
| The **user's** message item contains **zero** copy buttons (`to_have_count(0)` scoped under `USER_MESSAGE_ITEM`) | The case is titled "Copy **assistant** response" — the affordance being response-only is the invariant that makes Step 4 meaningful. Confirmed live: the user bubble has no children. An absence assertion is a first-class reference (canon #511 extension). |
| `data-copied` returns to `"false"` after the confirmation window | The confirmation is transient by design (`setTimeout(…, 2000)`); asserting only the "true" edge would pass even if the button latched permanently, which would be a real regression. |
| Console has no `type == "error"` messages during the run | Standard side-channel check; 0 observed. The Vite `Module "stream" has been externalized` line is a *warning* and must be filtered by type, not by text (digest quirk 6). |

## Fidelity Declaration

| Item | Transit / terminal / neither | Authority |
|---|---|---|
| `page.evaluate("() => navigator.clipboard.writeText('')")` **before** the click | **Neither — precondition hygiene.** It clears the clipboard so a stale value cannot be mistaken for a fresh copy. The asserted value is written afterwards by the **product** (`CopyButton.handleCopy`). In-repo precedent: `automation/pages/help_center_page.py:130`. | — |
| `page.evaluate("() => navigator.clipboard.readText()")` (`BasePage.get_clipboard_text`) | **Neither — observation channel.** It *reads* the OS clipboard; it does not produce the value. There is no other way to observe a clipboard write. | — |
| The expected response text | **Not authored by the test.** The live LLM answer is the oracle; assertions compare product-produced clipboard against product-rendered bubble. | `.agents/testing.md` § Fidelity policy → "How to test a nondeterministic producer" |

**No `page.route`, no `route.fulfill`, no `monkeypatch`, no injected state, no fabricated response.**
The reviewer's provenance grep should return the two `navigator.clipboard` `evaluate` calls above and
nothing else; both are disposed here.

## Known Deviations (case text vs live product)

1. **The tooltip never reads "Copied".** Case Step 5 says *"verify a visual confirmation (e.g., icon
   change, tooltip 'Copied') appears"*. Live, the tooltip text is `"Copy to clipboard"` before **and
   after** the click; the confirmation is delivered purely as the icon swap. Because the case offers the
   icon change as its **first** alternative and that alternative is present, the case's expected result
   **is satisfied** — this is not a defect and no clarification ticket is filed. Recorded here so nobody
   re-litigates it. Do **not** write a tooltip-text assertion.
2. **The clipboard payload is raw markdown, not the rendered text.** Case Step 6 says the pasted content
   should "match the assistant response text". It matches its *source*, not its *rendering*. This is
   normal, intentional copy-the-markdown behaviour and is why § Implementation Notes prescribes a
   markdown-tolerant correspondence assertion rather than string equality against `inner_text()`.

## Known Defects

None. No product defect was observed and no ticket was filed for this case.

## Blocked Steps

None.

## Gotchas (carried into the surface digest)

- Copy button = `CopyButton.tsx`, a `src/components/shared/` component rendered from `MessageItem.tsx:73`
  only for `role === 'assistant' && content && !isStreaming && !isAnimating`.
- Confirmation is an SVG path swap (`CopyIcon` → `CheckIcon`), `aria-label` and `className` unchanged —
  which is exactly why a `data-copied` attribute is required to assert it at all.
- Its self-revert is 2000 ms.
- Clipboard = `message.content` (markdown source).
- A **New chat** already contains 1 assistant greeting (hence 1 copy button) — always work off a baseline.
- Reply latency this run: 69.6 s.

## Implementation record (2026-08-22, test-automation-engineer)

- Spec: `automation/tests/ui/support_assistant/test_support_assistant_copy_response.py`
  (`TestSupportAssistantCopyResponse::test_copy_assistant_response_to_clipboard`).
- Testids of rows 6-9 added in **EliteaAI/elitea_assistant@216da01** on its `automation/testids`
  branch (attributes + one optional `testId` prop only — no new hook, node or state). Pushed;
  a human cherry-picks to that repo's `main`, then EliteaUI bumps the git-dependency.
- Ran GREEN 1/1 first attempt, 85.7 s, zero reruns. Reply latency in that run ~70 s, consistent
  with the digest's 33-135 s band — the 180 s wait is the right size.
- Provenance grep on the diff returns exactly one hit, `clear_clipboard`'s
  `navigator.clipboard.writeText('')`, disposed in § Fidelity Declaration as precondition hygiene.

---
name: JS wait predicates — verify the testid'd element's innerText SCOPE
description: A wait_for_function comparing innerText to an id can be silently unsatisfiable if the testid sits on a wrapper that also renders a label
type: feedback
---

When reviewing a `page.wait_for_function` predicate that compares a testid'd
element's `innerText` to some other value (an id, a name, a URL segment), the
load-bearing check is **where the component actually spreads `data-testid`** —
not whether the testid exists.

Worked case: PR #1875 (ELITEA-1888) gates on
`document.querySelector('[data-testid="copy-version-id"]').innerText.trim() === urlSegment`.
`ApplicationInformation.jsx` renders that testid on a `CopyToClipboardButton`
whose props include `label="Version ID:"`. If the testid had landed on the
component's outer `<Box>`, `innerText` would be `"Version ID: 1676"` and the
predicate could NEVER be true — the wait would always time out.

It is fine only because `CopyToClipboardButton.jsx`
(`src/[fsd]/shared/ui/button/CopyToClipboardButton.jsx`) spreads
`data-testid={dataTestId}` onto the inner `BaseBtn`, whose only child is
`<Typography>{value}</Typography>`; the label `Typography` is a **sibling**
inside the outer Box. So `innerText` is the bare value.

**Reviewer procedure:** open the shared component and find the JSX node the
`data-testid` prop lands on, then read that node's children. One hop. Shared
components under `src/components/` and `src/[fsd]/shared/` routinely take a
testid as a prop and place it somewhere other than the outermost element.

Related nuance: a JS predicate reading `innerText` (visibility-sensitive) beside
a page object reading `text_content()` (raw) is a safe asymmetry — a hidden
element makes the predicate time out loudly rather than let a stale value pass.

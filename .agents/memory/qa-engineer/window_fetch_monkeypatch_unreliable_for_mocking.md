---
name: window.fetch monkey-patch unreliable for mocking network failures
description: browser_evaluate window.fetch override with a call-counting guard let the first mocked POST through to the real backend once (ELITEA-2000); a version that always mocks + explicit clear worked. Prefer native page.route() for real Playwright tests regardless.
type: feedback
---

During ELITEA-2000 analysis (Skill "Build with AI" create-failure case),
used a `browser_evaluate` `window.fetch` monkey-patch to simulate a create
API failure — the standard technique this suite's analysts use when no
native `page.route()` is available in the exploration tool (see
ELITEA-1916/1915's AFSs for the same pattern on the Agent entity).

First attempt used a call-counting guard:
```js
window.__count = 0;
window.fetch = async (input, init) => {
  if (isCreateSkillPost(input, init)) {
    window.__count += 1;
    if (window.__count === 1) return mocked500Response;
  }
  return origFetch(input, init);
};
```
Clicking "Create Skill" unexpectedly reached the REAL backend and created a
genuine Skill instead of hitting the mocked failure — root cause not fully
isolated (possibly a request racing the evaluate() install, or the SPA
firing more than one POST attempt in a way the naive counter mis-tracked).

**Fix that worked:** a version with NO counter — always return the mocked
500 for every matching POST — followed by an explicit
`window.fetch = window.__origFetch` restore before the retry click. This
gave clean, deterministic single-call interception both times (mock then
real).

**Takeaway for exploration:** if a `window.fetch` monkey-patch with a
call-counting/one-shot guard doesn't reproduce the expected failure on the
first try, don't assume the product is fine — try an "always mock, then
explicitly restore" version before concluding. **Takeaway for automation:**
this fragility is a property of the ad hoc monkey-patch technique only —
the real Playwright test must use native `page.route()`/`page.unroute()`
(as `mock_generate_failure`/`mock_generate_success` in
`generate_entity_modal_page_base.py` already do), which intercepts at the
browser/protocol level and does not share this flakiness.

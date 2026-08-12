---
name: Playwright post_data_json returns None — use route() interception
description: response.request.post_data_json / Page.expect_request's post_data_json return None for small fetch()-dispatched PUT/POST bodies in this project's Chromium 149, despite a real Content-Length — use page.route() to read the body before it leaves the browser
type: feedback
---

Confirmed live (ELITEA-2347, `test_secret_edit_value_name_field_readonly.py`),
headed AND headless, this project's actual `pytest.ini`-launched Chromium 149:
reading a request's JSON body via `response.request.post_data_json` (read
post-hoc, after the response resolves) OR via `Page.expect_request(...).value
.post_data_json` (read right after the request event fires) both reliably
returned `None` for a small (`Content-Length: 34`) `PUT` body, even though the
header proves a body was sent. Not a product defect — a CDP-level Playwright
limitation reading `postData` back off a completed/in-flight request for this
kind of `fetch()`-dispatched call.

**Fix: use a temporary `page.route()` interceptor** — it reads the body
BEFORE the request leaves the browser, which is unaffected:

```python
captured: dict = {}
route_pattern = "**/secrets/secret/default/**"

def _capture_put_body(route):
    if route.request.method == "PUT":
        captured["post_data_json"] = route.request.post_data_json
    route.continue_()

page.route(route_pattern, _capture_put_body)
try:
    with page.expect_response(_is_edit_save_response, timeout=timeout) as resp_info:
        save_button.click()
finally:
    page.unroute(route_pattern, _capture_put_body)
```

Route pattern should be as narrow as the endpoint allows; filter by method
inside the handler (route matches ALL methods on that URL, e.g. GET reveal +
PUT edit + DELETE cleanup share the same singular-secret URL shape here) and
always `route.continue_()` regardless, so no request is ever blocked.

If a future case needs to assert a request body and reaches for
`response.request.post_data_json` first (the obvious API), expect it to
silently return `None` here — reach for `page.route()` from the start instead
of losing a debug cycle rediscovering this.

**Addendum (ELITEA-2434, PR #1446 fix round 1):** a payload-capturing helper
that uses ONLY `page.route()` (no `expect_response` wrapper) has no way to
return the response status — and a reviewer/AFS coverage-map check WILL
demand that status assertion later (e.g. "create-flow POST returns 201").
Combine both from the start, as the snippet above already shows — don't add
`page.route()` alone and assume a later round can bolt status capture onto
the same click without a second listener. Fix was to wrap the existing
`save_and_wait_for_navigation()` call in
`with page.expect_response(predicate, timeout=timeout) as response_info:`
and read `response_info.value.status` after — both listeners fire off the
same click, no duplicated network wait.

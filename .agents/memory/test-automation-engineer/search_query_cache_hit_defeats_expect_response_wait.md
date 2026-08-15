---
name: Search query cache hit defeats page.expect_response() wait
description: Re-typing a search value already fetched this session (or clearing back to the page's initial no-query state) can be served from the query-client cache with ZERO new network round-trip — page.expect_response() then hangs to timeout. Wait on UI state for that one transition instead.
type: feedback
---

## What happened (ELITEA-2163/2164/2165/2463, chat search gap-family)

Chat's conversation search (`Conversations.jsx` / `useQueryFoldersList.hooks.js`,
`GET .../elitea_core/folder/prompt_lib/{projectId}?query=<value>&grouped=true`)
is backed by a query-client cache keyed on the query string. Two shapes hit
this trap, both producing a real `playwright._impl._errors.TimeoutError:
Timeout ... waiting for event "response"` — not a product bug, an
implementation-time infrastructure miss:

1. **Re-querying an EXACT value already fetched earlier in the same test.**
   Typed `"un"` in step 3, later re-typed `"un"` again as a "restore state"
   step before a subsequent step — the second `type_conversation_search_
   query("un", ...)` call's `page.expect_response(lambda r: f"query={query}"
   in r.url)` hung, because the cache served the already-fetched result
   instantly with no new request. **Fix: don't re-query a value you've
   already fetched — restructure so the next step's own query call replaces
   the current value directly (it doesn't matter what the field held right
   before).**
2. **Clearing the field back to the page's INITIAL no-query state**
   (`Meta+a` + `Backspace` down to empty). This returns to the exact same
   cache key `navigate_to_chat()` populated on page load — the debounced
   `isSearchMode` flips false and the app can render straight from cache.
   **Fix: don't wrap this specific transition in `page.expect_response()`
   at all — wait on the resulting UI state instead** (a polling check like
   `is_conversation_in_group()`/`.wait_for(state="visible")`, run BEFORE
   any non-polling `.count()` read so the DOM has actually settled).

**Every OTHER query transition in this family (narrow value, broader-but-
never-fetched-before value, exact full name) DID fire a fresh response and
stayed correctly request-waitable** — this is not "never wait on
`expect_response` for search," it's specifically "a value identical to
something already cached this session is not a safe wait target."

Self-check before trusting `page.expect_response()` on ANY query-string
transition in an app with client-side query caching: has this EXACT value
(or its equivalent "no query" form) already been fetched earlier in the same
test/session? If yes, wait on UI state instead.

See also: `test-specs/chat-interface/_surface.md` § "Search gap-family" for
the full live-confirmed mechanism, and
`never_assume_a_transition_settled.md` for the broader "name the real
signal" principle this is an instance of.

# Artifacts surface — exploration digest

Handle cache for the Artifacts feature (`/artifacts`), built up across analyst
runs. **Not a source of truth** — verify a handle as you use it; treat a stale
entry as a prompt to look at the app, not as a fact. One writer at a time
(units run serially); the current writer updates this file directly.

## Confirmed handles (as of ELITEA-1811/1814 analysis, 2026-08-02)

| Element | Testid / handle | Where | Notes |
|---|---|---|---|
| Buckets page heading | `artifacts-buckets-heading` | `ArtifactsPage.wait_for_page_load()` | |
| Create-bucket icon | `artifacts-create-bucket-button` | `click_create_bucket_button()` | full page nav to `/artifacts/create-bucket`, not a modal |
| Bucket name field | `artifacts-bucket-name-input` | `fill_bucket_name()` | pre-filled `"new-bucket"` on fresh load; `aria-invalid` flips `"true"` only after blur or Save-click (NOT immediately on type — Formik `touched` gates it) |
| Save button (New Bucket form) | `artifacts-bucket-save-button` | `bucket_save_button` field | **never carries a `disabled` attribute for an invalid-but-nonempty, ≤56-char name** — its `disabled` prop only checks `isCreating/isUpdating/!name/name.length===0/name.length>56`, never the regex (`CreateBucket.jsx:292-298`). For the happy path, `click_bucket_save_button()` wraps the click in `page.expect_response` for the `POST .../artifacts/buckets` — **do not reuse that helper for an invalid name**, no request ever fires and it hangs for its timeout. |
| Bucket name validation rule | n/a (client-side yup) | `CreateBucket.jsx:22-30` | `^[a-zA-Z][a-zA-Z0-9-]*$`, max 56 chars; single shared error message `"Name should start with a letter and contain only letters, numbers, and hyphen"` for EVERY violation of the regex (leading digit, `$`, `_`, space — all produce byte-identical text) |
| Inline validation message | **testid needed: `artifacts-bucket-name-helper-text`** | not yet added | MUI `<TextField>` helperText renders NO `data-testid` today; fix shape: `FormHelperTextProps={{ 'data-testid': 'artifacts-bucket-name-helper-text' }}` (or `slotProps.formHelperText`, precedent: `GenerateSkillReviewForm.jsx`) |
| "Click 'Artifacts'" (return nav) | no testid — use `ArtifactsPage.navigate_to_artifacts()` (direct URL nav) | n/a | Sidebar nav entries (`SidebarBody.jsx`/`SidebarMenuItem.jsx`) are a SHARED component with NO `data-testid` on any item; threading one through is out of proportion to a single-click case need (confirmed independently by both ELITEA-1809 and ELITEA-1811/1814 analysis) |
| Bucket-not-in-list check | `ArtifactsPage.bucket_exists(name)` | pre-existing, raw `get_by_text` (tech debt #25/#42) | reused as-is, not a new handle |

## Known gotchas
- **Formik `touched` gating**: typing alone never reveals a validation error
  in this form — only blur or submit-attempt sets `touched.name = true`,
  which the `error`/`helperText` render both depend on. Don't assert
  `aria-invalid` immediately after `fill_bucket_name()`; assert it after the
  Save click (or a deliberate blur).
- **Invalid-name Save click produces NO network request at all** (yup blocks
  `formik.onSubmit` client-side) — this is distinct from ELITEA-1809's
  duplicate-name case, which DOES reach the server and gets a 400. Don't
  wait on a response for the invalid-name path.
- MCP Playwright server (`.mcp.json` → `playwright`) was not reachable via
  `ToolSearch` in this session — fell back to a direct
  `playwright.sync_api` Python scratch script driving `ArtifactsPage`
  methods directly. If this recurs, flag it — may indicate the MCP server
  needs a restart/reinstall, not just a one-off hiccup.

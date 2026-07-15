---
name: Toolkit/MCP creation form quirks
description: Shared schema-driven ToolBaseProperty.jsx renderer behind every toolkit/MCP/application create form; testid naming already in place; click-locator-ambiguity gotcha on type-selector cards
type: reference
---

Discovered while analyzing ELITEA-1922 (Create Remote MCP — All Fields Populated), 2026-07-15.

## Shared component — testids already exist, reuse before adding

`/mcps/create/mcp`, `/toolkits/create/*`, and `/applications/create/*` (and their
matching detail pages) all render fields through the SAME schema-driven component:
`EliteaUI/src/[fsd]/features/toolkits/ui/form/ToolBase/ToolBaseProperty.jsx`. It
switches on each schema property's `type` (string/integer/boolean/object/array/secret/…)
and renders a different underlying input per branch. As of PR `EliteaAI/EliteaUI#554`
(testids/ELITEA-1922-remote-mcp-form → main, draft; already live on
`automation/testids`), the following DYNAMIC testids exist for ANY toolkit type
sharing this renderer — check before adding a duplicate:

- `toolkit-field-{k}-input` — default text/integer branch (e.g. `toolkit-field-url-input`,
  `toolkit-field-client_id-input`, `toolkit-field-timeout-input`, `toolkit-field-cache_ttl-input`)
- `toolkit-field-{k}-editor` — object/JSON branch, CodeMirror-based (e.g.
  `toolkit-field-headers-editor`); testid lands on the wrapping `<Box>`, not CodeMirror's
  internal DOM — interact via `.locator('.cm-content')` for typing
- `toolkit-field-{k}-checkbox` — boolean branch (e.g. `toolkit-field-enable_caching-checkbox`,
  `toolkit-field-ssl_verify-checkbox`); testid lands on the MUI `<span>` wrapper (click
  works directly on it) — chain `.locator('input')` for `.checked` assertions
- `toolkit-field-{k}-input` — secret/array branches also route through this dynamic
  pattern via `SecretManagementInput`/`ArrayFieldInput`'s new `testId` prop; the Client
  Secret testid lands on the outer container `<Box>` (MUI TextField root), not the
  native `<input>` — chain `.locator('input')`

`k` is the exact JSON-schema property key (confirmed from the actual persisted Raw
JSON, not the UI label — e.g. Client Secret's schema key is `client_secret`, NOT
`api_key` even though the underlying `SecretField.jsx` hardcodes
`inputProps={{ name: name || 'api_key' }}` as an internal HTML `name` default).

Also shared and already testid'd:
- `toolkit-type-card-{itemKey}` — the type-selector cards on `/mcps/create`,
  `/toolkits/create`, `/applications/create` (`CategoryItemCard.jsx`); Remote MCP's
  `itemKey` is `mcp`
- `toolkit-form-name-input` / `toolkit-form-description-input` — `NameDescriptionInput.jsx`
- `toolkit-form-view-toggle` / `toolkit-raw-json-view-toggle` — Form/Raw Json toggle
  (`FormViewToggle.jsx`, shared between create AND detail pages)
- `toolkit-form-save-button` — `CreateToolkitToolTabBar.jsx`

## Secret fields never persist plaintext

Any schema field the `isSecretField()` helper routes through `SecretManagementInput`
persists as `{{secret.<32-char-hex>}}` in the Raw JSON — never the literal value, even
though the "Password" view visually accepts/echoes the typed input during entry. This
is intentional (`SecretField.jsx`'s `secretRegex = /^{{secret\.([A-Za-z0-9_]+)}}$/`),
confirmed by the SAME hex id appearing in both the Form view's masked field value and
the Raw JSON reference token after save. Do NOT assert the literal secret value
anywhere post-save; assert the reference-token pattern instead.

## Click-locator-ambiguity gotcha, not a product bug

A `getByText('<label>').first()` click on a `CategoryItemCard` (the type-selector
cards) can silently no-op even though the card has a plain, direct `onClick` (no MUI
ripple/overlay intercept — confirmed via source read, unlike the separate, REAL
Support Assistant launcher click-intercept quirk documented elsewhere in memory). The
`.first()` match resolves to a non-clickable ANCESTOR (the category-section wrapper,
which also contains the label text as a heading), not the actual `<Card>`. Before
filing a "click doesn't work" defect on these cards, retry with a clean, unambiguous
locator (ideally the testid above) in a fresh context — if that works on the first
try, the original finding was locator ambiguity, not a defect.

## Cleanup

`ToolkitAPI.delete_toolkit(toolkit_id)` already exists in `automation/api/client.py`
(`DELETE {ELITEA_API_BASE}/elitea_core/tool/prompt_lib/{project_id}/{toolkit_id}`) —
use it for MCP/toolkit-create test teardown; no new API client code needed. Capture
the created id from the Save response (`POST .../tools/prompt_lib/{project}` → `201`,
body has `id`) or the post-save detail-page URL (`/mcps/all/{id}`).

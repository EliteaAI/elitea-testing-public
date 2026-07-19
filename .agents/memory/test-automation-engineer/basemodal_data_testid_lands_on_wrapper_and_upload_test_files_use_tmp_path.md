---
name: BaseModal data-testid lands on MuiDialog-root wrapper; upload test files use tmp_path
description: EliteaUI's shared BaseModal component's data-testid prop lands on the outer MuiDialog-root/MuiModal-root ancestor div, not the [role="dialog"] Paper — confirmed useful for scoping. Plus the confirmed project convention for upload-test files is pytest tmp_path, not a checked-in fixtures directory.
type: feedback
---

## BaseModal `data-testid` placement (EliteaUI `src/[fsd]/shared/ui/modal/BaseModal.jsx`)

`BaseModal` accepts a `data-testid` prop and forwards it to the MUI `<Dialog
data-testid={dataTestId}>` element. Live-confirmed (ELITEA-1832, via
`document.querySelector('[data-testid="..."]')` in the browser): this lands
on the **`MuiDialog-root`/`MuiModal-root` wrapper div** (`role="presentation"`),
which is an ANCESTOR of the actual `[role="dialog"]` Paper element — not the
Paper itself. This is still fully usable for scoping (it wraps everything
inside, including the Paper), and Playwright's `.wait_for(state="visible"/"hidden")`
on it works correctly for open/close assertions (confirmed: the whole
`MuiDialog-root` div is removed from the DOM when the dialog closes, no
stale mounted-hidden residue for this component). Don't expect the testid
to land directly on `[role="dialog"]` when auditing/debugging — check the
ancestor chain instead of assuming forwarding failed.

Also: when a `BaseModal` consumer passes its own custom `actions` JSX
(rather than relying on BaseModal's built-in cancel/confirm button
rendering), BaseModal's `cancelButtonTestId`/`confirmButtonTestId` props are
DEAD for that caller — `renderActions()` returns the custom `actions` node
verbatim and never looks at those props. Add `data-testid` directly on the
caller's own `Button.BaseBtn` elements instead. Both `UploadPathDialog.jsx`
and `DuplicateResolutionDialog.jsx` are in this category.

## Upload-test file convention: `tmp_path`, not checked-in fixtures

No `automation/fixtures/files/` (or equivalent) directory exists anywhere in
this repo for file-upload test fixtures. Confirmed by reading
`test_chat_interface.py::test_attach_files_button_sends_file_with_message`
and `test_support_assistant_smoke.py` — both create the file on the fly via
pytest's built-in `tmp_path` fixture (`tmp_path / "name.ext"` +
`.write_text()`/`.write_bytes()`), scoped per-test, auto-cleaned by pytest.
Do this for any new upload test rather than proposing a new checked-in
fixtures directory — grep for `tmp_path` usage in neighbouring upload tests
before inventing a new pattern (from ELITEA-1832; the AFS's own tentative
"confirm the convention first" flag turned out to matter — the suggested
`automation/fixtures/files/` directory does not exist and would have been a
new, unnecessary pattern).

# Test Case: Admin cannot delete themselves from the project

## Metadata
- **TMS ID**: ELITEA-2306
- **Source case**: `.agents/automation/settings-w09/cases/ELITEA-2306.md`
- **Linked Story**: none
- **Priority**: l2 (case frontmatter `priority: high`). **pytest marker: `@pytest.mark.p1`** (if it ever ships).
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` → DEV backend, project 400 "UI Testing")
- **User set**: `${TEST_USER}`
- **Analyst**: test-automation-engineer (combined analyst+implementer slot)
- **Status**: blocked

## Why this is blocked (one paragraph)

The case asserts a guard — "an Admin cannot delete themselves" — whose FIRST
branch is live-disproven and whose SECOND branch cannot be exercised without
risking the destruction of the automation account's only writable project
membership. There is no honest, non-destructive way to reach the observable, so
per `.agents/testing.md` § Fidelity policy ("when the observable cannot be
produced honestly, that is a decision, not a puzzle") this goes to a human
rather than being engineered around.

## What WAS executed and observed live (2026-08-29)

1. Logged in as the acting automation account and opened Settings → Users on
   project 400 (case steps 1-2) — the page renders four rows.
2. Located the acting account's own row (case step 3). Identity confirmed
   independently on Settings → Profile: **Test Bot / `testbot@elitea.ai` /
   User ID 659**, and the Users table shows that same address with role `admin`.
3. Read the state of every row's Delete control (case step 4, first branch):

   | Row | Delete icon rendered | `disabled` |
   |---|---|---|
   | `levon_dadayan@epam.com` (admin) | yes | **false** |
   | `testbot@elitea.ai` (admin — **the acting user**) | yes | **false** |
   | `elitea-batch-edit-test2-70fda701@example.com` (viewer) | yes | false |
   | `elitea-batch-edit-test2-45c8fb8d@example.com` (editor) | yes | false |

   **The admin's own row offers an enabled Delete icon, identical to every
   other row.** Source agrees: `UsersTable.jsx` `renderActions` renders
   `DeleteUserButton` behind `checkPermission(PERMISSIONS.users.delete)` only —
   there is no self-row condition anywhere, and `DeleteUserButton`'s own
   `disabled` prop is never passed at the row call site.
4. Grepped the whole EliteaUI source for any self-deletion guard string
   (`delete yourself` / `cannot delete your` / `remove yourself` / `self-delete`,
   case-insensitive): **zero hits**.

So the case's first branch ("the Delete icon is disabled") is **false in the
product today**, verified two ways (live DOM + source).

## Blocked Steps

- **Case step 4, second branch — "a confirmation error appears when attempting
  self-deletion" — CANNOT BE PRODUCED SAFELY.**

  Exercising it means clicking Delete on the acting account's own row and
  confirming. Two outcomes, and there is no way to know which without doing it:

  - the backend rejects it → an error toast, the case passes; or
  - the backend accepts it → **`testbot@elitea.ai` loses its `admin` membership
    of project 400.**

  The second outcome is unrecoverable by any agent. Project 400 is the *only*
  project where this account holds `admin` (surface digest § Project-topology
  constraint — verified across projects 471 / 406 / 25, where it is a viewer and
  the Users page renders no action controls at all). Losing it removes the
  account's ability to re-invite itself, takes every Users-surface test in the
  suite with it, and needs a human admin (`levon_dadayan@epam.com`) to restore.

  No safe proxy exists:
  - a *seeded* disposable admin cannot be used — an invited user has no
    credentials, so no session can act as them;
  - the API route is the same identity and the same request;
  - another project cannot host the attempt — the account lacks
    `users.delete` there, so a 403 would answer a different question;
  - the backend's OpenAPI (`/shared/openapi/?all=true`) is auth-gated behind
    the DEV OIDC redirect and could not be read to settle it statically.

- **Case step 5 — "Verify the Admin remains in the table"** is only meaningful
  after step 4's attempt, so it inherits the same block.

## The decision a human needs to make

Which of these is true?

- **(a) The guard is a real requirement and the product is missing it** — then
  #-file a product bug ("an admin can delete themselves out of a project, with
  no guard in the UI and none found in the source"), and the automated test
  asserts the *correct* behaviour with `expect.soft()` + a defect link, i.e.
  sanctioned-RED. Confirming that requires someone with a disposable admin
  account to run the attempt once.
- **(b) Self-removal is intentional** (leaving a project is a normal action) —
  then the **case text is wrong** and should be rewritten or retired, and this
  AFS is closed as `out-of-scope-by-author`.

Either way the deciding evidence is one destructive attempt on an account the
factory can afford to lose. That is a human's call, not an agent's.

## Coverage Map

**Axis 1 — Source-case elements:**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Log in as Admin role | User is authenticated and lands on the expected landing page | executed live | — | executed, not automated (blocked case) |
| 2 Navigate to Settings → Users | Target page/section loads successfully | executed live | — | executed, not automated |
| 3 Locate your own user row | Action completes without error | executed live — identity cross-checked on Settings → Profile | — | executed, not automated |
| 4 Verify the Delete icon is disabled OR a confirmation error appears when attempting self-deletion | Condition holds as described | **branch 1 disproven live; branch 2 unreachable** | — | **blocked** |
| 5 Verify the Admin remains in the table | Condition holds as described | depends on step 4 | — | **blocked** |
| Expected Final State: the Admin remains in the table | (restates step 5) | depends on step 4 | — | **blocked** |

**Axis 2 — Analyst additions:** none. Nothing is added to a case that cannot be
executed.

## Concrete Handles (discovered during exploration)

Recorded so whoever unblocks this does not re-derive them — every handle the
case needs already exists, so the block is purely about product behaviour, never
about tooling:

| Element | Testid | Provenance (verified 2026-08-29) |
|---|---|---|
| User row / Email cell | `user-row` / `user-column-value-email` | pre-existing |
| Row Delete (trash) icon | `user-row-delete-button` | pre-existing |
| Confirmation dialog / Delete / Cancel | `delete-confirm-dialog` / `delete-confirm-button` / `delete-confirm-cancel-button` | pre-existing shared |
| Error toast | `toast-alert` (+ `data-severity="error"`) / `toast-message` | pre-existing shared |

**No new testid is needed.** The acting account's own row would be resolved at
runtime from its profile (Settings → Profile renders the email), never
hardcoded.

## Known Defects Found During Exploration
None filed — whether the missing guard IS a defect is exactly the question
above, and filing it as a bug before that is answered would assert a contract
nobody has confirmed.

## Automation Hints (for whoever unblocks this)
- The acting account's own row must be derived at runtime (read the email off
  Settings → Profile, then match the row), never hardcoded — the automation
  identity is env-driven.
- If the answer is (a), the shape is: assert the enabled-icon reality, attempt
  the delete, soft-assert the error toast + the row's survival with
  `# Known defect: #N`.
- If the answer is (b), retire the case rather than inverting the assertion —
  a test that proves an admin CAN delete themselves is a different case with a
  different name.

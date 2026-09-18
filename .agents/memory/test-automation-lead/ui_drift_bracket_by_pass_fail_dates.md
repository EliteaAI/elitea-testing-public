# UI-drift triage: bracket EliteaUI `main` by last-green / first-red nightly, then `git log -S` the gate line

When a merged spec goes red on DEV and promotion-gap checks are null (spec byte-identical main↔base, testid on main), get the last-passing and first-failing DEV Stable run dates (sibling `[FIX]`/question cards often already tabulate them — #2327 did), then in `../EliteaUI`:

    git log --since=<last-pass> --until=<first-fail> --format='%h %ci %s' origin/main -- <component paths>
    git log -S"<the exact gate/condition line from the component>" origin/main -- <file>

The `-S` on the condition line (e.g. `isForked && isOnApplicationsPage`) names the introducing PR in one command; its PR body usually states the intent verbatim — that sentence is what decides A-adjust vs B-bug, and it belongs quoted in the question card. Verified 2026-09-17 on #2343/ELITEA-2051 → EliteaAI/EliteaUI#996 (EL-6612).

Caveat learned the same day: a grep hit in a component is not proof it renders — `DataTableRow.jsx` still had the icon but is dead code (`DataTable.jsx` mounts `GridTableRow`). Confirm the mounted path (analyst can read the React fiber's component props live) before citing a call site as "still shown".

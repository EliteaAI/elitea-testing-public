# Batch report: skills-run-own-skill-4634

**Totals:** 1 case, blocked: 1

| Case | Outcome | Note |
|---|---|---|
| ELITEA-4634 | blocked | review/fix round 1 failed |

## Findings

### clarification (2)

- Case text step 4 says Run creates a new chat. On DEV, Run (table-row menu) opens /skills/all/{id}?focus=run with the skill test panel. Steps 2, 4-8 and 14 are stale (no card play icon, no participants panel, empty placeholder, run not in the Chats list). The TMS case text should be fixed. The AFS asserts the live contract. (ref: `ELITEA-4634`)
- The case text disagrees with live DEV on where Run lives (table-row menu, not a card icon), on where it leads (skill detail and test panel, no new chat) and on the input placeholder (empty). The test asserts the live contract. The TMS case text needs correcting on the TMS side. No bug was filed, which is correct per the reverse-masking guard. (ref: `ELITEA-4634`)

### note (10)

- The corner platform banner overlays the test-panel send button on DEV. A force click lands on the banner and silently does not send. Dismiss platform-banner-close first. SkillDetailPage.send_test_message does not do this today.
- The branch tests/ELITEA-4634-run-own-skill already has implementation commit cc75c747. Checking out the trunk for this dispatch was done as instructed, and nothing there was altered.
- The checkout has no automation/.env.test and no APP_PREFIX in the shell, so the framework builds URLs without /app and DEV returns a 404 page. I ran with APP_PREFIX=/app on the command line. The lead's gate runs need the same.
- After page.reload() on /skills/all/{id}?run=<convId>, the skill test panel is aria-hidden. It has to be opened with open_test_skill_panel(), after which both messages restore. The AFS says reload restores them but not that the panel must be reopened.
- SkillsListPage.skill_exists_in_list is a point-in-time check. Right after navigate() it returned False for the new skill, so the spec waits on the card with expect(...).to_have_count(1) instead.
- The AFS Automation Hints suggest the TMS file name ELITEA-4634_..., but the real file is ELITEA-4634_run-own-skill-from-skills-page.md. Reviewers can use it for the TMS link check.
- `ruff` is not installed in the repo .venv, so the documented lint step could not run.
- Mechanical locator grep on `git diff main...HEAD -- pages tests` returned one hit, in the spec: `expect(page.locator(chat.PARTICIPANT_CATALOG_TAG)).to_have_count(0)`. It is compliant, because `PARTICIPANT_CATALOG_TAG` is an UPPER_CASE class constant defined as `'[data-testid="chat-participant-catalog-tag"]'` (chat_page.py:7034). No `locator=`, `fallback=` or `.nth(` was added. The new declarations… [clipped; full text in the unit's receipt under .agents/automation/_returns/]
- Steps 3 and 7 of the case (no Catalog badge, participant with version badge) are asserted only through a vacuous count-0 check on `chat-participant-catalog-tag`. The participants panel does not exist in this view. The AFS declares this as a clarification, so this is not blocking. Step 14 (chat in the Chats list) is correctly not asserted. The AFS says skill-source runs are not listed, and persiste… [clipped; full text in the unit's receipt under .agents/automation/_returns/] (ref: `AFS Clarifications 1-5`)
- TMS pair check: `@pytest.mark.tms("ELITEA-4634")` and `@allure.issue` are both present on the single test. The link file name `ELITEA-4634_run-own-skill-from-skills-page.md` exists in the sibling TMS clone under skills/. Every step is wrapped in `allure.step`. Cleanup is in `finally` and deletes both the conversation and the skill, with the conversation id taken from `?run=`. I did not run `tms_ba… [clipped; full text in the unit's receipt under .agents/automation/_returns/]

### defect (2)

- The Step 6 reply check is `assert "HELLO WORLD" in reply.upper()`. This passes if the skill echoes the input lowercase, so it cannot detect a failed uppercase conversion. That is the one thing the case exists to prove (expected 'HELLO WORLD'). The AFS wording 'case-insensitive' was meant to allow surrounding whitespace and punctuation, not to ignore case. Fix: `assert "HELLO WORLD" in reply`. The … [clipped; full text in the unit's receipt under .agents/automation/_returns/] (ref: `automation/tests/ui/skills/test_own_skill_run_message_exchange.py:Step 6`)
- DEV (https://dev.elitea.ai/app) serves the 404 'Page Not Found' page for the skills routes (/skills/all). Two skills specs go red at the first navigation step: ELITEA-4634 on HEAD, and the catalog-run spec on `catalog-page-heading`. The failure is not isolated to this case. Check the DEV deployment or whether the skills route was moved before the gate runs. (ref: `automation/screenshots/test_run_own_skill_and_exchange_message_FAIL_20261111_165444.png`)

## Gate

No gate verdict (gate: null); no timings recorded.

AFS: `test-specs/skills/l1_run-own-skill-from-skills-page-and-message-exchange_ELITEA-4634.md`  
Branch: `tests/ELITEA-4634-own-skill-run`

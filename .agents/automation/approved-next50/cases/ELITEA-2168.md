---
id: ELITEA-2168
title: "Chat – Team Project – Add Multiple Users, Mention User, View User List and Remove Users from Conversation"
priority: high
type: functional
module: chat-interface
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:chat]
requirements: []
---

# ELITEA-2168: Chat – Team Project – Add Multiple Users, Mention User, View User List and Remove Users from Conversation

**Module:** chat-interface · **Priority:** high · **Type:** functional

**Objective:** Verify the complete flow of adding multiple users with deselection, mentioning users, using @Everyone, and removing users via the PARTICIPANTS dropdown.

---

## Preconditions

- User is logged in to the Elitea platform.
- User is in a Team project with an existing conversation that has participants.

---

## Test Data

| Field | Value |
|-------|-------|
| Users | user_1, user_2, user_3, user_4 | Mention | @Test Bot hi | @Everyone message | @Everyone hi |

---

## Steps

| # | Action | Expected Result |
|---|--------|--------------------|
| 1 | Open a conversation in Team project with existing participants | PARTICIPANTS USERS section visible |
| 2 | Open Invite Users modal and select user_1, user_2, user_3, user_4 | Four user chips shown |
| 3 | Click X on user_4's chip to deselect | user_4 removed from chips; user_1/2/3 remain |
| 4 | Click Add; verify user_1/2/3 added to PARTICIPANTS | Three users added |
| 5 | Verify USERS section shows first 5 avatars and +N indicator for additional users | +N indicator shown |
| 6 | Open Invite Users again, select user_4, click Cancel | Modal closes; user_4 not added |
| 7 | Type '@Test Bot hi' and send | Message sent; notification badge appears; no LLM response generated |
| 8 | Click the USERS avatar group to open dropdown; hover over Admin Bot; click delete icon | Remove user? modal appears |
| 9 | Click Remove in the modal | Admin Bot removed from dropdown and PARTICIPANTS |
| 10 | Hover over user_1 and click delete; click Cancel | Modal closes; user_1 not removed |
| 11 | Click 'All users' at bottom of dropdown; verify @Everyone inserted in message field | @Everyone mention highlighted |
| 12 | Type 'hi' and send '@Everyone hi' | Message sent; all participants receive notification; no LLM response |

---

## Expected Final State

Multiple users managed correctly; @mention and @Everyone work; removal via confirm dialog works.

---

## Pass/Fail Criteria

**Pass:**
- All steps complete without errors.
- All user management flows work correctly.

**Fail:**
- Any step produces an error or unexpected result.
- User add/remove fails or mentions don't work.

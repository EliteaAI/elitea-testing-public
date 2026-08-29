"""Unit tests pinning WHERE the conversation id is read back for teardown.

Regression coverage for the review finding on PR #1994 (ELITEA-2416,
``tests/ui/settings/test_chat_error_invalid_llm_credential.py``): the spec's
``finally`` deletes the conversation the chat step creates, but the id it needs
was captured only at the END of the ``try`` block::

    chat.send_message(CHAT_MESSAGE)     # <- the conversation is CREATED here
    ...                                 # steps 7, 8, 9 -- any of these can raise
    match = CONVERSATION_URL_PATTERN.search(page.url)
    if match:
        conversation_id = int(match.group(1))     # <- id captured only HERE
    finally:
        if conversation_id:
            conversation_api.delete_conversation(conversation_id)

``.agents/testing.md`` § Teardown-guard ordering is usually read as "set the
boolean flag before the mutating click", but the rule binds any value teardown
NEEDS -- most often an id read out of a URL or a response. Between the send and
the late capture sit step 7's 90 s Socket.IO frame wait and step 8's 10 s
message-count wait, both on the documented flake-prone chat path: every failure
there left an orphan conversation in the shared test user's list, feeding the
``#1082`` pollution the spec's own AFS says not to add to. And, exactly like the
PR #1989 finding this file's sibling pins, the leak is invisible to the merge
gate -- it only happens on the runs that already failed.

These tests are static (AST over the spec source) rather than behavioural,
because the defect is a statement-ordering shape, not a value: parsing the file
is enough, no browser and no live app. They fail against the pre-fix
ELITEA-2416 source and pass after it.

The rule is checked from both ends:

1. The send that creates the conversation must be followed IMMEDIATELY by the
   ``conversation_id`` read-back (no window at all between mutation and capture).
2. The ``finally`` must re-derive the id when it is still ``None``, before it
   deletes -- so a send that navigated late (or a read-back that came back
   empty) still gets cleaned up rather than silently skipped.
"""

from __future__ import annotations

import ast
from pathlib import Path

SETTINGS_TESTS_DIR = Path(__file__).resolve().parents[1] / "ui" / "settings"

#: The chat-error spec (settings-w11, ELITEA-2416) whose chat step creates a
#: conversation on the shared test user and owes it a guarded teardown.
SPEC_NAME = "test_chat_error_invalid_llm_credential.py"

#: The variable the ``finally`` deletes by.
ID_NAME = "conversation_id"

#: The call that CREATES the conversation: the first message send is what turns
#: a blank composer into a persisted ``/chat/{id}``.
MUTATING_METHOD = "send_message"

#: The teardown call the captured id feeds.
DELETE_METHOD = "delete_conversation"


def _parse() -> ast.Module:
    path = SETTINGS_TESTS_DIR / SPEC_NAME
    assert path.is_file(), f"chat-error spec not found: {path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _statement_blocks(tree: ast.Module) -> list[list[ast.stmt]]:
    """Every ``body``-like list of statements in the module.

    Statement adjacency only means anything within one block, so the checks
    below walk blocks rather than the flat node stream: ``with allure.step(...)``
    nesting must not make two statements look adjacent when they are not.
    """
    blocks: list[list[ast.stmt]] = []
    for node in ast.walk(tree):
        for field in ("body", "orelse", "finalbody"):
            value = getattr(node, field, None)
            if isinstance(value, list) and value and all(isinstance(item, ast.stmt) for item in value):
                blocks.append(value)
    return blocks


def _called_method(statement: ast.stmt) -> str | None:
    """The method this statement calls, if it is a bare or assigned call."""
    if isinstance(statement, ast.Expr):
        call = statement.value
    elif isinstance(statement, ast.Assign):
        call = statement.value
    else:
        return None
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
        return None
    return call.func.attr


def _assigns_conversation_id(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.Assign) and any(
        isinstance(target, ast.Name) and target.id == ID_NAME for target in statement.targets
    )


def test_conversation_id_is_read_back_immediately_after_the_send() -> None:
    """No statement may sit between the send and the ``conversation_id`` capture.

    This is the exact PR #1994 finding. Anything in that window is a path on
    which a failure leaves the ``finally`` with no id to delete by, while the
    conversation itself already exists on the shared user.
    """
    tree = _parse()
    sends = [
        (block, index)
        for block in _statement_blocks(tree)
        for index, statement in enumerate(block)
        if _called_method(statement) == MUTATING_METHOD
    ]
    assert sends, (
        f"{SPEC_NAME}: no {MUTATING_METHOD}() call found -- this spec sends a chat message, "
        "which is what creates the conversation its teardown deletes."
    )

    for block, index in sends:
        send_line = block[index].lineno
        following = block[index + 1] if index + 1 < len(block) else None
        assert following is not None and _assigns_conversation_id(following), (
            f"{SPEC_NAME}: the send at line {send_line} is not immediately followed by a "
            f"`{ID_NAME} = ...` read-back (found: "
            f"{'end of block' if following is None else ast.dump(following)} at line "
            f"{send_line if following is None else following.lineno}). Sending the first message "
            "CREATES the conversation, so every statement between the send and the capture -- the "
            "90 s error-frame wait and the message-count wait among them -- is a path on which the "
            "`finally` has no id to delete by and orphans a conversation on the shared test user "
            "(#1082)."
        )


def test_teardown_re_derives_the_id_before_deleting() -> None:
    """The ``finally`` must have a last-chance read-back ahead of the delete.

    Guards the other half: the read-back at the send is deliberately
    non-raising, so it can legitimately come back ``None`` (the app navigated
    late, or the send failed after the conversation was created server-side).
    Without a re-derive in ``finally`` those runs skip the delete silently --
    the same leak by a different route.
    """
    tree = _parse()
    finalbodies = [node.finalbody for node in ast.walk(tree) if isinstance(node, ast.Try) and node.finalbody]
    assert finalbodies, f"{SPEC_NAME}: no try/finally found -- the teardown block is missing entirely."

    for finalbody in finalbodies:
        deletes = [
            node.lineno
            for statement in finalbody
            for node in ast.walk(statement)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == DELETE_METHOD
        ]
        if not deletes:
            continue
        re_reads = [
            node.lineno
            for statement in finalbody
            for node in ast.walk(statement)
            if _assigns_conversation_id(node)
        ]
        assert re_reads and min(re_reads) < min(deletes), (
            f"{SPEC_NAME}: the `finally` calls {DELETE_METHOD}() at line {min(deletes)} without "
            f"re-deriving `{ID_NAME}` first (assignments found in the finally block: "
            f"{re_reads or 'none'}). The read-back at the send is non-raising by design, so the "
            "teardown owes a last chance to recover the id from the URL before it gives up on a "
            "conversation that does exist."
        )

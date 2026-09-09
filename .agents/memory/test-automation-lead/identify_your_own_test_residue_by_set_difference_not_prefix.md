---
name: Identify your gate's own leaked test data by SET DIFFERENCE, never by name prefix
description: Snapshot the collection before and after the gate and diff — prefix-matching a generated test name also matches every pre-existing leak from earlier CI runs, turning cleanup into an unauthorized purge
type: feedback
aliases: [cleanup residue, leaked buckets, prefix match, comm -13, before after snapshot, gate cleanup, test data purge]
tags: [area/gate, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

Specs generate names from the test's own node id, so a gate's buckets look like
`autotest-test-create-bucket-via-form-and-<6 digits>`. The obvious cleanup is to
delete everything matching that prefix. On #2084 that prefix matched **44** objects
— 41 of them leaked by *earlier CI runs*, not mine. Deleting them would have been an
unauthorized purge of shared DEV state, done silently, under the banner of tidying up.

Timestamps do not rescue you either: `creationDate` on these rows tracks *listing*
time, not creation, and it moves between two consecutive listings.

## The technique

Snapshot the collection before and after, and diff. It is exact, needs no naming
convention, and cannot reach anything you did not create:

```bash
list > /tmp/before.txt          # sorted names
# ...run the gate...
list > /tmp/after.txt
comm -13 /tmp/before.txt /tmp/after.txt   # exactly what I created -> delete these
comm -23 /tmp/before.txt /tmp/after.txt   # what VANISHED -> must be empty
```

The second `comm` is the half people skip, and it is the one that catches a gate
that *destroyed* shared state. Re-list afterwards and assert the count returns to
baseline: on #2084, 1221 → 1224 → 3 deleted → **1221**, both checks empty.

## Also

Verify the delete endpoint before trusting a 2xx-less response. My first attempt hit
`/artifacts/s3/?name=` and got **405**; the real route is
`{api_base}/artifacts/buckets/default/{pid}?name=<name>` → `200 {"message":"Deleted"}`.
A cleanup that silently 4xxs looks exactly like a cleanup that worked.

Related: [[timeout_raise_on_a_leak_fed_list_has_a_decaying_balance]] · [[a_delivered_card_is_not_verified_until_the_env_ran_it]]

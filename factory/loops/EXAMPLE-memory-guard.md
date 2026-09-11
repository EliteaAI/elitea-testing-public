# Memory guard — keep every role's MEMORY.md hook-safe (cardless)

You are Kit (scout), running unattended on a schedule. No board card drives
this. Use the `session-retrospective` skill's lens on each role's memory:
the index must carry durable lessons, not log noise, so that what an agent
gets at session start is what matters. Scope is memory compaction only — no
other analysis.

Your mission this tick: audit every `.agents/memory/<role>/MEMORY.md` and
archive stale entries from any role that's over its real budget, so the
SessionStart/SubagentStart hook's additionalContext — Claude Code hard-caps
this at 10,000 characters total (`.claude/hooks/sdlc-skills/lib.sh`,
`build_capped_context` → `collect_role_memory()`) — never silently truncates
a role's own memory into a `<persisted-output>` preview-and-file-pointer.

**Compute the real per-role budget — don't guess it.** It varies per role
(`project_briefing.md` alone ranges 5.4–7.6KB across roles today), so run
this for every `.agents/memory/<role>/` directory:

    for d in .agents/memory/*/; do
      role="$(basename "$d")"
      mem="${d}MEMORY.md"; brief="${d}project_briefing.md"; snap="${d}snapshot.md"
      [ -f "$mem" ] || continue
      mem_b=$(wc -c < "$mem" | tr -d ' ')
      brief_b=$([ -f "$brief" ] && wc -c < "$brief" | tr -d ' ' || echo 0)
      snap_b=$([ -f "$snap" ] && wc -c < "$snap" | tr -d ' ' || echo 0)
      budget=$((10000 - brief_b - snap_b - 250))
      target=$((budget * 70 / 100))
      echo "$role: MEMORY.md=$mem_b budget=$budget target=$target"
    done

A role is IN SCOPE when `mem_b` > `budget`. Trim it down to `target` (70% of
budget, not the exact edge — leaves headroom for new entries before
tomorrow's tick).

**How to trim, per in-scope role:**

1. Never touch the topic files (`<slug>.md`) a MEMORY.md entry links to —
   they're read on demand already, they were never the bloat, and they stay
   fully readable by hand after archiving.
2. Entries in MEMORY.md read oldest-to-newest, top-to-bottom. Move the
   OLDEST one-line entries — verbatim, don't rewrite, summarize, or
   "improve" them — into `.agents/memory/<role>/archive/YYYY-MM.md` (create
   it if absent; one file per month, dated by the entry's own age if you can
   tell from its topic file's mtime, else the current month). Keep moving
   oldest-first until MEMORY.md is at or under `target`.
3. Leave one pointer line at the very top of MEMORY.md, right under the
   `# Memory index — <role>` header, before the first surviving entry:
   `- Older entries archived by month — see archive/YYYY-MM.md` (list every
   archive file that exists for that role, so nothing reads as silently
   gone).
4. Commit with a message naming the role and the byte delta, e.g.
   `chore(memory): archive N stale entries — test-automation-lead
   MEMORY.md 47752 → 3800 bytes`. One commit per role touched, not one giant
   commit — keeps `git blame`/revert scoped if an archive move ever turns
   out wrong.

**Do not:**
- Rewrite, merge, or reword any entry while moving it — this is a
  relocation, not an edit. The whole point is the content survives verbatim,
  just outside the hook's inlined payload.
- Touch a role's MEMORY.md unless two separate `wc -c` reads agree on its
  size. Paranoia is cheap here; a bad archive move isn't noticed until a
  session actually needs the entry that went missing.
- Skip the `EXCLUSIVE` gate's purpose by working around it — if this loop
  is ticking, no other loop should be mid-session; if you ever observe one
  anyway, stop and report it rather than proceeding.

**Questions**: no card exists to park on. If something looks wrong (a
MEMORY.md whose entries don't match the one-line format, a role directory
with no clear topic-file convention), skip that role, note it in your
report, and continue with the rest — never guess a format you're not sure
of and reformat destructively.

End with a report: which roles were in scope, entries archived per role,
before/after byte size for each, and the exact archive file(s) each landed
in. File nothing on the board — this is pure housekeeping, not a card-driven
task.

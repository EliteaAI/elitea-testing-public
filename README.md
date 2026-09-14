# Team telemetry (auto-written)

Machine-written usage data: what each AI session cost, which cases it worked
on. Hooks write here; commits go to the \`telemetry\` branch of THIS repo —
never to main.

One subfolder per factory — \`automation/\` is the test-automation factory's;
other factories add their own and ride the same branch and sync.

- Don't edit by hand. Don't commit this folder to main.
- See the team picture:  \`git -C .agents/telemetry pull\`  → then run team-report
- Empty after clone? run:  \`git submodule update --init\`

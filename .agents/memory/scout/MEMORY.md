# Memory index — scout

> Only *preventive* facts are indexed. Daily logs are on disk, read on demand:
> `.agents/memory/scout/daily/YYYY-MM-DD.md`

- [Project briefing](project_briefing.md) — test-automation onboarding: framework, TMS, base branch, merge policy
- [Hook context cap & doc delivery](hook_context_cap_and_shared_doc_delivery.md) — 10k cap; __none__ sentinel; budgets
- [Efficiency-audit gotchas](efficiency_audit_gotchas.md) — externalOk=false is benign; --resolved-from misses wave-*/; sessions date to START
- [Context delivery architecture](context_delivery_architecture.md) — @-imports are the ONLY channel for .agents/*; hook carries memory only
- [Gates are blind to provenance](pipeline_gates_are_blind_to_provenance.md) — substitution passes every check; N×-green gate rewards it; model was not the cause

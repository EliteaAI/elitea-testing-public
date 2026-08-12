---
name: Skill custom icon renders correctly but lacks testid at 3 call sites
description: SkillMenu/SkillCard/MentionSkillList each independently render EliteAImage with no data-testid — check each JSX call site, not just one
type: reference
---

ELITEA-2605 (2026-08-12, live-confirmed): a skill's custom icon (`icon_meta.url`)
renders correctly and consistently across all 5 UI surfaces that show a skill
(list card, detail page, agent SkillMenu attach-dropdown, agent SKILLS-section
SkillCard, chat/instructions `~mention` autocomplete) — no product defect.

But `EliteAImage` (`src/components/EliteAImage.jsx`) DOES accept a `data-testid`
prop — the limitation is entirely at the CALLER. Three separate JSX call sites
each independently implement `icon_meta?.url ? <EliteAImage .../> : <SkillIcon/>`
and NONE of the three passes a testid on either branch:
`SkillMenu.jsx` (agent attach-dropdown item), `SkillCard.jsx`
(`src/[fsd]/features/skill/ui/SkillCard.jsx`, agent SKILLS-section card), and
`MentionSkillList.jsx` (chat `~mention` popper item, feeds into shared
`MentionToolItem.jsx`). Two OTHER call sites of the same icon_meta pattern DO
already have testids: the list-card's `EntityIcon`→`entity-card-icon-img`
(via `Card.jsx`, ELITEA-2428) and the form's own `skill-form-icon-img`
(ELITEA-2602/2604).

Lesson for future icon/avatar-visibility cases on ANY entity (agents, pipelines,
MCPs): a shared image-rendering component accepting `data-testid` does NOT mean
every caller passes one — grep each individual JSX call site
(`icon_meta?.url ? ... : ...` or similar ternaries) rather than assuming "the
component supports it, so it must be wired everywhere." Full detail + exact
fix recommendations:
`test-specs/skills/l2_skill-custom-icon-visibility-across-ui_ELITEA-2605.md`.

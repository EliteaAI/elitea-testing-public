# sdlc-skills per-role hook defaults — GENERATED, do not edit (regenerated on
# every install/update from the agents installed in this repo).
# Presence of this file = roster mode: a role with no per-role variable gets
# NOTHING from the shared hooks. Grant or tune roles in config.sh (sourced
# first, so its lines win), e.g.: : "${SDLC_SHARED_DOCS_MY_AGENT:=profile testing}"
: "${SDLC_SHARED_DOCS_QA_ENGINEER:=${SDLC_SHARED_DOCS:-testing profile conventions role-overrides}"
: "${SDLC_ROLE_MEMORY_FILES_QA_ENGINEER:=${SDLC_ROLE_MEMORY_FILES:-SOUL.md RULES.md snapshot.md MEMORY.md project_briefing.md}}"
: "${SDLC_SHARED_DOCS_SCOUT:=${SDLC_SHARED_DOCS:-testing profile workflow conventions role-overrides team-comms}}"
: "${SDLC_ROLE_MEMORY_FILES_SCOUT:=${SDLC_ROLE_MEMORY_FILES:-SOUL.md RULES.md snapshot.md MEMORY.md project_briefing.md}}"
: "${SDLC_SHARED_DOCS_TEST_AUTOMATION_ENGINEER:=${SDLC_SHARED_DOCS:-testing profile conventions role-overrides}}"
: "${SDLC_ROLE_MEMORY_FILES_TEST_AUTOMATION_ENGINEER:=${SDLC_ROLE_MEMORY_FILES:-SOUL.md RULES.md snapshot.md MEMORY.md project_briefing.md}}"
: "${SDLC_SHARED_DOCS_TEST_AUTOMATION_LEAD:=${SDLC_SHARED_DOCS:-testing profile workflow conventions role-overrides team-comms}}"
: "${SDLC_ROLE_MEMORY_FILES_TEST_AUTOMATION_LEAD:=${SDLC_ROLE_MEMORY_FILES:-SOUL.md RULES.md snapshot.md MEMORY.md project_briefing.md}}"
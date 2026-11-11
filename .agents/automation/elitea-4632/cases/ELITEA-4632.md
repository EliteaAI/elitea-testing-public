---
id: ELITEA-4632
title: "ELITEA-4632: Navigate to Skill Run Analytics and Verify Cost Accuracy"
priority: critical
type: regression
module: skills/analytics
status: draft
execution_type: manual
tags: [automated:UI:regression, feat:skills, analytics, cost-tracking, data-reconciliation]
requirements: [EliteaAI/elitea_issues#6928]
---
# ELITEA-4632: Navigate to Skill Run Analytics and Verify Cost Accuracy

**Module:** Skills / Analytics · **Priority:** Critical · **Type:** Regression

**Objective:** Verify that users can navigate from skill Run History to the Analytics page, and that cost calculations are accurate and reconcile correctly with usage events.

**Coverage:**
- Navigation from Run History to Analytics
- Analytics page loads with correct run context
- Costs tab displays total cost accurately
- Cost breakdown by model is correct
- Cost reconciles with usage events data
- No data leakage between different runs

## Preconditions

- User is logged into {{base_url}}
- User has created at least one skill with execution history
- Skill has completed runs with cost/token data
- Run used specific model(s) with known pricing

## Test Data

| Field | Value |
|-------|-------|
| Skill name | test-skill-analytics |
| Completed run | Run with known token usage and model |
| Model used | e.g., Claude Sonnet (with known token pricing) |
| Expected cost calculation | (prompt_tokens + completion_tokens) × model_rate |

## Steps

| # | Action | Expected Result |
|---|--------|-----------------|
| 1 | Navigate to skill's Run History page | Run History displays with list of executions |
| 2 | Locate a completed run with cost data | Run row shows in table |
| 3 | Click 3-dot menu (⋮) on the run row | Context menu appears |
| 4 | Click "Analytics" option | Navigation to Analytics page initiates |
| 5 | Verify Analytics page loads | Analytics page displays for selected run |
| 6 | Verify breadcrumbs show correct navigation path | Breadcrumbs display: Skills > [Skill Name] > Run [ID] > Analytics |
| 7 | Verify run header displays correct metadata | Run ID, timestamp, status, version visible |
| 8 | Click "Costs" tab | Costs tab becomes active |
| 9 | Verify "Total Cost" summary card displays | Total cost shown with $ amount |
| 10 | Verify "Cost Breakdown" section shows model-level costs | Cost breakdown by model displayed (e.g., Claude Sonnet: $X.XX) |
| 11 | Verify "Cost by User" table shows accurate data | If applicable, cost attributed to user correctly |
| 12 | Verify "Cost by Model" table shows accurate data | Each model's cost and token usage displayed |
| 13 | Calculate expected cost: (prompt_tokens + completion_tokens) × model_rate | Manual calculation matches displayed total |
| 14 | Click "Health" or "Tokens" tab and return to "Costs" | Tab switching preserves run context, no data mixing |
| 15 | Navigate to different run and verify costs don't leak | Each run shows only its own cost data |

## Expected Final State

- Navigation from Run History to Analytics works seamlessly
- Analytics page displays correct run-specific data
- Total cost matches token usage × model pricing
- Cost breakdown reconciles with usage events
- No data leakage between different skill runs
- All financial data is accurate and auditable

## Pass/Fail Criteria

**Pass:**
- Analytics navigation from Run History works
- Costs tab displays with total cost and breakdown
- Cost calculation is mathematically correct
- Cost data reconciles with usage events/tokens
- Each run shows only its own cost data

**Fail:**
- Analytics page doesn't load or shows wrong run
- Cost calculations are incorrect or missing
- Cost breakdown doesn't match total
- Data from different runs mixed together
- Cost doesn't reconcile with token usage

## Notes

**Source functional tests:** ELITEA-4408, ELITEA-4409, ELITEA-4412, ELITEA-4424
**Regression rationale:** Business-critical financial accuracy; ensures billing integrity and cost tracking for skill executions.
**Selected checkpoints:** Navigation flow, cost calculation accuracy, data reconciliation, run isolation.

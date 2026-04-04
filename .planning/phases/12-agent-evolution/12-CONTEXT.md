# Phase 12: Agent Evolution - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

Add 5th detector to agent_pr_creator.py: detect_pilot_queue_stale(). Flags pending pilot_queue.json entries older than 24 hours. Ensures no pilot request goes unanswered.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
- Follow existing detector pattern in agent_pr_creator.py (4 existing detectors)
- Read reports/pilot_queue.json, check timestamps
- Entries with status "pending" or "processed" older than 24h are stale
- Return warning message for each stale entry

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- scripts/agent_pr_creator.py has 4 detectors already
- reports/pilot_queue.json created by agent_pilot.py in Phase 11

### Integration Points
- agent_pr_creator.py is called by agent_evolution.py check #18

</code_context>

<specifics>
## Specific Ideas

No specific requirements — follow existing detector pattern.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

---
name: action-document
description: Create and continuously update a traceable action document for implementation, bug-fixing, refactoring, or other project file changes. Use before modifying files when the work needs recorded context, measures, affected file trees, verification methods, and actual verification results. Do not use for discussion-only or read-only work.
---

# Traceable action document

Maintain one action document as the task's execution record. It must describe the real current state, not an aspirational or stale plan.

## Before changing project files

1. Read the applicable `AGENTS.md` and authoritative project documents.
2. Reuse the project's action-document location and naming convention. If none exists, use `docs/actions/YYYY-MM-DD-<task-name>.md`.
3. Create or update the action document before implementation begins with these sections:
   - **Status and situation**: status, scope, source request, current facts, confirmed decisions, unknowns, and explicit exclusions.
   - **Implementation measures**: ordered changes and completion criteria.
   - **Affected file tree**: planned additions, modifications, and removals. Annotate every path with its responsibility. State relevant relationships and design-pattern roles.
   - **Self-verification method**: commands, checks, test layers, and expected results.
   - **Self-verification results**: initially `Pending`.

If the user has limited the work to discussion or read-only analysis, do not create an action document unless they explicitly request the document itself.

## While executing

- Keep the measures and affected file tree synchronized with actual work.
- Record material deviations and newly confirmed decisions when they occur.
- Inspect existing interfaces and documentation before use; do not guess or invent an interface that can be reused.
- Ask the user to decide unresolved product behavior, scope, or architecture tradeoffs. Find discoverable technical facts yourself.
- Link to authoritative facts instead of duplicating them across documents.

## Before closing

1. Replace planned file entries with the actual changed-file tree.
2. Record every verification command or manual check and its actual result.
3. Record failures, skipped checks, limitations, and remaining risks honestly.
4. Update any affected problem, architecture, status, or deployment document in the same change batch so no stale source of truth remains.
5. Set the action document status to `Completed`, `Blocked`, or `Superseded` only when that state is factual.

Never report a check as passed unless it was run and its result was inspected.

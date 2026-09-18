# QMI Foundation v1.3 — Consolidation 001

Scope: structural cleanup only. Functional decision behavior is intentionally frozen.

## Changes

1. Archived accidental nested `backend/backend/` tree under `docs/consolidation/archive/` and removed it from runtime source.
2. Removed duplicate design-token import in React entry point.
3. Added `.js` extension to `qmiDecisionService`.
4. Added static regression/architecture tests.
5. Documented DE-CORE-006.x identifier collisions for a later controlled migration.

## Explicitly unchanged

- Technical calculations and gates.
- Fundamental calculations.
- Cross-engine fusion DE-CORE-004.2.
- Action Policy DE-CORE-005.2.
- Snapshot/history behavior.
- API endpoint paths.
- Database schema.

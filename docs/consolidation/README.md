# QMI Consolidation 001

This directory records the first structural consolidation of QMI Foundation v1.3.

## Applied safe changes

- Removed the accidental runtime `backend/backend/` duplicate tree.
- Preserved that tree verbatim under `docs/consolidation/archive/backend_backend/` for forensic comparison.
- Removed the duplicated `tokens.css` import from `frontend/src/main.jsx`.
- Renamed the extensionless `frontend/src/services/qmiDecisionService` to `qmiDecisionService.js`.
- Added architecture-contract tests under `backend/tests/`.
- No decision formulas, engine weights, API paths, database schemas, or UI business logic were intentionally changed.

## Deferred intentionally

Engine-ID collisions in the DE-CORE-006.x family are documented but not automatically renumbered because IDs may be persisted in snapshots/history. They require a migration/versioning decision rather than a blind rename.

Empty frontend placeholder components and page CSS files are retained because deleting them gives little benefit and they may be reserved for planned modules.

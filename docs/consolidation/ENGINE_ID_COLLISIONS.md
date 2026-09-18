# DE-CORE-006.x ID collisions

The current source contains repeated IDs that represent different services. These are preserved in Consolidation 001 to avoid changing persisted identifiers without a migration policy.

Known examples from the audited source:

- `DE-CORE-006.5.1`: scheduled observation service and automatic outcome refresh service.
- `DE-CORE-006.5.2`: observation pipeline service, decision price capture service, and outcome tracking service.

Before renumbering, inspect stored snapshots/history and define backward-compatible aliases or a data migration.

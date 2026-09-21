QMI V1_4 — DE-CORE-004.4 Decision Trust Layer

Adds an auditable trust layer to the integrated QMI decision.
The trust score uses existing DE-DI evidence instead of creating duplicate engines.

Trust components:
- Decision Evidence Score: 40%
- Historical Decision Reliability: 25%
- Contradiction Coherence: 20%
- Persisted Validation State: 15%

Missing components are renormalized. Governance caps can limit trust when the evidence gate is blocked, the decision is unvalidated, or the contradiction guard reports a hard conflict.

IMPORTANT: Decision Trust does NOT change Combined Score, fusion weights, execution permission, or technical risk gates.

BACKEND
cd C:\Users\rodri\OneDrive\Escritorio\Python\QMI_Foundation_v1_4\backend
..\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload

FRONTEND
cd C:\Users\rodri\OneDrive\Escritorio\Python\QMI_Foundation_v1_4\frontend
npm run dev

After replacing files, use Ctrl+F5 in the browser.

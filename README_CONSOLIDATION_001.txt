QMI FOUNDATION v1.3 — CONSOLIDATION 001
=======================================

This is the complete consolidated project based on the supplied QMI_Foundation_v1_3.

SAFE STRUCTURAL CHANGES
- backend/backend removed from runtime and preserved in docs/consolidation/archive/backend_backend.
- Duplicate ./styles/tokens.css import removed from frontend/src/main.jsx.
- frontend/src/services/qmiDecisionService renamed to qmiDecisionService.js.
- backend/tests/test_architecture_contracts.py added.
- DE-CORE-006.x ID collisions documented, not renumbered.

VALIDATION PERFORMED
- Python source compilation: PASS.
- Architecture tests: 3 PASS.
- Frontend Vite build in the audit container: NOT EXECUTABLE because uploaded node_modules contains Windows-native optional bindings, while audit runs on Linux. This is an environment mismatch, not a detected source-code failure. Validate on the target Windows machine with npm run dev/build.

BACKEND (PowerShell)
cd C:\Users\rodri\OneDrive\Escritorio\Python\QMI_Foundation_v1_3\backend
python -m uvicorn app.main:app --reload

FRONTEND (PowerShell)
cd C:\Users\rodri\OneDrive\Escritorio\Python\QMI_Foundation_v1_3\frontend
npm run dev

If dependencies need refreshing:
npm install
npm run dev

After CSS/frontend changes, use Ctrl+F5 in the browser.

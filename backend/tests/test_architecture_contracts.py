from pathlib import Path
import ast

BACKEND = Path(__file__).resolve().parents[1]
PROJECT = BACKEND.parent


def test_backend_has_single_runtime_root():
    assert (BACKEND / "app" / "main.py").is_file()
    assert not (BACKEND / "backend").exists(), "Nested backend/backend must stay out of runtime tree"


def test_critical_decision_services_exist():
    required = [
        "app/services/technical/decision_synthesis_service.py",
        "app/fundamental/fundamental_decision_engine.py",
        "app/services/qmi_decision_service.py",
        "app/services/qmi_decision_policy_service.py",
        "app/api/routes/qmi_decision_snapshot.py",
    ]
    missing = [p for p in required if not (BACKEND / p).is_file()]
    assert not missing, f"Missing critical QMI files: {missing}"


def test_backend_python_sources_parse():
    failures = []
    for path in (BACKEND / "app").rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        except Exception as exc:
            failures.append(f"{path.relative_to(PROJECT)}: {exc}")
    assert not failures, "Python syntax failures:\n" + "\n".join(failures)

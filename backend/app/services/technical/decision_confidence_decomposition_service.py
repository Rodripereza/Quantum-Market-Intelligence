from __future__ import annotations
from typing import Any

class DecisionConfidenceDecompositionService:
    ENGINE_ID="DE-DI-005"
    VERSION="0.1.1"

    @staticmethod
    def _n(v, default=0.0):
        try: return float(v)
        except (TypeError, ValueError): return default

    def analyze(self, *, decision_synthesis: dict[str,Any], execution_plan: dict[str,Any],
                confluence: dict[str,Any], transition: dict[str,Any], persistence: dict[str,Any]) -> dict[str,Any]:
        syn=decision_synthesis.get("technical_decision_synthesis") or decision_synthesis.get("decision_synthesis") or {}
        conf=confluence.get("technical_confluence") or {}
        diag=conf.get("diagnostics") or {}
        drivers=[d for d in diag.get("engine_contributions") or [] if d.get("available") is not False]
        driver_conf=[self._n(d.get("confidence")) for d in drivers if d.get("confidence") is not None]
        agreement=sum(driver_conf)/len(driver_conf) if driver_conf else 0.0
        conviction=self._n(syn.get("conviction") or syn.get("confidence"))
        execution_core = execution_plan.get("technical_execution_plan") or execution_plan
        execution_confidence = (
            execution_core.get("execution_confidence")
            or execution_plan.get("execution_confidence")
            or {}
        )
        if isinstance(execution_confidence, dict):
            exe = self._n(execution_confidence.get("score"))
        else:
            exe = self._n(execution_confidence)
        tr=(transition.get("technical_state_transition") or {})
        readiness=self._n((tr.get("transition_readiness") or {}).get("score"))
        stability=self._n((persistence.get("technical_state_persistence") or persistence).get("stability_score"), conviction)
        components={"technical_agreement":agreement,"driver_consistency":conviction,"state_stability":stability,
                    "transition_certainty":readiness,"execution_confidence":exe}
        vals=[v for v in components.values() if v>0]
        overall=sum(vals)/len(vals) if vals else conviction
        strongest=max(components,key=components.get); weakest=min(components,key=components.get)
        quality="HIGH" if overall>=75 else "MEDIUM" if overall>=55 else "LOW"
        return {"engine_id":self.ENGINE_ID,"version":self.VERSION,"status":"operational",
                "decision_confidence_decomposition":{"overall":round(overall,1),"quality":quality,
                "components":{k:round(v,1) for k,v in components.items()},
                "main_confidence_source":strongest,"main_uncertainty_source":weakest,
                "method":"deterministic_existing_pipeline_signals","automatic_execution":False}}

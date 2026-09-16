from copy import deepcopy
from threading import Lock
from time import perf_counter, monotonic

from fastapi import APIRouter, HTTPException, Query

from app.api.routes.support_resistance import get_support_resistance

from app.api.routes.technical_execution_plan import (
    get_technical_execution_plan,
)
from app.api.routes.technical_regime_maturity import (
    build_regime_maturity_from_context,
)
from app.api.routes.technical_state_persistence import (
    get_technical_state_persistence,
)
from app.api.routes.technical_state_transition import (
    state_transition_service,
)
from app.services.technical.decision_synthesis_service import (
    TechnicalDecisionSynthesisService,
)
from app.services.technical.transition_confirmation_service import (
    TechnicalTransitionConfirmationService,
)
from app.services.technical.setup_engine_service import (
    TechnicalSetupEngineService,
)
from app.services.technical.price_plan_service import (
    TechnicalPricePlanService,
)
from app.services.technical.state_history_service import (
    TechnicalStateHistoryService,
)
from app.services.technical.decision_evolution_service import (
    DecisionEvolutionService,
)
from app.services.technical.decision_change_attribution_service import (
    DecisionChangeAttributionService,
)
from app.services.technical.decision_confidence_decomposition_service import (
    DecisionConfidenceDecompositionService,
)
from app.services.technical.decision_reliability_service import (
    DecisionReliabilityService,
)
from app.services.technical.decision_reliability_breakdown_service import (
    DecisionReliabilityBreakdownService,
)
from app.services.technical.decision_outcome_service import (
    DecisionOutcomeService,
)
from app.services.technical.decision_calibration_service import (
    DecisionCalibrationService,
)
from app.services.technical.decision_memory_service import (
    DecisionMemoryService,
)
from app.services.technical.historical_outcome_memory_service import (
    HistoricalOutcomeMemoryService,
)
from app.services.technical.historical_edge_service import (
    HistoricalEdgeService,
)
from app.services.technical.decision_evidence_alignment_service import (
    DecisionEvidenceAlignmentService,
)
from app.services.technical.decision_evidence_score_service import (
    DecisionEvidenceScoreService,
)
from app.services.technical.decision_evidence_gate_service import (
    DecisionEvidenceGateService,
)
from app.services.technical.decision_validation_state_service import (
    DecisionValidationStateService,
)
from app.services.technical.decision_validation_momentum_service import (
    DecisionValidationMomentumService,
)
from app.services.technical.decision_contradiction_guard_service import (
    DecisionContradictionGuardService,
)
from app.services.technical.shadow_adaptive_decision_service import (
    ShadowAdaptiveDecisionService,
)
from app.services.technical.decision_intelligence_quality_control_service import (
    DecisionIntelligenceQualityControlService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

transition_confirmation_service = (
    TechnicalTransitionConfirmationService()
)
decision_synthesis_service = TechnicalDecisionSynthesisService()
setup_engine_service = TechnicalSetupEngineService()
price_plan_service = TechnicalPricePlanService()
state_history_service = TechnicalStateHistoryService()
decision_evolution_service = DecisionEvolutionService()
decision_change_attribution_service = DecisionChangeAttributionService()
decision_confidence_decomposition_service = DecisionConfidenceDecompositionService()
decision_reliability_service = DecisionReliabilityService()
decision_reliability_breakdown_service = DecisionReliabilityBreakdownService()
decision_outcome_service = DecisionOutcomeService()
decision_calibration_service = DecisionCalibrationService()
decision_memory_service = DecisionMemoryService()
historical_outcome_memory_service = HistoricalOutcomeMemoryService()
historical_edge_service = HistoricalEdgeService()
decision_evidence_alignment_service = DecisionEvidenceAlignmentService()
decision_evidence_score_service = DecisionEvidenceScoreService()
decision_evidence_gate_service = DecisionEvidenceGateService()
decision_validation_state_service = DecisionValidationStateService()
decision_validation_momentum_service = DecisionValidationMomentumService()
decision_contradiction_guard_service = DecisionContradictionGuardService()
shadow_adaptive_decision_service = ShadowAdaptiveDecisionService()
decision_intelligence_quality_control_service = DecisionIntelligenceQualityControlService()


# BE-DI-001 — Decision Snapshot Performance
# Short-lived in-process cache shared by Technical and Decision Intelligence.
# This is intentionally separate from DE-CORE-006.1 historical Snapshot Policy.
_UI_SNAPSHOT_CACHE_TTL_SECONDS = 60.0
_ui_snapshot_cache = {}
_ui_snapshot_cache_lock = Lock()
_ui_snapshot_key_locks = {}


def _snapshot_cache_key(symbol, period, interval, pivot_window, history_limit):
    return (
        str(symbol).strip().upper(),
        str(period),
        str(interval),
        int(pivot_window),
        int(history_limit),
    )


def _get_key_lock(cache_key):
    with _ui_snapshot_cache_lock:
        lock = _ui_snapshot_key_locks.get(cache_key)
        if lock is None:
            lock = Lock()
            _ui_snapshot_key_locks[cache_key] = lock
        return lock


def _read_cached_snapshot(cache_key):
    now = monotonic()
    with _ui_snapshot_cache_lock:
        entry = _ui_snapshot_cache.get(cache_key)
        if not entry:
            return None, None

        age_seconds = now - entry["stored_at"]
        if age_seconds >= _UI_SNAPSHOT_CACHE_TTL_SECONDS:
            _ui_snapshot_cache.pop(cache_key, None)
            return None, None

        return deepcopy(entry["payload"]), age_seconds


def _store_cached_snapshot(cache_key, payload):
    with _ui_snapshot_cache_lock:
        _ui_snapshot_cache[cache_key] = {
            "stored_at": monotonic(),
            "payload": deepcopy(payload),
        }


def _with_cache_metadata(payload, *, cache_hit, cache_age_seconds=0.0, request_ms=0.0):
    result = deepcopy(payload)
    performance = dict(result.get("performance") or {})
    performance.update({
        "cache_enabled": True,
        "cache_hit": bool(cache_hit),
        "cache_ttl_seconds": _UI_SNAPSHOT_CACHE_TTL_SECONDS,
        "cache_age_seconds": round(float(cache_age_seconds), 3),
        "request_ms": round(float(request_ms), 2),
    })
    result["performance"] = performance
    return result


@router.get("/ui-snapshot/{symbol}")
def get_technical_ui_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
    force_refresh: bool = False,
):
    """
    DE-CORE-003 — Technical UI Snapshot

    Builds one shared evaluation for the upper technical UI pipeline and
    returns the complete DE-TA-013.0 → DE-TA-015.0 snapshot:

    - Technical Confluence / Decision Drivers
    - Execution Plan
    - State Transition
    - State Persistence
    - Regime Maturity
    - Transition Confirmation
    - Decision Synthesis
    - Technical Setup Qualification
    - Technical Price Plan
    - Support / Resistance context

    The expensive upstream technical context is evaluated only once.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    cache_key = _snapshot_cache_key(
        normalized_symbol,
        period,
        interval,
        pivot_window,
        history_limit,
    )
    request_started = perf_counter()

    if not force_refresh:
        cached, age_seconds = _read_cached_snapshot(cache_key)
        if cached is not None:
            return _with_cache_metadata(
                cached,
                cache_hit=True,
                cache_age_seconds=age_seconds,
                request_ms=(perf_counter() - request_started) * 1000.0,
            )

    key_lock = _get_key_lock(cache_key)

    try:
        with key_lock:
            # A second request may have completed while this request was waiting.
            if not force_refresh:
                cached, age_seconds = _read_cached_snapshot(cache_key)
                if cached is not None:
                    return _with_cache_metadata(
                        cached,
                        cache_hit=True,
                        cache_age_seconds=age_seconds,
                        request_ms=(perf_counter() - request_started) * 1000.0,
                    )

            build_started = perf_counter()
            # 1) Build DE-TA-013.0 once, including its already-computed sources.
            execution_started = perf_counter()
            execution_response = get_technical_execution_plan(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                pivot_window=pivot_window,
                include_source_responses=True,
            )
            execution_ms = (perf_counter() - execution_started) * 1000.0

            evaluation_context = (
                execution_response.pop("_evaluation_context", None) or {}
            )

            confluence_response = (
                evaluation_context.get("confluence_response") or {}
            )
            decision_response = (
                evaluation_context.get("decision_response") or {}
            )
            scenario_response = (
                evaluation_context.get("scenario_response") or {}
            )
            action_response = (
                evaluation_context.get("action_response") or {}
            )
            risk_response = (
                evaluation_context.get("risk_response") or {}
            )
            sizing_response = (
                evaluation_context.get("sizing_response") or {}
            )

            missing_sources = [
                name
                for name, value in {
                    "confluence_response": confluence_response,
                    "decision_response": decision_response,
                    "scenario_response": scenario_response,
                    "action_response": action_response,
                    "risk_response": risk_response,
                    "sizing_response": sizing_response,
                }.items()
                if not value
            ]

            if missing_sources:
                raise RuntimeError(
                    "Execution Plan did not expose the expected evaluation "
                    f"context: {', '.join(missing_sources)}"
                )

            # 2) Derive DE-TA-014.0 from the same context.
            transition_result = state_transition_service.analyze(
                execution_response=execution_response,
                sizing_response=sizing_response,
                risk_response=risk_response,
                action_response=action_response,
                decision_response=decision_response,
                scenario_response=scenario_response,
            )

            transition_response = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "current_price": decision_response.get(
                    "current_price",
                    execution_response.get("current_price"),
                ),
                "source_execution_engine_id": execution_response.get("engine_id"),
                "source_sizing_engine_id": sizing_response.get("engine_id"),
                "source_risk_engine_id": risk_response.get("engine_id"),
                "source_action_engine_id": action_response.get("engine_id"),
                "source_decision_engine_id": decision_response.get("engine_id"),
                "source_scenario_engine_id": scenario_response.get("engine_id"),
                "performance": {
                    "upstream_context_reused": True,
                    "duplicate_upstream_calls_removed": 5,
                },
                **transition_result,
            }

            # 3) Historical persistence is loaded once.
            persistence_started = perf_counter()
            persistence_response = get_technical_state_persistence(
                symbol=normalized_symbol,
                limit=history_limit,
            )
            persistence_ms = (perf_counter() - persistence_started) * 1000.0

            # 4) Derive DE-TA-014.3 from existing 014.0 + 014.2.
            maturity_response = build_regime_maturity_from_context(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                persistence_response=persistence_response,
                transition_response=transition_response,
            )

            # 5) Derive DE-TA-014.4 without re-running the upstream tree.
            confirmation_result = transition_confirmation_service.analyze(
                maturity_response=maturity_response,
                persistence_response=persistence_response,
                transition_response=transition_response,
                execution_response=execution_response,
                action_response=action_response,
                risk_response=risk_response,
            )

            confirmation_response = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "source_maturity_engine_id": maturity_response.get("engine_id"),
                "source_persistence_engine_id": persistence_response.get("engine_id"),
                "source_transition_engine_id": transition_response.get("engine_id"),
                "source_execution_engine_id": execution_response.get("engine_id"),
                "source_action_engine_id": action_response.get("engine_id"),
                "source_risk_engine_id": risk_response.get("engine_id"),
                "performance": {
                    "shared_evaluation_context": True,
                    "execution_plan_evaluations": 1,
                    "transition_recomputed": False,
                    "action_recomputed": False,
                    "risk_recomputed": False,
                },
                **confirmation_result,
            }

            # 6) DE-TA-015.0 consumes the already-computed confirmation.
            synthesis_result = decision_synthesis_service.analyze(
                confirmation_response=confirmation_response,
            )

            synthesis_response = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "source_confirmation_engine_id": confirmation_response.get(
                    "engine_id"
                ),
                "performance": {
                    "execution_plan_recomputed": False,
                    "synthesis_input": "DE-TA-014.4",
                    "ui_snapshot_context_reused": True,
                },
                **synthesis_result,
            }

            # DE-DI-003.0 — live state versus latest persisted baseline.
            previous_state_snapshot = state_history_service.latest_snapshot(normalized_symbol)
            previous_driver_snapshot = state_history_service.latest_driver_snapshot(normalized_symbol)
            decision_evolution_response = decision_evolution_service.analyze(
                symbol=normalized_symbol, previous_snapshot=previous_state_snapshot,
                transition_response=transition_response, decision_synthesis_response=synthesis_response,
                confluence_response=confluence_response, previous_driver_snapshot=previous_driver_snapshot,
            )
            synthesis_core = (
                synthesis_response.get("technical_decision_synthesis")
                or synthesis_response.get("decision_synthesis")
                or {}
            )
            current_posture = synthesis_core.get("final_posture")
            decision_change_attribution_response = decision_change_attribution_service.analyze(
                symbol=normalized_symbol,
                decision_evolution_response=decision_evolution_response,
                current_posture=current_posture,
                previous_driver_snapshot=previous_driver_snapshot,
            )
            decision_confidence_decomposition_response = decision_confidence_decomposition_service.analyze(
                decision_synthesis=synthesis_response,
                execution_plan=execution_response,
                confluence=confluence_response,
                transition=transition_response,
                persistence=persistence_response,
            )
            driver_persistence = state_history_service.record_driver_snapshot(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                confluence_response=confluence_response,
                decision_posture=current_posture,
            )

            # 7) DE-TA-016.0 reuses the already-computed 015.0 synthesis.
            setup_result = setup_engine_service.analyze(
                synthesis_response=synthesis_response,
            )

            setup_response = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "source_synthesis_engine_id": synthesis_response.get("engine_id"),
                "performance": {
                    "decision_synthesis_recomputed": False,
                    "ui_snapshot_context_reused": True,
                },
                **setup_result,
            }

            # 8) Build DE-TA-006.1 once for the UI and DE-TA-016.1.
            # MarketService cache makes this reuse the same recent history.
            support_resistance_started = perf_counter()
            support_resistance_response = get_support_resistance(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                pivot_window=pivot_window,
                min_touches=2,
                max_zones=6,
            )
            support_resistance_ms = (perf_counter() - support_resistance_started) * 1000.0

            # 9) DE-TA-016.1 reuses the already-computed 016.0 setup + S/R.
            price_plan_result = price_plan_service.analyze(
                setup_response=setup_response,
                support_resistance_response=support_resistance_response,
            )

            price_plan_response = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "source_setup_engine_id": setup_response.get("engine_id"),
                "source_support_resistance_engine_id": (
                    support_resistance_response.get("engine_id")
                ),
                "performance": {
                    "setup_recomputed": False,
                    "support_resistance_reused": True,
                    "ui_snapshot_context_reused": True,
                },
                **price_plan_result,
            }

            evolution_timeline = state_history_service.evolution_timeline(
                normalized_symbol,
                limit=12,
            )
            reliability_history = state_history_service.history(normalized_symbol, limit=250)
            decision_reliability_response = decision_reliability_service.analyze(
                symbol=normalized_symbol,
                state_history=reliability_history,
            )
            decision_reliability_breakdown_response = decision_reliability_breakdown_service.analyze(
                symbol=normalized_symbol,
                state_history=reliability_history,
            )
            decision_outcome_response = decision_outcome_service.analyze(
                symbol=normalized_symbol,
                state_history=reliability_history,
            )
            decision_calibration_response = decision_calibration_service.analyze(
                reliability_breakdown=decision_reliability_breakdown_response,
                decision_outcome=decision_outcome_response,
            )
            memory_driver_history = state_history_service.driver_history(
                normalized_symbol,
                limit=100,
            )
            decision_memory_response = decision_memory_service.analyze(
                current_state=(reliability_history[0] if reliability_history else {}),
                current_drivers=state_history_service.latest_driver_snapshot(normalized_symbol),
                state_history=reliability_history,
                driver_history=memory_driver_history,
            )
            historical_outcome_memory_response = historical_outcome_memory_service.analyze(
                decision_memory=decision_memory_response,
                state_history=reliability_history,
            )
            historical_edge_response = historical_edge_service.analyze(
                historical_outcome_memory=historical_outcome_memory_response,
            )
            decision_evidence_alignment_response = decision_evidence_alignment_service.analyze(
                decision_synthesis=synthesis_response,
                historical_edge=historical_edge_response,
            )
            decision_evidence_score_response = decision_evidence_score_service.analyze(
                confidence_decomposition=decision_confidence_decomposition_response,
                historical_edge=historical_edge_response,
                evidence_alignment=decision_evidence_alignment_response,
            )
            decision_evidence_gate_response = decision_evidence_gate_service.analyze(
                decision_synthesis=synthesis_response,
                decision_evidence_score=decision_evidence_score_response,
                evidence_alignment=decision_evidence_alignment_response,
                historical_edge=historical_edge_response,
            )
            decision_validation_state_response = decision_validation_state_service.evaluate(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                evidence_gate=decision_evidence_gate_response,
                persist=True,
            )
            decision_validation_history = decision_validation_state_service.history(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                limit=12,
            )
            decision_validation_momentum_response = decision_validation_momentum_service.analyze(
                validation_state=decision_validation_state_response,
                validation_history=decision_validation_history,
            )
            decision_contradiction_guard_response = decision_contradiction_guard_service.analyze(
                decision_synthesis=synthesis_response,
                execution_plan=execution_response,
                evidence_alignment=decision_evidence_alignment_response,
                evidence_gate=decision_evidence_gate_response,
                validation_state=decision_validation_state_response,
                validation_momentum=decision_validation_momentum_response,
            )
            shadow_adaptive_decision_response = shadow_adaptive_decision_service.analyze(
                decision_synthesis=synthesis_response,
                historical_edge=historical_edge_response,
                evidence_score=decision_evidence_score_response,
                evidence_gate=decision_evidence_gate_response,
                contradiction_guard=decision_contradiction_guard_response,
                validation_momentum=decision_validation_momentum_response,
            )
            decision_intelligence_quality_control_response = decision_intelligence_quality_control_service.analyze(
                decision_synthesis=synthesis_response,
                execution_plan=execution_response,
                evidence_score=decision_evidence_score_response,
                evidence_gate=decision_evidence_gate_response,
                validation_state=decision_validation_state_response,
                validation_momentum=decision_validation_momentum_response,
                contradiction_guard=decision_contradiction_guard_response,
                shadow_adaptive_decision=shadow_adaptive_decision_response,
            )

            total_build_ms = (perf_counter() - build_started) * 1000.0

            snapshot = {
                "symbol": normalized_symbol,
                "period": period,
                "interval": interval,
                "engine": "QMI Technical UI Snapshot",
                "engine_id": "DE-CORE-003",
                "version": "2.3.0",
                "status": "operational",
                "performance": {
                    "shared_evaluation_context": True,
                    "execution_plan_evaluations": 1,
                    "ui_requests_consolidated": 30,
                "confluence_included": True,
                "decision_evolution_included": True,
                    "driver_evolution_history_included": True,
                    "evolution_timeline_included": True,
                    "decision_change_attribution_included": True,
                    "decision_confidence_decomposition_included": True,
                    "decision_reliability_included": True,
                    "decision_reliability_breakdown_included": True,
                    "decision_outcome_included": True,
                    "decision_calibration_included": True,
                    "decision_memory_included": True,
                    "historical_outcome_memory_included": True,
                    "historical_edge_included": True,
                    "decision_evidence_alignment_included": True,
                    "decision_evidence_score_included": True,
                    "decision_evidence_gate_included": True,
                    "decision_validation_state_included": True,
                    "decision_validation_momentum_included": True,
                    "decision_contradiction_guard_included": True,
                    "shadow_adaptive_decision_included": True,
                    "decision_intelligence_quality_control_included": True,
                    "upper_pipeline_recomputations_removed": True,
                    "cache_enabled": True,
                    "cache_hit": False,
                    "cache_ttl_seconds": _UI_SNAPSHOT_CACHE_TTL_SECONDS,
                    "cache_age_seconds": 0.0,
                    "timings_ms": {
                        "execution_plan": round(execution_ms, 2),
                        "state_persistence": round(persistence_ms, 2),
                        "support_resistance": round(support_resistance_ms, 2),
                        "derived_pipeline": round(
                            max(
                                0.0,
                                total_build_ms
                                - execution_ms
                                - persistence_ms
                                - support_resistance_ms,
                            ),
                            2,
                        ),
                        "total_build": round(total_build_ms, 2),
                    },
                },
                "confluence": confluence_response,
                "decision_evolution": decision_evolution_response,
                "decision_change_attribution": decision_change_attribution_response,
                "decision_confidence_decomposition": decision_confidence_decomposition_response,
                "decision_reliability": decision_reliability_response,
                "decision_reliability_breakdown": decision_reliability_breakdown_response,
                "decision_outcome": decision_outcome_response,
                "decision_calibration": decision_calibration_response,
                "decision_memory": decision_memory_response,
                "historical_outcome_memory": historical_outcome_memory_response,
                "historical_edge": historical_edge_response,
                "decision_evidence_alignment": decision_evidence_alignment_response,
                "decision_evidence_score": decision_evidence_score_response,
                "decision_evidence_gate": decision_evidence_gate_response,
                "decision_validation_state": decision_validation_state_response,
                "decision_validation_momentum": decision_validation_momentum_response,
                "decision_contradiction_guard": decision_contradiction_guard_response,
                "shadow_adaptive_decision": shadow_adaptive_decision_response,
                "decision_intelligence_quality_control": decision_intelligence_quality_control_response,
                "driver_persistence": driver_persistence,
                "evolution_timeline": evolution_timeline,
                "execution_plan": execution_response,
                "state_transition": transition_response,
                "state_persistence": persistence_response,
                "regime_maturity": maturity_response,
                "transition_confirmation": confirmation_response,
                "decision_synthesis": synthesis_response,
                "technical_setup": setup_response,
                "support_resistance": support_resistance_response,
                "technical_price_plan": price_plan_response,
            }

            _store_cached_snapshot(cache_key, snapshot)

            return _with_cache_metadata(
                snapshot,
                cache_hit=False,
                cache_age_seconds=0.0,
                request_ms=(perf_counter() - request_started) * 1000.0,
            )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate technical UI snapshot. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc

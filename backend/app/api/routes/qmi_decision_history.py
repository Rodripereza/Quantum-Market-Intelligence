from fastapi import APIRouter, HTTPException, Query

from app.api.routes.qmi_action_policy import get_qmi_action_policy
from app.services.qmi_decision_history_service import QMIDecisionHistoryService
from app.services.qmi_snapshot_policy_service import QMISnapshotPolicyService
from app.services.qmi_decision_price_capture_service import (
    QMIDecisionPriceCaptureService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

history_service = QMIDecisionHistoryService()
snapshot_policy_service = QMISnapshotPolicyService()
price_capture_service = QMIDecisionPriceCaptureService()


def _capture_price(
    symbol: str,
    policy_response: dict,
):
    return price_capture_service.enrich(
        symbol=symbol,
        action_policy_response=policy_response,
        fail_open=True,
    )


def _build_policy_response(
    *,
    symbol: str,
    period: str,
    interval: str,
    pivot_window: int,
    history_limit: int,
):
    return get_qmi_action_policy(
        symbol=symbol,
        period=period,
        interval=interval,
        pivot_window=pivot_window,
        history_limit=history_limit,
        observe=False,
    )


@router.post("/decision-history/snapshot/{symbol}")
def record_qmi_decision_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-006.0 — Manual/administrative snapshot.

    This endpoint intentionally preserves the original unconditional POST
    behavior for debugging and exceptional manual persistence.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    try:
        policy_response = _build_policy_response(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        policy_response, price_capture = _capture_price(
            normalized_symbol,
            policy_response,
        )

        persistence = history_service.record_snapshot(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            action_policy_response=policy_response,
        )

        return {
            "symbol": normalized_symbol,
            "engine": history_service.ENGINE,
            "engine_id": history_service.ENGINE_ID,
            "version": history_service.VERSION,
            "status": "operational",
            "mode": "MANUAL_UNCONDITIONAL",
            "source_policy_engine_id": policy_response.get("engine_id"),
            "decision_price_capture": price_capture,
            "persistence": persistence,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to persist QMI decision snapshot. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get("/snapshot-policy/{symbol}")
def preview_qmi_snapshot_policy(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
    force: bool = Query(default=False),
):
    """
    DE-CORE-006.1 — Preview SAVE / SKIP without writing to the database.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    try:
        policy_response = _build_policy_response(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        policy_response, price_capture = _capture_price(
            normalized_symbol,
            policy_response,
        )

        previous = history_service.latest_snapshot(normalized_symbol)

        result = snapshot_policy_service.evaluate(
            symbol=normalized_symbol,
            action_policy_response=policy_response,
            previous_snapshot=previous,
            force=force,
        )
        result["decision_price_capture"] = price_capture
        return result

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to evaluate QMI snapshot policy. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.post("/decision-history/smart-snapshot/{symbol}")
def record_qmi_smart_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
    force: bool = Query(default=False),
):
    """
    DE-CORE-006.1 — Policy-controlled persistence.

    Computes DE-CORE-005.2, asks Snapshot Policy whether the observation is
    material, and writes only when the policy returns SAVE.

    force=True bypasses materiality checks but still uses the same repository.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    try:
        policy_response = _build_policy_response(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        policy_response, price_capture = _capture_price(
            normalized_symbol,
            policy_response,
        )

        previous = history_service.latest_snapshot(normalized_symbol)

        snapshot_policy = snapshot_policy_service.evaluate(
            symbol=normalized_symbol,
            action_policy_response=policy_response,
            previous_snapshot=previous,
            force=force,
        )

        persistence = None

        if snapshot_policy["should_save"]:
            persistence = history_service.record_snapshot(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                action_policy_response=policy_response,
            )

        return {
            "symbol": normalized_symbol,
            "engine": snapshot_policy_service.ENGINE,
            "engine_id": snapshot_policy_service.ENGINE_ID,
            "version": snapshot_policy_service.VERSION,
            "status": "operational",
            "source_policy_engine_id": policy_response.get("engine_id"),
            "decision_price_capture": price_capture,
            "snapshot_policy": snapshot_policy,
            "persistence": persistence,
        }

    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to process smart QMI snapshot. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get("/decision-history/{symbol}")
def get_qmi_decision_history(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """DE-CORE-006.0 — Read persistent QMI decision snapshots."""
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    history = history_service.history(normalized_symbol, limit=limit)

    return {
        "symbol": normalized_symbol,
        "engine_id": history_service.ENGINE_ID,
        "count": len(history),
        "history": history,
    }


@router.get("/decision-transitions/{symbol}")
def get_qmi_decision_transitions(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """DE-CORE-006.0 — Read real QMI action-change audit events only."""
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    transitions = history_service.transitions(normalized_symbol, limit=limit)

    return {
        "symbol": normalized_symbol,
        "engine_id": history_service.ENGINE_ID,
        "count": len(transitions),
        "transitions": transitions,
    }


@router.get("/decision-history-summary/{symbol}")
def get_qmi_decision_history_summary(symbol: str):
    """DE-CORE-006.0 — Persistent QMI decision-history summary."""
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    return {
        "engine_id": history_service.ENGINE_ID,
        **history_service.summary(normalized_symbol),
    }

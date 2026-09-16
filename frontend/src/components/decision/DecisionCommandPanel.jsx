import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Ban,
  CheckCircle2,
  CircleDot,
  ShieldAlert,
  Target,
  TrendingDown,
  Zap,
} from "lucide-react";

function pretty(value) {
  if (value === null || value === undefined || value === "") return "--";
  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(digits)}%`;
}

function formatScore(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const n = Number(value);
  return `${n > 0 ? "+" : ""}${n.toFixed(digits)}`;
}

function permissionValue(permissions, key) {
  const value = permissions?.[key] ?? permissions?.[String(key).toUpperCase()] ?? "--";
  return typeof value === "object"
    ? value?.state || value?.permission || value?.status || "--"
    : value;
}

function permissionTone(value) {
  const normalized = String(value || "").toUpperCase();
  if (["PRIMARY", "PERMITTED", "ALLOWED"].includes(normalized)) return "is-positive";
  if (["BLOCKED", "PROHIBITED", "HARD_BLOCK", "DENIED"].includes(normalized)) return "is-negative";
  if (["CONDITIONAL", "WATCH", "WAIT"].includes(normalized)) return "is-watch";
  return "";
}

function postureTone(value) {
  const normalized = String(value || "").toUpperCase();
  if (["ENTER", "ADD", "BUY", "ACCUMULATE"].includes(normalized)) return "is-positive";
  if (["REDUCE", "EXIT", "SELL", "DEFENSIVE"].includes(normalized)) return "is-negative";
  return "is-watch";
}

function blockerText(item) {
  if (!item) return "--";
  return item?.reason || item?.type || String(item);
}

function conditionText(item) {
  if (!item) return "--";
  if (typeof item === "string") return pretty(item);
  return item?.target || item?.condition || "--";
}

function driverTone(score) {
  const n = Number(score);
  if (n > 8) return "is-positive";
  if (n < -8) return "is-negative";
  return "is-neutral";
}

function driverPosition(score) {
  const n = Math.max(-100, Math.min(100, Number(score) || 0));
  return `${((n + 100) / 200) * 100}%`;
}

function evolutionTone(value) {
  const state = String(value || "").toUpperCase();
  if (["RECOVERING", "IMPROVING"].includes(state)) return "is-positive";
  if (state === "DETERIORATING") return "is-negative";
  if (state === "MIXED") return "is-watch";
  return "is-neutral";
}

function signedDelta(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const n = Number(value);
  return `${n > 0 ? "+" : ""}${n.toFixed(1)}`;
}

function driverWidth(score) {
  const n = Math.min(100, Math.abs(Number(score) || 0));
  return `${n / 2}%`;
}

function sparklinePoints(values, width = 240, height = 42) {
  const clean = values.map((value) => Number(value)).filter(Number.isFinite);
  if (!clean.length) return "";
  const min = Math.min(...clean), max = Math.max(...clean), range = max - min || 1;
  return clean.map((value, index) => {
    const x = clean.length === 1 ? width / 2 : (index / (clean.length - 1)) * width;
    const y = height - ((value - min) / range) * (height - 8) - 4;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function MiniTimeline({ label, values, suffix = "", invert = false }) {
  const clean = values.map(Number).filter(Number.isFinite);
  const first = clean[0], last = clean[clean.length - 1];
  const delta = Number.isFinite(first) && Number.isFinite(last) ? last - first : null;
  const points = sparklinePoints(clean).split(" ");

  const percentMetric = suffix === "%";
  const min = percentMetric || invert ? 0 : -100;
  const max = 100;
  const clamped = Number.isFinite(last) ? Math.max(min, Math.min(max, last)) : min;
  const markerPct = ((clamped - min) / (max - min)) * 100;

  const tone = invert
    ? clamped >= 70 ? "is-negative" : clamped >= 40 ? "is-warning" : "is-positive"
    : percentMetric
      ? clamped >= 60 ? "is-positive" : clamped >= 35 ? "is-warning" : "is-negative"
      : clamped <= -60 ? "is-negative" : clamped < 20 ? "is-warning" : "is-positive";

  const scaleLabels = invert
    ? ["Low", "Moderate", "High"]
    : percentMetric
      ? (label === "Transition" ? ["Unstable", "Transitioning", "Stable"] : ["Low", "Neutral", "High"])
      : ["Bearish", "Neutral", "Bullish"];

  return (
    <div className={`qmi-command__timeline-row qmi-command__timeline-row--visual ${tone}`}>
      <div className="qmi-command__timeline-label">
        <strong>{label}</strong>
        <span>{Number.isFinite(last) ? `${last.toFixed(1)}${suffix}` : "--"}</span>
      </div>
      <div className="qmi-command__trajectory">
        <div className="qmi-command__trajectory-bar">
          <div className="qmi-command__trajectory-marker" style={{ left: `${markerPct}%` }} />
        </div>
        <div className="qmi-command__trajectory-scale">
          <span>{scaleLabels[0]}</span><span>{scaleLabels[1]}</span><span>{scaleLabels[2]}</span>
        </div>
        <svg viewBox="0 0 240 24" preserveAspectRatio="none" aria-hidden="true">
          <polyline points={points.join(" ")} />
        </svg>
      </div>
      <div className="qmi-command__timeline-delta">{signedDelta(delta)}</div>
    </div>
  );
}

/* FE-CORE-001: typography governed by styles/qmi-typography.css */
export default function DecisionCommandPanel({
  symbol = "",
  decisionSynthesis = null,
  executionPlan = null,
  confluence = null,
  decisionEvolution = null,
  evolutionTimeline = null,
  decisionChangeAttribution = null,
  decisionConfidenceDecomposition = null,
  decisionReliability = null,
  decisionReliabilityBreakdown = null,
  decisionOutcome = null,
  decisionCalibration = null,
  decisionMemory = null,
  historicalOutcomeMemory = null,
  historicalEdge = null,
  decisionEvidenceAlignment = null,
  decisionEvidenceScore = null,
  decisionEvidenceGate = null,
  decisionValidationState = null,
  decisionValidationMomentum = null,
  decisionContradictionGuard = null,
  shadowAdaptiveDecision = null,
  decisionIntelligenceQualityControl = null,
  loading = false,
  error = "",
}) {
  const core =
    decisionSynthesis?.technical_decision_synthesis ||
    decisionSynthesis?.decision_synthesis ||
    {};

  const execution =
    executionPlan?.technical_execution_plan ||
    executionPlan?.execution_plan ||
    executionPlan ||
    {};

  const evolution = decisionEvolution?.decision_evolution || {};
  const evolutionTrajectory = evolution?.trajectory || {};
  const evolutionPrevious = evolution?.previous || {};
  const evolutionCurrent = evolution?.current || {};
  const evolutionDeltas = evolution?.deltas || {};
  const evolutionSignals = evolution?.signals || {};
  const evolutionBaseline = evolution?.baseline || {};
  const timeline = evolutionTimeline || {};
  const timelinePoints = Array.isArray(timeline?.state_points) ? timeline.state_points : [];
  const timelineDrivers = timeline?.driver_series || {};
  const attribution = decisionChangeAttribution?.decision_change_attribution || {};
  const attributionPressure = attribution?.pressure || {};
  const postureChange = attribution?.posture_change || {};
  const confidenceDecomposition = decisionConfidenceDecomposition?.decision_confidence_decomposition || {};
  const confidenceComponents = confidenceDecomposition?.components || {};
  const reliability = decisionReliability?.decision_reliability || {};
  const reliabilityHorizons = Array.isArray(reliability?.horizons) ? reliability.horizons : [];
  const reliabilityBreakdown = decisionReliabilityBreakdown?.reliability_breakdown || {};
  const outcome = decisionOutcome?.decision_outcome || {};
  const outcomePostures = Array.isArray(outcome?.by_posture) ? outcome.by_posture : [];
  const calibration = decisionCalibration?.decision_calibration || {};
  const memory = decisionMemory?.decision_memory || {};
  const memoryMatches = Array.isArray(memory?.matches) ? memory.matches : [];
  const outcomeMemory = historicalOutcomeMemory?.historical_outcome_memory || {};
  const outcomeMemoryHorizons = Array.isArray(outcomeMemory?.horizons) ? outcomeMemory.horizons : [];
  const edge = historicalEdge?.historical_edge || {};
  const edgeHorizons = Array.isArray(edge?.horizons) ? edge.horizons : [];
  const alignment = decisionEvidenceAlignment?.decision_evidence_alignment || {};
  const evidenceScore = decisionEvidenceScore?.decision_evidence_score || {};
  const liveEvidenceComponents = evidenceScore?.live_evidence?.components || {};
  const evidenceGate = decisionEvidenceGate?.decision_evidence_gate || {};
  const evidenceGateChecks = Array.isArray(evidenceGate?.checks) ? evidenceGate.checks : [];
  const validationState = decisionValidationState?.decision_validation_state || {};
  const validationHistory = Array.isArray(validationState?.state_history) ? validationState.state_history : [];
  const validationMomentum = decisionValidationMomentum?.decision_validation_momentum || {};
  const contradictionGuard = decisionContradictionGuard?.decision_contradiction_guard || {};
  const contradictionItems = Array.isArray(contradictionGuard?.contradictions) ? contradictionGuard.contradictions : [];
  const shadowAdaptive = shadowAdaptiveDecision?.shadow_adaptive_decision || {};
  const qualityControl = decisionIntelligenceQualityControl?.decision_intelligence_quality_control || {};
  const qualityChecks = Array.isArray(qualityControl?.checks) ? qualityControl.checks : [];

  const transition = core?.transition || {};
  const marketContext = core?.market_context || {};
  const trace = core?.decision_trace || {};
  const permissions =
    trace?.action_permissions ||
    core?.action_permissions ||
    execution?.action_matrix ||
    {};

  const confluenceCore = confluence?.technical_confluence || {};
  const confluenceDiagnostics = confluenceCore?.diagnostics || {};
  const engineContributions = Array.isArray(confluenceDiagnostics?.engine_contributions)
    ? confluenceDiagnostics.engine_contributions
    : [];
  const decisionDrivers = engineContributions
    .filter((item) => item?.available !== false && Number.isFinite(Number(item?.score)))
    .sort((a, b) => Math.abs(Number(b?.normalized_contribution ?? b?.score ?? 0)) - Math.abs(Number(a?.normalized_contribution ?? a?.score ?? 0)))
    .slice(0, 7);

  const dominantDriver =
    confluenceDiagnostics?.largest_abs_contribution ||
    confluenceDiagnostics?.dominant_negative_engine ||
    confluenceDiagnostics?.dominant_positive_engine ||
    decisionDrivers[0] ||
    null;

  const blockers = Array.isArray(core?.blockers) ? core.blockers : [];
  const activationConditions = Array.isArray(execution?.activation_conditions)
    ? execution.activation_conditions
    : [];
  const deescalationPath = Array.isArray(execution?.deescalation_path)
    ? execution.deescalation_path
    : [];

  const posture = core?.final_posture || trace?.final_posture || "--";
  const conviction = core?.conviction ?? core?.conviction_score;
  const risk = core?.risk_state || core?.risk || execution?.execution_state?.risk_state || "--";
  const timing = core?.timing || "--";
  const currentState =
    transition?.current_state ||
    core?.current_state ||
    execution?.execution_state?.state ||
    "--";
  const targetState =
    transition?.target_state ||
    transition?.next_state ||
    core?.target_state ||
    "--";
  const scenario =
    marketContext?.primary_scenario ||
    core?.primary_scenario ||
    execution?.source_context?.primary_scenario ||
    "--";
  const direction =
    marketContext?.direction_score ??
    core?.direction_score ??
    execution?.source_context?.direction_score;
  const executionConfidence =
    marketContext?.execution_confidence ??
    core?.execution_confidence ??
    execution?.execution_confidence?.score;
  const transitionProbability =
    transition?.probability ??
    transition?.transition_probability ??
    0;
  const transitionReadiness =
    transition?.readiness ??
    transition?.transition_readiness ??
    0;
  const maturityPhase =
    transition?.maturity_phase ||
    core?.maturity_phase ||
    "--";
  const rationale =
    core?.rationale ||
    "QMI has synthesized the technical decision pipeline into the current posture.";

  const actionKeys = ["WAIT", "ENTER", "ADD", "REDUCE", "EXIT"];
  const changeConditions = activationConditions.length
    ? activationConditions.slice(0, 5)
    : deescalationPath.slice(0, 5).map((condition) => ({ target: condition }));

  if (loading && !decisionSynthesis) {
    return (
      <section className="qmi-command qmi-command--status">
        <Activity size={18} /> Building Decision Intelligence...
      </section>
    );
  }

  if (error) {
    return (
      <section className="qmi-command qmi-command--status is-error">
        <AlertTriangle size={18} /> Decision Intelligence unavailable: {error}
      </section>
    );
  }

  return (
    <section className={`qmi-command ${postureTone(posture)}`}>
      <style>{`

        /* FE-DI-004 — Decision Intelligence Visual Rework */
        .qmi-command{font-size:14px!important;line-height:1.45!important}
        .qmi-command__eyebrow,.qmi-command__card-title,.qmi-command__evolution-head span,
        .qmi-command__confidence-decomp-head span,.qmi-command__attribution-head span,
        .qmi-command__timeline-head span,.qmi-command__driver-evolution-title{
          font-size:11px!important;line-height:1.3!important;letter-spacing:.065em!important
        }
        .qmi-command__title,.qmi-command__decision strong{font-size:28px!important;line-height:1.05!important}
        .qmi-command__subtitle,.qmi-command__decision p,.qmi-command__summary,.qmi-command__evolution-note,
        .qmi-command__attribution-summary{font-size:14px!important;line-height:1.55!important}
        .qmi-command__metric span,.qmi-command__mini span,.qmi-command__state-box span,
        .qmi-command__confidence-source span,.qmi-command__cause>span{font-size:10px!important}
        .qmi-command__metric strong,.qmi-command__mini strong{font-size:18px!important}
        .qmi-command__state-box strong{font-size:15px!important}
        .qmi-command__driver-name,.qmi-command__driver strong,
        .qmi-command__driver-evolution-row strong{font-size:12px!important}
        .qmi-command__driver span,.qmi-command__driver small,.qmi-command__driver em,
        .qmi-command__driver-evolution-row span,.qmi-command__driver-evolution-row em,
        .qmi-command__driver-evolution-head span,.qmi-command__driver-evolution-summary{
          font-size:10px!important
        }
        .qmi-command__driver-evolution-row{min-height:34px!important;padding:7px 6px!important}
        .qmi-command__evolution{padding:20px!important}
        .qmi-command__evolution-head strong{font-size:19px!important}
        .qmi-command__evolution-score{font-size:22px!important}
        .qmi-command__evolution-states{gap:12px!important}
        .qmi-command__evolution-state{padding:14px!important;min-height:72px!important}
        .qmi-command__evolution-state span{font-size:10px!important}
        .qmi-command__evolution-state strong{font-size:14px!important}
        .qmi-command__evolution-state small{font-size:10px!important}
        .qmi-command__evolution-metric{padding:12px!important;min-height:76px!important}
        .qmi-command__evolution-metric>span{font-size:10px!important}
        .qmi-command__evolution-metric small,.qmi-command__evolution-metric strong{font-size:13px!important}
        .qmi-command__evolution-metric em{font-size:10px!important}
        .qmi-command__reliability{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.12);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__reliability-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:16px}
        .qmi-command__reliability-head span{display:block;color:#5b8cff;font-size:11px;font-weight:950;letter-spacing:.065em;text-transform:uppercase}
        .qmi-command__reliability-head strong{display:block;margin-top:4px;color:#dce6f2;font-size:20px;font-weight:950}
        .qmi-command__reliability-score{text-align:right}.qmi-command__reliability-score strong{font-size:30px;color:#e8eef7}.qmi-command__reliability-score span{font-size:11px;color:#8292a7}
        .qmi-command__reliability-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}
        .qmi-command__reliability-horizon{padding:14px;border:1px solid rgba(148,163,184,.08);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__reliability-horizon>span{font-size:10px;color:#77879b;font-weight:900;text-transform:uppercase}
        .qmi-command__reliability-horizon strong{display:block;margin-top:5px;font-size:20px;color:#dce6f2}
        .qmi-command__reliability-horizon small{display:block;margin-top:4px;font-size:10px;color:#8493a7}
        .qmi-command__reliability-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
        .qmi-command__reliability-meta span{padding:7px 9px;border-radius:7px;background:rgba(148,163,184,.05);font-size:10px;color:#9cabbc;font-weight:850}
        @media(max-width:760px){.qmi-command__reliability-grid{grid-template-columns:1fr}}
        .qmi-command__reliability-breakdown{margin-top:10px;padding:20px;border:1px solid rgba(148,163,184,.09);border-radius:12px;background:rgba(2,6,23,.14)}
        .qmi-command__reliability-breakdown h3{margin:0;color:#dce6f2;font-size:18px}.qmi-command__reliability-breakdown>span{display:block;color:#5b8cff;font-size:11px;font-weight:950;letter-spacing:.065em;text-transform:uppercase;margin-bottom:4px}
        .qmi-command__segment-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:14px}.qmi-command__segment{padding:13px;border:1px solid rgba(148,163,184,.08);border-radius:9px}.qmi-command__segment span{font-size:10px;color:#8292a7;font-weight:900}.qmi-command__segment strong{display:block;margin-top:5px;font-size:18px;color:#dce6f2}.qmi-command__segment small{font-size:10px;color:#77879b}
        .qmi-command__segment-note{margin-top:12px;font-size:12px;line-height:1.5;color:#9cabbc}@media(max-width:760px){.qmi-command__segment-grid{grid-template-columns:1fr}}
        .qmi-command__confidence-decomp{padding:20px!important}
        .qmi-command__confidence-decomp-head{margin-bottom:18px!important}
        .qmi-command__confidence-decomp-head strong{font-size:20px!important}
        .qmi-command__confidence-score strong{font-size:30px!important}
        .qmi-command__confidence-score span{font-size:11px!important;margin-top:3px!important}
        .qmi-command__confidence-bars{gap:13px!important}
        .qmi-command__confidence-row{grid-template-columns:190px minmax(160px,1fr) 62px!important;gap:14px!important}
        .qmi-command__confidence-row>span{font-size:12px!important;color:#b7c5d8!important}
        .qmi-command__confidence-track{height:10px!important}
        .qmi-command__confidence-row>strong{font-size:12px!important}
        .qmi-command__confidence-footer{gap:12px!important;margin-top:18px!important}
        .qmi-command__confidence-source{padding:13px!important}
        .qmi-command__confidence-source strong{font-size:13px!important;margin-top:5px!important}
        .qmi-command__attribution{padding:20px!important}
        .qmi-command__attribution-head strong{font-size:19px!important}
        .qmi-command__attribution-pressure{padding:8px 11px!important;font-size:11px!important}
        .qmi-command__attribution-grid{gap:12px!important}
        .qmi-command__cause{padding:13px!important;min-height:76px!important}
        .qmi-command__cause strong{font-size:14px!important}
        .qmi-command__cause em{font-size:11px!important}
        .qmi-command__metric-pressure{gap:8px!important;margin-top:13px!important}
        .qmi-command__metric-pressure span{padding:7px 9px!important;font-size:10px!important}
        .qmi-command__timeline{padding:20px!important}
        .qmi-command__timeline-head strong{font-size:17px!important}
        .qmi-command__timeline-head>div:last-child{font-size:10px!important}
        .qmi-command__timeline-row{grid-template-columns:110px minmax(140px,1fr) 58px!important;min-height:66px!important;padding:10px 12px!important}
        .qmi-command__timeline-label strong{font-size:11px!important}
        .qmi-command__timeline-label span,.qmi-command__timeline-delta{font-size:10px!important}
        .qmi-command__timeline-drivers-title{font-size:10px!important}
        @media(max-width:900px){
          .qmi-command__confidence-row{grid-template-columns:135px minmax(100px,1fr) 52px!important}
        }
        .qmi-command {
          position:relative;
          overflow:hidden;
          padding:20px;
          border:1px solid rgba(148,163,184,.15);
          border-radius:18px;
          background:
            radial-gradient(circle at 92% 0%, rgba(59,130,246,.14), transparent 26%),
            linear-gradient(145deg, rgba(12,19,33,.97), rgba(8,13,24,.94));
          box-shadow:0 20px 46px rgba(2,6,23,.15);
        }
        .qmi-command::before {
          content:"";
          position:absolute;
          left:0; top:0; bottom:0;
          width:4px;
          background:#f4c542;
        }
        .qmi-command.is-positive::before { background:#31d890; }
        .qmi-command.is-negative::before { background:#ff6178; }

        .qmi-command--status {
          display:flex; align-items:center; gap:9px;
          color:#9aa8ba; font-size:13px; font-weight:850;
        }
        .qmi-command--status.is-error { color:#ff8798; }

        .qmi-command__header {
          display:flex; align-items:flex-start; justify-content:space-between;
          gap:18px; margin-bottom:15px;
        }
        .qmi-command__kicker {
          color:#60a5fa; font-size:9px; font-weight:950;
          letter-spacing:.105em; text-transform:uppercase;
        }
        .qmi-command__header h2 {
          margin:4px 0 0; font-size:21px; line-height:1.15;
          font-weight:950; letter-spacing:-.025em;
        }
        .qmi-command__live {
          display:flex; align-items:center; gap:6px;
          padding:7px 9px; border:1px solid rgba(49,216,144,.13);
          border-radius:9px; color:#7ee7b6; background:rgba(49,216,144,.045);
          font-size:9px; font-weight:950; letter-spacing:.06em; text-transform:uppercase;
          white-space:nowrap;
        }

        .qmi-command__grid {
          display:grid;
          grid-template-columns:minmax(250px,.9fr) minmax(340px,1.35fr);
          gap:10px;
        }
        .qmi-command__card {
          min-width:0;
          border:1px solid rgba(148,163,184,.105);
          border-radius:13px;
          background:rgba(148,163,184,.025);
          padding:15px;
        }
        .qmi-command__card-title {
          display:flex; align-items:center; gap:7px;
          color:#8191a8; font-size:9px; font-weight:950;
          letter-spacing:.075em; text-transform:uppercase;
          margin-bottom:10px;
        }

        .qmi-command__directive {
          display:flex; flex-direction:column; justify-content:space-between;
          min-height:230px;
          background:
            radial-gradient(circle at 80% 12%, rgba(255,97,120,.09), transparent 32%),
            rgba(2,6,23,.16);
        }
        .qmi-command__posture {
          margin:4px 0 6px;
          color:#f4c542;
          font-size:44px; line-height:.95; font-weight:950;
          letter-spacing:-.05em; text-transform:uppercase;
        }
        .qmi-command.is-negative .qmi-command__posture { color:#ff6178; }
        .qmi-command.is-positive .qmi-command__posture { color:#31d890; }
        .qmi-command__directive-text {
          color:#a8b5c7; font-size:11px; line-height:1.45; font-weight:750;
        }
        .qmi-command__transition {
          display:flex; align-items:center; flex-wrap:wrap; gap:6px;
          margin-top:12px; color:#8ea0b7; font-size:10px; font-weight:850;
        }
        .qmi-command__metrics {
          display:grid; grid-template-columns:repeat(2,minmax(0,1fr));
          gap:6px; margin-top:14px;
        }
        .qmi-command__metric {
          padding:9px 10px; border:1px solid rgba(148,163,184,.08);
          border-radius:9px; background:rgba(148,163,184,.025);
        }
        .qmi-command__metric span {
          display:block; color:#728197; font-size:8px; font-weight:900;
          letter-spacing:.06em; text-transform:uppercase;
        }
        .qmi-command__metric strong {
          display:block; margin-top:4px; color:#eef4fb;
          font-size:13px; font-weight:950;
        }

        .qmi-command__why { min-height:230px; }
        .qmi-command__rationale {
          color:#c4cfdd; font-size:13px; line-height:1.52; font-weight:800;
          margin-bottom:12px;
        }
        .qmi-command__scenario {
          display:grid; grid-template-columns:1.4fr .6fr;
          gap:7px; margin-bottom:10px;
        }
        .qmi-command__scenario-box {
          padding:10px 11px; border:1px solid rgba(148,163,184,.09);
          border-radius:9px; background:rgba(2,6,23,.12);
        }
        .qmi-command__scenario-box span {
          display:block; color:#77879d; font-size:8px; font-weight:900;
          letter-spacing:.06em; text-transform:uppercase;
        }
        .qmi-command__scenario-box strong {
          display:block; margin-top:4px; color:#f0f5fb; font-size:12px; font-weight:950;
        }
        .qmi-command__blockers { display:grid; gap:5px; }
        .qmi-command__blocker {
          display:flex; align-items:flex-start; gap:7px;
          padding:7px 8px; border:1px solid rgba(255,97,120,.10);
          border-radius:8px; background:rgba(255,97,120,.045);
          color:#ff8798; font-size:9.5px; line-height:1.35; font-weight:800;
        }
        .qmi-command__blocker svg { margin-top:1px; flex:0 0 auto; }

        .qmi-command__evolution {
          margin-top:10px; padding:14px 15px; border:1px solid rgba(148,163,184,.10);
          border-radius:12px; background:rgba(148,163,184,.022);
        }
        .qmi-command__evolution.is-positive { border-color:rgba(49,216,144,.14); background:rgba(49,216,144,.028); }
        .qmi-command__evolution.is-negative { border-color:rgba(255,97,120,.14); background:rgba(255,97,120,.028); }
        .qmi-command__evolution.is-watch { border-color:rgba(244,197,66,.14); }
        .qmi-command__evolution-head { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:10px; }
        .qmi-command__evolution-head span { display:block; color:#718198; font-size:8px; font-weight:950; letter-spacing:.065em; text-transform:uppercase; }
        .qmi-command__evolution-head strong { display:block; margin-top:3px; color:#dfe8f3; font-size:14px; font-weight:950; }
        .qmi-command__evolution-score { color:#91a1b6; font-size:17px; font-weight:950; }
        .qmi-command__evolution.is-positive .qmi-command__evolution-head strong,
        .qmi-command__evolution.is-positive .qmi-command__evolution-score { color:#31d890; }
        .qmi-command__evolution.is-negative .qmi-command__evolution-head strong,
        .qmi-command__evolution.is-negative .qmi-command__evolution-score { color:#ff6178; }
        .qmi-command__evolution.is-watch .qmi-command__evolution-head strong,
        .qmi-command__evolution.is-watch .qmi-command__evolution-score { color:#f4c542; }
        .qmi-command__evolution-flow { display:grid; grid-template-columns:1fr auto 1fr; gap:8px; align-items:center; margin-bottom:9px; }
        .qmi-command__evolution-flow > div { padding:8px 10px; border:1px solid rgba(148,163,184,.08); border-radius:8px; background:rgba(2,6,23,.13); }
        .qmi-command__evolution-flow span,.qmi-command__evolution-metric > span { display:block; color:#718198; font-size:7.5px; font-weight:950; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-command__evolution-flow strong { display:block; margin-top:3px; color:#e8eef6; font-size:11px; font-weight:950; }
        .qmi-command__evolution-flow small { display:block; margin-top:3px; color:#607086; font-size:8px; font-weight:750; }
        .qmi-command__evolution-flow svg { color:#5f7087; }
        .qmi-command__evolution-metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:6px; }
        .qmi-command__evolution-metric { padding:8px 9px; border:1px solid rgba(148,163,184,.075); border-radius:8px; background:rgba(2,6,23,.10); }
        .qmi-command__evolution-metric > div { display:flex; align-items:center; gap:5px; margin-top:4px; }
        .qmi-command__evolution-metric small { color:#728197; font-size:9px; font-weight:850; }
        .qmi-command__evolution-metric strong { color:#e4ebf4; font-size:10px; font-weight:950; }
        .qmi-command__evolution-metric svg { color:#5c6b80; }
        .qmi-command__evolution-metric em { display:block; margin-top:4px; font-style:normal; color:#8290a4; font-size:7.5px; font-weight:850; }
        .qmi-command__evolution-metric.is-positive em { color:#31d890; }
        .qmi-command__evolution-metric.is-negative em { color:#ff6178; }
        .qmi-command__evolution-metric.is-watch em { color:#f4c542; }
        .qmi-command__timeline{padding:14px;border:1px solid rgba(91,140,255,.12);border-radius:12px;background:rgba(6,12,22,.42)}
        .qmi-command__timeline-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:12px}
        .qmi-command__timeline-head span{display:block;color:#5b8cff;font-size:8px;font-weight:950;letter-spacing:.08em;text-transform:uppercase}
        .qmi-command__timeline-head strong{display:block;margin-top:3px;color:#cbd6e5;font-size:11px;font-weight:900}
        .qmi-command__timeline-head>div:last-child{color:#718198;font-size:8px;font-weight:850}
        .qmi-command__timeline-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
        .qmi-command__timeline-row{display:grid;grid-template-columns:78px minmax(100px,1fr) 44px;gap:8px;align-items:center;min-height:54px;padding:7px 9px;border:1px solid rgba(148,163,184,.07);border-radius:9px;background:rgba(2,6,23,.22)}
        .qmi-command__timeline-label strong{display:block;color:#b8c5d6;font-size:8.5px;font-weight:900}.qmi-command__timeline-label span{display:block;margin-top:3px;color:#77879b;font-size:8px;font-weight:800}
        .qmi-command__timeline-row svg{width:100%;height:42px;overflow:visible}.qmi-command__timeline-row svg line{stroke:rgba(148,163,184,.08);stroke-width:1}.qmi-command__timeline-row svg polyline{fill:none;stroke:#8190a5;stroke-width:2;vector-effect:non-scaling-stroke}.qmi-command__timeline-row svg circle{fill:#8190a5}
        .qmi-command__timeline-row.is-positive svg polyline{stroke:#31d890}.qmi-command__timeline-row.is-positive svg circle{fill:#31d890}.qmi-command__timeline-row.is-negative svg polyline{stroke:#ff6178}.qmi-command__timeline-row.is-negative svg circle{fill:#ff6178}
        .qmi-command__timeline-delta{text-align:right;color:#8b99aa;font-size:9px;font-weight:950}.qmi-command__timeline-row.is-positive .qmi-command__timeline-delta{color:#31d890}.qmi-command__timeline-row.is-negative .qmi-command__timeline-delta{color:#ff6178}
        .qmi-command__timeline-drivers{margin-top:10px;padding-top:10px;border-top:1px solid rgba(148,163,184,.07);display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.qmi-command__timeline-drivers-title{grid-column:1/-1;color:#718198;font-size:8px;font-weight:950;letter-spacing:.08em;text-transform:uppercase}
        @media(max-width:900px){.qmi-command__timeline-grid,.qmi-command__timeline-drivers{grid-template-columns:1fr}}
        .qmi-command__evolution-note { margin-top:8px; padding-top:8px; border-top:1px solid rgba(148,163,184,.06); color:#8998ac; font-size:9px; line-height:1.4; font-weight:750; }
        .qmi-command__driver-evolution{margin-top:10px;padding-top:10px;border-top:1px solid rgba(148,163,184,.07)}
        .qmi-command__driver-evolution-head,.qmi-command__driver-evolution-row{display:grid;grid-template-columns:1.2fr .65fr .65fr 1fr;gap:8px;align-items:center}
        .qmi-command__driver-evolution-head{color:#65758a;font-size:7.5px;font-weight:950;text-transform:uppercase;margin-bottom:4px}
        .qmi-command__driver-evolution-row{padding:6px 0;border-top:1px solid rgba(148,163,184,.045);font-size:9px}
        .qmi-command__driver-evolution-row strong{color:#b9c6d6}.qmi-command__driver-evolution-row span{color:#8392a6}
        .qmi-command__driver-evolution-row em{font-style:normal;color:#8b99aa;font-weight:900}
        .qmi-command__driver-evolution-row.is-positive em{color:#31d890}.qmi-command__driver-evolution-row.is-negative em{color:#ff6178}
        .qmi-command__driver-evolution-summary{display:flex;justify-content:space-between;gap:10px;margin-top:7px;padding-top:7px;border-top:1px solid rgba(148,163,184,.06);color:#718198;font-size:8px;font-weight:850}
        .qmi-command__driver-evolution-summary strong{color:#d6e0ec}


        .qmi-command__confidence-decomp{margin-top:10px;padding:14px 15px;border:1px solid rgba(91,140,255,.12);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__confidence-decomp-head{display:flex;justify-content:space-between;gap:12px;margin-bottom:11px}.qmi-command__confidence-decomp-head span{display:block;color:#5b8cff;font-size:8px;font-weight:950;letter-spacing:.075em;text-transform:uppercase}.qmi-command__confidence-decomp-head strong{display:block;margin-top:3px;color:#dce6f2;font-size:13px;font-weight:950}
        .qmi-command__confidence-score{text-align:right}.qmi-command__confidence-score strong{display:block;color:#e8eef7;font-size:18px;font-weight:950}.qmi-command__confidence-score span{display:block;color:#7f8ea2;font-size:8px;font-weight:900}
        .qmi-command__confidence-bars{display:grid;gap:7px}.qmi-command__confidence-row{display:grid;grid-template-columns:150px minmax(100px,1fr) 48px;gap:9px;align-items:center}.qmi-command__confidence-row>span{color:#8f9eb1;font-size:8.5px;font-weight:850}.qmi-command__confidence-track{height:6px;overflow:hidden;border-radius:99px;background:rgba(148,163,184,.08)}.qmi-command__confidence-fill{height:100%;border-radius:99px;background:linear-gradient(90deg,#4f7fff,#65a1ff)}.qmi-command__confidence-row>strong{text-align:right;color:#c9d5e4;font-size:9px;font-weight:950}
        .qmi-command__confidence-footer{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:11px}.qmi-command__confidence-source{padding:8px 9px;border:1px solid rgba(148,163,184,.07);border-radius:8px;background:rgba(2,6,23,.14)}.qmi-command__confidence-source span{display:block;color:#68788d;font-size:7.5px;font-weight:900;text-transform:uppercase}.qmi-command__confidence-source strong{display:block;margin-top:3px;color:#b9c7d8;font-size:9px;font-weight:950}
        .qmi-command__attribution{margin-top:10px;padding:14px 15px;border:1px solid rgba(96,165,250,.12);border-radius:12px;background:rgba(59,130,246,.025)}
        .qmi-command__attribution-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:10px}
        .qmi-command__attribution-head span{display:block;color:#60a5fa;font-size:8px;font-weight:950;letter-spacing:.075em;text-transform:uppercase}
        .qmi-command__attribution-head strong{display:block;margin-top:3px;color:#dce6f2;font-size:13px;font-weight:950}
        .qmi-command__attribution-pressure{padding:6px 8px;border-radius:8px;color:#9aabbe;background:rgba(148,163,184,.05);font-size:9px;font-weight:950}
        .qmi-command__attribution-pressure.is-positive{color:#31d890;background:rgba(49,216,144,.05)}
        .qmi-command__attribution-pressure.is-negative{color:#ff6178;background:rgba(255,97,120,.05)}
        .qmi-command__attribution-pressure.is-watch{color:#f4c542}
        .qmi-command__attribution-summary{color:#aab8c9;font-size:10px;line-height:1.45;font-weight:800;margin-bottom:10px}
        .qmi-command__attribution-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
        .qmi-command__cause{padding:9px 10px;border:1px solid rgba(148,163,184,.075);border-radius:9px;background:rgba(2,6,23,.13)}
        .qmi-command__cause>span{display:block;color:#718198;font-size:7.5px;font-weight:950;text-transform:uppercase;letter-spacing:.055em}
        .qmi-command__cause strong{display:block;margin-top:4px;color:#dce5ef;font-size:10px;font-weight:950}
        .qmi-command__cause em{display:block;margin-top:3px;color:#7e8da1;font-size:8px;font-style:normal;font-weight:850}
        .qmi-command__cause.is-positive strong,.qmi-command__cause.is-positive em{color:#31d890}
        .qmi-command__cause.is-negative strong,.qmi-command__cause.is-negative em{color:#ff6178}
        .qmi-command__metric-pressure{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px}
        .qmi-command__metric-pressure span{padding:5px 7px;border-radius:7px;background:rgba(148,163,184,.045);color:#8493a7;font-size:8px;font-weight:850}
        .qmi-command__metric-pressure span.is-positive{color:#31d890}.qmi-command__metric-pressure span.is-negative{color:#ff6178}
        @media(max-width:760px){.qmi-command__attribution-grid{grid-template-columns:1fr}}
        .qmi-command__bottom {
          display:grid; grid-template-columns:1fr 1fr;
          gap:10px; margin-top:10px;
        }
        .qmi-command__permissions {
          display:grid; grid-template-columns:repeat(5,minmax(0,1fr));
          gap:5px;
        }
        .qmi-command__permission {
          min-width:0; padding:9px 8px;
          border:1px solid rgba(148,163,184,.09);
          border-radius:8px; background:rgba(2,6,23,.12);
        }
        .qmi-command__permission span {
          display:block; color:#75849a; font-size:8px; font-weight:950;
          letter-spacing:.06em; text-transform:uppercase;
        }
        .qmi-command__permission strong {
          display:flex; align-items:center; gap:5px; margin-top:4px;
          color:#cbd5e1; font-size:10px; font-weight:950;
          overflow-wrap:anywhere;
        }
        .qmi-command__permission.is-positive strong { color:#31d890; }
        .qmi-command__permission.is-negative strong { color:#ff6178; }
        .qmi-command__permission.is-watch strong { color:#f4c542; }

        .qmi-command__state-box {
          margin-top:18px;
          padding:12px;
          border:1px solid rgba(96,165,250,.11);
          border-radius:10px;
          background:rgba(59,130,246,.035);
        }
        .qmi-command__state-head {
          display:flex; align-items:center; justify-content:space-between; gap:10px;
          margin-bottom:10px;
        }
        .qmi-command__state-head span {
          color:#74849a; font-size:8px; font-weight:950;
          letter-spacing:.06em; text-transform:uppercase;
        }
        .qmi-command__state-head strong {
          color:#60a5fa; font-size:12px; font-weight:950;
        }
        .qmi-command__state-flow {
          display:grid; grid-template-columns:1fr auto 1fr;
          gap:8px; align-items:center;
        }
        .qmi-command__state-flow > div {
          padding:9px 10px; border-radius:8px;
          background:rgba(2,6,23,.14);
          border:1px solid rgba(148,163,184,.08);
        }
        .qmi-command__state-flow span {
          display:block; color:#728197; font-size:8px; font-weight:900;
          letter-spacing:.05em; text-transform:uppercase;
        }
        .qmi-command__state-flow strong {
          display:block; margin-top:4px; color:#e9f0f8;
          font-size:11px; font-weight:950;
        }
        .qmi-command__state-flow svg { color:#5f7087; }
        .qmi-command__state-meta {
          display:flex; justify-content:space-between; gap:10px;
          margin-top:8px; color:#738298; font-size:8px; font-weight:800;
        }
        .qmi-command__state-meta strong { color:#b9c7d8; }

        .qmi-command__dominant {
          display:grid; grid-template-columns:1.3fr .85fr .85fr;
          gap:8px; padding:10px 11px; margin-top:10px;
          border:1px solid rgba(255,97,120,.12);
          border-radius:9px; background:rgba(255,97,120,.035);
        }
        .qmi-command__dominant.is-positive {
          border-color:rgba(49,216,144,.13);
          background:rgba(49,216,144,.035);
        }
        .qmi-command__dominant.is-neutral {
          border-color:rgba(244,197,66,.13);
          background:rgba(244,197,66,.035);
        }
        .qmi-command__dominant span {
          display:block; color:#75849a; font-size:7.5px; font-weight:950;
          letter-spacing:.055em; text-transform:uppercase;
        }
        .qmi-command__dominant strong {
          display:block; margin-top:3px; color:#ff6178; font-size:10px; font-weight:950;
        }
        .qmi-command__dominant.is-positive strong { color:#31d890; }
        .qmi-command__dominant.is-neutral strong { color:#f4c542; }

        .qmi-command__drivers-axis {
          display:grid; grid-template-columns:repeat(5,1fr);
          margin:9px 48px 2px 97px;
          color:#5e6e83; font-size:7px; font-weight:850;
        }
        .qmi-command__drivers-axis span:nth-child(1){text-align:left;}
        .qmi-command__drivers-axis span:nth-child(2),
        .qmi-command__drivers-axis span:nth-child(3),
        .qmi-command__drivers-axis span:nth-child(4){text-align:center;}
        .qmi-command__drivers-axis span:nth-child(5){text-align:right;}

        .qmi-command__drivers {
          display:grid; gap:8px; margin-top:12px;
        }
        .qmi-command__driver {
          display:grid; grid-template-columns:88px minmax(0,1fr) 48px;
          gap:9px; align-items:center;
        }
        .qmi-command__driver-label {
          color:#9cacbf; font-size:9px; line-height:1.1; font-weight:900;
          text-transform:uppercase; letter-spacing:.035em;
          overflow:hidden; text-overflow:ellipsis; white-space:nowrap;
        }
        .qmi-command__driver-score {
          text-align:right; color:#cbd5e1; font-size:10px; font-weight:950;
        }
        .qmi-command__driver.is-negative .qmi-command__driver-score { color:#ff6178; }
        .qmi-command__driver.is-positive .qmi-command__driver-score { color:#31d890; }
        .qmi-command__driver.is-neutral .qmi-command__driver-score { color:#f4c542; }
        .qmi-command__driver-track {
          position:relative; height:8px; border-radius:999px;
          background:
            linear-gradient(to right,
              transparent 24.8%, rgba(148,163,184,.12) 25%, transparent 25.2%,
              transparent 49.8%, rgba(226,232,240,.34) 50%, transparent 50.2%,
              transparent 74.8%, rgba(148,163,184,.12) 75%, transparent 75.2%
            ),
            rgba(148,163,184,.09);
          overflow:hidden;
        }
        .qmi-command__driver-track::after {
          content:""; position:absolute; left:50%; top:-2px; bottom:-2px;
          width:1px; background:rgba(226,232,240,.38); z-index:2;
        }
        .qmi-command__driver-fill {
          position:absolute; top:0; bottom:0; border-radius:999px;
          background:#f4c542;
        }
        .qmi-command__driver.is-negative .qmi-command__driver-fill { background:#ff6178; }
        .qmi-command__driver.is-positive .qmi-command__driver-fill { background:#31d890; }
        .qmi-command__driver-meta {
          grid-column:2 / 4; margin-top:-5px;
          color:#66768c; font-size:8px; font-weight:750;
        }

        .qmi-command__conditions { display:grid; gap:5px; }
        .qmi-command__condition {
          display:grid; grid-template-columns:22px minmax(0,1fr);
          align-items:center; gap:7px;
          padding:6px 7px; border:1px solid rgba(96,165,250,.09);
          border-radius:8px; background:rgba(59,130,246,.035);
        }
        .qmi-command__condition-index {
          width:22px; height:22px; display:grid; place-items:center;
          border-radius:7px; color:#60a5fa; background:rgba(59,130,246,.08);
          font-size:8px; font-weight:950;
        }
        .qmi-command__condition strong {
          display:block; color:#c9d4e2; font-size:10px; line-height:1.3; font-weight:850;
        }
        .qmi-command__condition small {
          display:block; margin-top:2px; color:#738298; font-size:8px; font-weight:750;
        }

        @media(max-width:1100px){
          .qmi-command__grid,.qmi-command__bottom{grid-template-columns:1fr;}
        }
        @media(max-width:760px){
          .qmi-command__permissions{grid-template-columns:repeat(2,minmax(0,1fr));}
          .qmi-command__posture{font-size:36px;}
          .qmi-command__dominant{grid-template-columns:1fr;}
          .qmi-command__drivers-axis{margin-left:0;}
          .qmi-command__evolution-metrics{grid-template-columns:repeat(2,minmax(0,1fr));}
        }
        @media(max-width:520px){
          .qmi-command__header{flex-direction:column;}
          .qmi-command__permissions,.qmi-command__metrics{grid-template-columns:1fr;}
          .qmi-command__scenario{grid-template-columns:1fr;}
        }
      
        /* FE-DI-004.1 — Large-value readability */
        .qmi-command__drivers strong,
        .qmi-command__drivers [class*="score"],
        .qmi-command__drivers [class*="value"]{
          font-size:14px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
        }
        .qmi-command__drivers small{
          font-size:10.5px !important;
          line-height:1.4 !important;
        }
        .qmi-command__evolution table td,
        .qmi-command__evolution table th{
          font-size:12px !important;
          line-height:1.45 !important;
        }
        .qmi-command__evolution table td:nth-child(2),
        .qmi-command__evolution table td:nth-child(3),
        .qmi-command__evolution table td:nth-child(4){
          font-size:15px !important;
          font-weight:900 !important;
        }
        .qmi-command__evolution [class*="metric"] strong{
          font-size:18px !important;
          line-height:1.3 !important;
        }

      
        /* FE-DI-004.3 — REAL Driver Evolution History selectors */
        .qmi-command__driver-evolution{
          margin-top:16px !important;
        }
        .qmi-command__driver-evolution-head{
          min-height:32px !important;
          align-items:center !important;
        }
        .qmi-command__driver-evolution-head span{
          font-size:11px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
          letter-spacing:.045em !important;
        }
        .qmi-command__driver-evolution-row{
          min-height:44px !important;
          padding:10px 6px !important;
          align-items:center !important;
        }
        .qmi-command__driver-evolution-row strong{
          font-size:14px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
        }
        .qmi-command__driver-evolution-row span{
          font-size:16px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
          color:#ff5d78 !important;
        }
        .qmi-command__driver-evolution-row em{
          font-size:15px !important;
          line-height:1.3 !important;
          font-weight:900 !important;
          color:#a9bad0 !important;
          font-style:normal !important;
        }
        .qmi-command__driver-evolution-summary{
          font-size:12px !important;
          line-height:1.4 !important;
          padding-top:10px !important;
        }
        .qmi-command__driver-evolution-summary strong{
          font-size:13px !important;
          font-weight:950 !important;
        }

      
        /* FE-DI-004.4 — Unified driver typography */
        .qmi-command__driver-evolution-row strong{
          font-size:14px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
        }

        /* Driver names in the upper Decision Drivers block:
           use the same 14 px scale as Driver Evolution History. */
        .qmi-command__drivers strong{
          font-size:14px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
        }

        /* Keep the enlarged values already approved. */
        .qmi-command__driver-evolution-row span{
          font-size:16px !important;
          line-height:1.3 !important;
          font-weight:950 !important;
        }
        .qmi-command__driver-evolution-row em{
          font-size:15px !important;
          line-height:1.3 !important;
          font-weight:900 !important;
          font-style:normal !important;
        }

      
        /* FE-DI-004.6 — Force exact same size on upper/lower driver labels */
        .qmi-command__driver-label,
        .qmi-command__driver-evolution-row > strong:first-child{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
          text-transform:none !important;
        }
        .qmi-command__driver-row > :first-child,
        .qmi-command__drivers-row > :first-child,
        .qmi-command__driver > :first-child{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
        }

      
        /* FE-DI-004.7 — Normalize analytic label typography to approved 14 px scale */

        /* Evolution Timeline: Direction / Readiness / Transition / Risk
           and all Driver Trajectory names. */
        .qmi-command__timeline-card > strong:first-child,
        .qmi-command__timeline-card > span:first-child,
        .qmi-command__trajectory-card > strong:first-child,
        .qmi-command__trajectory-card > span:first-child,
        .qmi-command__timeline [class*="label"],
        .qmi-command__trajectory [class*="label"]{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
        }

        /* Confidence Structure component names. */
        .qmi-command__confidence-row > span:first-child,
        .qmi-command__confidence-row > strong:first-child,
        .qmi-command__confidence-component > span:first-child,
        .qmi-command__confidence-component > strong:first-child{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
        }

        /* Existing driver labels remain exactly on the same scale. */
        .qmi-command__driver-label,
        .qmi-command__driver-evolution-row > strong:first-child{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
        }

      
        /* FE-DI-004.8 — Evolution Timeline exact readability normalization */
        .qmi-command__timeline-card strong,
        .qmi-command__timeline-card b,
        .qmi-command__timeline-card [class*="name"],
        .qmi-command__timeline-card [class*="label"],
        .qmi-command__timeline-row strong,
        .qmi-command__timeline-row b,
        .qmi-command__timeline-row [class*="name"],
        .qmi-command__timeline-row [class*="label"],
        .qmi-command__trajectory-row strong,
        .qmi-command__trajectory-row b,
        .qmi-command__trajectory-row [class*="name"],
        .qmi-command__trajectory-row [class*="label"],
        .qmi-command__spark-card strong:first-child,
        .qmi-command__spark-card b:first-child{
          font-size:14px !important;
          line-height:18px !important;
          font-weight:950 !important;
          letter-spacing:0 !important;
        }

        /* Normalize small supporting values in those same timeline cards. */
        .qmi-command__timeline-card small,
        .qmi-command__timeline-row small,
        .qmi-command__trajectory-row small,
        .qmi-command__spark-card small{
          font-size:12px !important;
          line-height:16px !important;
          font-weight:800 !important;
        }

      
        /* DE-DI-008 — Decision Outcome */
        .qmi-command__outcome{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__outcome-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__outcome-kicker{font-size:11px;font-weight:950;letter-spacing:.065em;text-transform:uppercase;color:#5b8cff}
        .qmi-command__outcome-title{margin-top:4px;font-size:20px;font-weight:950;color:#e8eef7}
        .qmi-command__outcome-score{text-align:right}.qmi-command__outcome-score strong{display:block;font-size:30px;line-height:1;color:#e8eef7}.qmi-command__outcome-score span{font-size:11px;font-weight:900;color:#8292a7}
        .qmi-command__outcome-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__outcome-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__outcome-card>span{font-size:14px;line-height:18px;font-weight:950;color:#a9bad0}
        .qmi-command__outcome-card>strong{display:block;margin-top:6px;font-size:20px;color:#e8eef7}
        .qmi-command__outcome-card>small{display:block;margin-top:5px;font-size:12px;line-height:16px;font-weight:800;color:#8292a7}
        .qmi-command__outcome-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
        .qmi-command__outcome-meta span{padding:7px 9px;border-radius:7px;background:rgba(148,163,184,.05);font-size:12px;font-weight:850;color:#9cabbc}
        @media(max-width:1000px){.qmi-command__outcome-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:650px){.qmi-command__outcome-grid{grid-template-columns:1fr}}

      
        /* DE-DI-009 — Adaptive Decision Calibration */
        .qmi-command__calibration{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__calibration-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__calibration-kicker{font-size:11px;font-weight:950;letter-spacing:.065em;text-transform:uppercase;color:#5b8cff}
        .qmi-command__calibration-title{margin-top:4px;font-size:20px;font-weight:950;color:#e8eef7}
        .qmi-command__calibration-state{font-size:14px;line-height:18px;font-weight:950;color:#a9bad0}
        .qmi-command__calibration-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
        .qmi-command__calibration-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__calibration-card>span{font-size:14px;line-height:18px;font-weight:950;color:#8292a7}
        .qmi-command__calibration-card>strong{display:block;margin-top:5px;font-size:18px;color:#e8eef7}
        .qmi-command__calibration-card>small{display:block;margin-top:4px;font-size:12px;line-height:16px;font-weight:800;color:#8292a7}
        .qmi-command__calibration-note{margin-top:12px;font-size:14px;line-height:1.5;font-weight:800;color:#a9bad0}
        .qmi-command__calibration-guard{margin-top:10px;font-size:12px;font-weight:900;color:#5b8cff}
        @media(max-width:760px){.qmi-command__calibration-grid{grid-template-columns:1fr}}

      
        /* DE-DI-010 — Decision Memory */
        .qmi-command__memory{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__memory-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__memory-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__memory-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__memory-match{display:grid;grid-template-columns:110px 1fr 130px;gap:12px;align-items:center;padding:10px 0;border-top:1px solid rgba(148,163,184,.08)}
        .qmi-command__memory-match:first-child{border-top:0}
        .qmi-command__memory-bar{height:8px;border-radius:999px;background:rgba(148,163,184,.10);overflow:hidden}
        .qmi-command__memory-bar>i{display:block;height:100%;border-radius:999px;background:#5b8cff}
        @media(max-width:900px){.qmi-command__memory-grid{grid-template-columns:1fr}.qmi-command__memory-match{grid-template-columns:90px 1fr}}

      
        .qmi-command__outcome-memory{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__outcome-memory-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__outcome-memory-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__outcome-memory-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__outcome-memory-split{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
        @media(max-width:760px){.qmi-command__outcome-memory-grid{grid-template-columns:1fr}}

      
        /* DE-DI-012 — Historical Edge */
        .qmi-command__historical-edge{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__historical-edge-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__historical-edge-score{text-align:right}
        .qmi-command__historical-edge-score strong{font-size:30px;font-weight:900;line-height:1}
        .qmi-command__historical-edge-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__historical-edge-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__historical-edge-quality{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:10px}
        @media(max-width:760px){.qmi-command__historical-edge-grid,.qmi-command__historical-edge-quality{grid-template-columns:1fr}}

      
        /* DE-DI-013 — Decision Evidence Alignment */
        .qmi-command__alignment{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__alignment-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__alignment-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__alignment-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        @media(max-width:900px){.qmi-command__alignment-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:600px){.qmi-command__alignment-grid{grid-template-columns:1fr}}

      
        /* DE-DI-014 — Decision Evidence Score */
        .qmi-command__evidence-score{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__evidence-score-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__evidence-score-main{text-align:right}
        .qmi-command__evidence-score-main strong{font-size:34px;font-weight:900;line-height:1}
        .qmi-command__evidence-score-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__evidence-score-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__evidence-score-components{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px;margin-top:10px}
        @media(max-width:1000px){.qmi-command__evidence-score-components{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:700px){.qmi-command__evidence-score-grid,.qmi-command__evidence-score-components{grid-template-columns:1fr}}

      
        /* FE-DI-005 — Color Trajectory System */
        .qmi-command__timeline-row--visual{grid-template-columns:110px minmax(180px,1fr) 58px!important;min-height:86px!important;padding:12px 14px!important}
        .qmi-command__timeline-row--visual .qmi-command__timeline-label strong{font-size:14px!important;line-height:1.2!important;font-weight:900!important;color:#d9e5f5!important}
        .qmi-command__timeline-row--visual .qmi-command__timeline-label span{margin-top:5px!important;font-size:12px!important;font-weight:900!important}
        .qmi-command__timeline-row--visual.is-negative .qmi-command__timeline-label span{color:#ff5268!important}
        .qmi-command__timeline-row--visual.is-warning .qmi-command__timeline-label span{color:#ffb52e!important}
        .qmi-command__timeline-row--visual.is-positive .qmi-command__timeline-label span{color:#31d890!important}
        .qmi-command__trajectory{position:relative;padding:4px 0 0}
        .qmi-command__trajectory-bar{position:relative;height:9px;border-radius:999px;background:linear-gradient(90deg,#f43f5e 0%,#fb923c 25%,#facc15 50%,#84cc16 72%,#10b981 100%);box-shadow:inset 0 0 0 1px rgba(255,255,255,.06),0 0 16px rgba(59,130,246,.05)}
        .qmi-command__trajectory-marker{position:absolute;top:50%;width:18px;height:18px;border-radius:50%;transform:translate(-50%,-50%);background:#0b1220;border:3px solid #fff;box-shadow:0 0 0 2px #ffb52e,0 0 12px rgba(255,181,46,.42);z-index:3}
        .qmi-command__timeline-row--visual.is-negative .qmi-command__trajectory-marker{box-shadow:0 0 0 2px #ff4058,0 0 13px rgba(255,64,88,.48)}
        .qmi-command__timeline-row--visual.is-positive .qmi-command__trajectory-marker{box-shadow:0 0 0 2px #22d391,0 0 13px rgba(34,211,145,.45)}
        .qmi-command__trajectory-scale{display:grid;grid-template-columns:1fr 1fr 1fr;margin-top:7px;color:#7f91aa;font-size:10px;font-weight:750}
        .qmi-command__trajectory-scale span:nth-child(2){text-align:center}.qmi-command__trajectory-scale span:last-child{text-align:right}
        .qmi-command__timeline-row--visual .qmi-command__trajectory svg{position:absolute;left:0;right:0;top:-7px;width:100%;height:24px!important;opacity:.15;pointer-events:none}
        .qmi-command__timeline-row--visual .qmi-command__trajectory svg polyline{fill:none!important;stroke:#fff!important;stroke-width:1.2!important;vector-effect:non-scaling-stroke}
        .qmi-command__timeline-row--visual .qmi-command__timeline-delta{font-size:11px!important;font-weight:900!important;color:#8ea2bd!important}
        .qmi-command__timeline-drivers-title{font-size:11px!important;font-weight:900!important;color:#7f94b2!important}
        @media(max-width:900px){.qmi-command__timeline-row--visual{grid-template-columns:90px minmax(150px,1fr) 48px!important}}

      
        /* DE-DI-015 — Decision Evidence Gate */
        .qmi-command__evidence-gate{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__evidence-gate-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__evidence-gate-status{text-align:right}
        .qmi-command__evidence-gate-status strong{font-size:24px;font-weight:900;line-height:1}
        .qmi-command__evidence-gate-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__evidence-gate-card,.qmi-command__evidence-gate-check{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__evidence-gate-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}
        .qmi-command__evidence-gate-check{display:flex;gap:10px;align-items:flex-start}
        .qmi-command__gate-dot{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:0 0 auto;background:#7f91aa}
        .qmi-command__evidence-gate-check.is-pass .qmi-command__gate-dot{background:#31d890;box-shadow:0 0 10px rgba(49,216,144,.35)}
        .qmi-command__evidence-gate-check.is-fail .qmi-command__gate-dot{background:#ff5268;box-shadow:0 0 10px rgba(255,82,104,.35)}
        .qmi-command__evidence-gate-check.is-conditional .qmi-command__gate-dot,.qmi-command__evidence-gate-check.is-pending .qmi-command__gate-dot{background:#ffb52e}
        .qmi-command__evidence-gate-status.is-passed strong{color:#31d890}.qmi-command__evidence-gate-status.is-blocked strong{color:#ff5268}.qmi-command__evidence-gate-status.is-conditional strong{color:#ffb52e}
        @media(max-width:1050px){.qmi-command__evidence-gate-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
        @media(max-width:700px){.qmi-command__evidence-gate-grid,.qmi-command__evidence-gate-checks{grid-template-columns:1fr}}

      
        /* DE-DI-016 — Decision Validation State */
        .qmi-command__validation-state{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__validation-state-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__validation-state-status{text-align:right}
        .qmi-command__validation-state-status strong{font-size:22px;font-weight:900;line-height:1}
        .qmi-command__validation-state-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__validation-state-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__validation-history{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:12px}
        .qmi-command__validation-node{padding:7px 10px;border-radius:999px;border:1px solid rgba(148,163,184,.12);background:rgba(15,23,42,.5);font-size:11px;font-weight:800;color:#a8bad0}
        .qmi-command__validation-arrow{color:#52647b;font-size:12px}
        .qmi-command__validation-state-status.is-validated strong,.qmi-command__validation-state-status.is-strongly_validated strong{color:#31d890}
        .qmi-command__validation-state-status.is-conditional strong{color:#ffb52e}
        .qmi-command__validation-state-status.is-unvalidated strong{color:#ff5268}
        @media(max-width:1050px){.qmi-command__validation-state-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
        @media(max-width:700px){.qmi-command__validation-state-grid{grid-template-columns:1fr}}

      
        /* DE-DI-017 — Validation Momentum */
        .qmi-command__validation-momentum{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__validation-momentum-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__validation-momentum-status{text-align:right}
        .qmi-command__validation-momentum-status strong{font-size:22px;font-weight:900}
        .qmi-command__validation-momentum-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__validation-momentum-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__validation-momentum-bar{height:8px;border-radius:999px;margin-top:14px;background:linear-gradient(90deg,#f43f5e 0%,#fb923c 25%,#facc15 50%,#84cc16 72%,#10b981 100%);position:relative}
        .qmi-command__validation-momentum-marker{position:absolute;top:50%;width:16px;height:16px;border-radius:50%;transform:translate(-50%,-50%);background:#0b1220;border:3px solid #fff;box-shadow:0 0 0 2px #5b8cff}
        .qmi-command__validation-momentum-status.is-accelerating strong,.qmi-command__validation-momentum-status.is-strengthening strong{color:#31d890}
        .qmi-command__validation-momentum-status.is-weakening strong{color:#ffb52e}
        .qmi-command__validation-momentum-status.is-deteriorating strong{color:#ff5268}
        .qmi-command__validation-momentum-status.is-stable strong{color:#8fb5ff}
        @media(max-width:900px){.qmi-command__validation-momentum-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

      
        /* DE-DI-018 — Contradiction Guard */
        .qmi-command__contradiction-guard{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.14);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__contradiction-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__contradiction-status{text-align:right}
        .qmi-command__contradiction-status strong{font-size:22px;font-weight:900}
        .qmi-command__contradiction-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__contradiction-card,.qmi-command__contradiction-item{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__contradiction-list{display:grid;gap:8px;margin-top:10px}
        .qmi-command__contradiction-item{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:start}
        .qmi-command__severity{font-size:10px;font-weight:900;padding:4px 7px;border-radius:999px}
        .qmi-command__severity.is-high{color:#ff5268;background:rgba(255,82,104,.10)}
        .qmi-command__severity.is-medium{color:#ffb52e;background:rgba(255,181,46,.10)}
        .qmi-command__severity.is-low{color:#8fb5ff;background:rgba(143,181,255,.10)}
        .qmi-command__contradiction-status.is-clear strong{color:#31d890}
        .qmi-command__contradiction-status.is-watch strong{color:#ffb52e}
        .qmi-command__contradiction-status.is-conflict_review strong,.qmi-command__contradiction-status.is-hard_conflict strong{color:#ff5268}
        @media(max-width:900px){.qmi-command__contradiction-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

      
        /* DE-DI-019 — Shadow Adaptive Decision */
        .qmi-command__shadow-adaptive{margin-top:10px;padding:20px;border:1px solid rgba(96,165,250,.18);border-radius:12px;background:linear-gradient(135deg,rgba(37,99,235,.045),rgba(2,6,23,.12))}
        .qmi-command__shadow-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__shadow-status{text-align:right}.qmi-command__shadow-status strong{font-size:22px;font-weight:900;color:#8fb5ff}
        .qmi-command__shadow-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__shadow-card{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__shadow-comparison{display:flex;align-items:center;justify-content:center;gap:14px;margin-top:14px;padding:16px;border-radius:10px;background:rgba(2,6,23,.18)}
        .qmi-command__shadow-posture{font-size:20px;font-weight:950}.qmi-command__shadow-arrow{color:#62748d;font-size:20px}
        .qmi-command__shadow-note{margin-top:12px;padding:11px 13px;border-left:3px solid #5b8cff;background:rgba(91,140,255,.05);border-radius:0 8px 8px 0}
        @media(max-width:1050px){.qmi-command__shadow-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
        @media(max-width:700px){.qmi-command__shadow-grid{grid-template-columns:1fr}}

      
        /* DE-DI-020 — Decision Intelligence Quality Control */
        .qmi-command__quality-control{margin-top:10px;padding:20px;border:1px solid rgba(91,140,255,.16);border-radius:12px;background:rgba(91,140,255,.025)}
        .qmi-command__quality-head{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
        .qmi-command__quality-status{text-align:right}.qmi-command__quality-status strong{font-size:22px;font-weight:900}
        .qmi-command__quality-status.is-ready strong{color:#31d890}.qmi-command__quality-status.is-degraded strong{color:#ffb52e}.qmi-command__quality-status.is-failed strong{color:#ff5268}
        .qmi-command__quality-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:16px}
        .qmi-command__quality-card,.qmi-command__quality-check{padding:14px;border:1px solid rgba(148,163,184,.09);border-radius:9px;background:rgba(2,6,23,.16)}
        .qmi-command__quality-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px}
        .qmi-command__quality-check{display:flex;gap:10px;align-items:flex-start}
        .qmi-command__quality-dot{width:9px;height:9px;border-radius:50%;margin-top:5px;flex:0 0 auto}
        .qmi-command__quality-check.is-pass .qmi-command__quality-dot{background:#31d890;box-shadow:0 0 10px rgba(49,216,144,.3)}
        .qmi-command__quality-check.is-fail .qmi-command__quality-dot{background:#ff5268;box-shadow:0 0 10px rgba(255,82,104,.3)}
        @media(max-width:900px){.qmi-command__quality-grid,.qmi-command__quality-checks{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:650px){.qmi-command__quality-grid,.qmi-command__quality-checks{grid-template-columns:1fr}}

      
        /* FE-DI-006 — Final Workspace */
        .qmi-command__workspace-map{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin:0 0 14px}
        .qmi-command__workspace-tier{padding:14px 16px;border:1px solid rgba(148,163,184,.10);border-radius:10px;background:rgba(15,23,42,.36)}
        .qmi-command__workspace-tier strong{display:block;margin-top:3px}.qmi-command__workspace-tier span{display:block;margin-top:5px;color:#8294ad;font-size:11px;font-weight:650;line-height:1.4}
        .qmi-command__workspace-tier.is-primary{border-color:rgba(49,216,144,.18);background:linear-gradient(135deg,rgba(49,216,144,.035),rgba(15,23,42,.32))}
        .qmi-command__workspace-tier.is-intelligence{border-color:rgba(91,140,255,.18);background:linear-gradient(135deg,rgba(91,140,255,.04),rgba(15,23,42,.32))}
        .qmi-command__workspace-tier.is-advanced{border-color:rgba(168,85,247,.16);background:linear-gradient(135deg,rgba(168,85,247,.03),rgba(15,23,42,.32))}
        .qmi-command__release-strip{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:11px 14px;margin:0 0 14px;border:1px solid rgba(49,216,144,.14);border-radius:10px;background:rgba(49,216,144,.025)}
        .qmi-command__release-strip-left{display:flex;align-items:center;gap:10px}.qmi-command__release-dot{width:8px;height:8px;border-radius:50%;background:#31d890;box-shadow:0 0 10px rgba(49,216,144,.35)}
        .qmi-command__release-strip-right{font-size:11px;font-weight:850;color:#31d890;white-space:nowrap}
        @media(max-width:900px){.qmi-command__workspace-map{grid-template-columns:1fr}.qmi-command__release-strip{align-items:flex-start;flex-direction:column}}

      `}</style>

      <div className="qmi-command__release-strip">
        <div className="qmi-command__release-strip-left">
          <span className="qmi-command__release-dot" />
          <div>
            <div className="qmi-type-label">Decision Intelligence v1.0 · Functional Core Complete</div>
            <div className="qmi-type-secondary">Live decision authoritative · Historical adaptation shadow-only</div>
          </div>
        </div>
        <div className="qmi-command__release-strip-right">FINAL WORKSPACE</div>
      </div>

      <div className="qmi-command__workspace-map">
        <div className="qmi-command__workspace-tier is-primary">
          <div className="qmi-type-eyebrow">01 · Executive Decision</div>
          <strong className="qmi-type-card">What QMI says now</strong>
          <span>Posture · conviction · risk · permissions · execution</span>
        </div>
        <div className="qmi-command__workspace-tier is-intelligence">
          <div className="qmi-type-eyebrow">02 · Decision Intelligence</div>
          <strong className="qmi-type-card">Why and how it is changing</strong>
          <span>Drivers · evolution · attribution · confidence · validation</span>
        </div>
        <div className="qmi-command__workspace-tier is-advanced">
          <div className="qmi-type-eyebrow">03 · Historical / Advanced</div>
          <strong className="qmi-type-card">Memory and governance</strong>
          <span>Reliability · outcomes · edge · calibration · shadow · quality control</span>
        </div>
      </div>

      <div className="qmi-command__header">
        <div>
          <div className="qmi-command__kicker">FE-DI-001 · Decision Intelligence Panel · {symbol}</div>
          <h2>QMI Decision Command</h2>
        </div>
        <div className="qmi-command__live"><Zap size={10} /> Deterministic live synthesis</div>
      </div>

      <div className="qmi-command__grid">
        <div className="qmi-command__card qmi-command__directive">
          <div>
            <div className="qmi-command__card-title"><Target size={12} /> What QMI says now</div>
            <div className="qmi-command__posture">{pretty(posture)}</div>
            <div className="qmi-command__directive-text">
              {pretty(risk)} risk · {pretty(timing)} timing · {pretty(scenario)}
            </div>
            <div className="qmi-command__transition">
              <CircleDot size={10} />
              {pretty(currentState)} <ArrowRight size={11} /> {pretty(targetState)}
            </div>
          </div>

          <div className="qmi-command__state-box">
            <div className="qmi-command__state-head">
              <span>Decision State Transition</span>
              <strong>{formatPercent(transitionProbability)}</strong>
            </div>
            <div className="qmi-command__state-flow">
              <div>
                <span>Current</span>
                <strong>{pretty(currentState)}</strong>
              </div>
              <ArrowRight size={15} />
              <div>
                <span>Next Candidate</span>
                <strong>{pretty(targetState)}</strong>
              </div>
            </div>
            <div className="qmi-command__state-meta">
              <span>Readiness <strong>{formatPercent(transitionReadiness)}</strong></span>
              <span>Maturity <strong>{pretty(maturityPhase)}</strong></span>
            </div>
          </div>

          <div className="qmi-command__metrics">
            <div className="qmi-command__metric"><span>Conviction</span><strong>{formatPercent(conviction)}</strong></div>
            <div className="qmi-command__metric"><span>Execution Conf.</span><strong>{formatPercent(executionConfidence)}</strong></div>
            <div className="qmi-command__metric"><span>Direction</span><strong>{formatScore(direction)}</strong></div>
            <div className="qmi-command__metric"><span>Risk</span><strong>{pretty(risk)}</strong></div>
          </div>
        </div>

        <div className="qmi-command__card qmi-command__why">
          <div className="qmi-command__card-title"><TrendingDown size={12} /> Why this decision</div>
          <div className="qmi-command__rationale">{rationale}</div>

          <div className="qmi-command__scenario">
            <div className="qmi-command__scenario-box">
              <span>Primary scenario</span>
              <strong>{pretty(scenario)}</strong>
            </div>
            <div className="qmi-command__scenario-box">
              <span>Direction score</span>
              <strong>{formatScore(direction)}</strong>
            </div>
          </div>

          {decisionDrivers.length > 0 && (
            <>
              <div className="qmi-command__card-title" style={{marginTop: 12}}>
                <Activity size={12} /> Decision drivers
              </div>
              {dominantDriver && (
                <div className={`qmi-command__dominant ${driverTone(dominantDriver?.score)}`}>
                  <div>
                    <span>Dominant Driver</span>
                    <strong>{pretty(dominantDriver?.engine)}</strong>
                  </div>
                  <div>
                    <span>Contribution</span>
                    <strong>{formatScore(dominantDriver?.normalized_contribution)}</strong>
                  </div>
                  <div>
                    <span>Effective Weight</span>
                    <strong>{formatPercent(dominantDriver?.effective_weight_pct)}</strong>
                  </div>
                </div>
              )}

              <div className="qmi-command__drivers-axis">
                <span>-100</span><span>-50</span><span>0</span><span>+50</span><span>+100</span>
              </div>

              <div className="qmi-command__drivers">
                {decisionDrivers.map((driver) => {
                  const score = Number(driver?.score || 0);
                  const tone = driverTone(score);
                  const width = driverWidth(score);
                  const positive = score >= 0;
                  const style = positive
                    ? { left: "50%", width }
                    : { right: "50%", width };

                  return (
                    <div className={`qmi-command__driver ${tone}`} key={driver?.engine}>
                      <div className="qmi-command__driver-label">{pretty(driver?.engine)}</div>
                      <div className="qmi-command__driver-track">
                        <div className="qmi-command__driver-fill" style={style} />
                      </div>
                      <div className="qmi-command__driver-score">{formatScore(score)}</div>
                      <div className="qmi-command__driver-meta">
                        {pretty(driver?.state)} · confidence {formatPercent(driver?.confidence)}
                        {driver?.effective_weight_pct !== undefined
                          ? ` · weight ${formatPercent(driver.effective_weight_pct)}`
                          : ""}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}

          <div className="qmi-command__blockers">
            {blockers.length ? blockers.slice(0, 4).map((item, index) => (
              <div className="qmi-command__blocker" key={`decision-blocker-${index}`}>
                <ShieldAlert size={11} />
                <span><strong>{pretty(item?.severity)}</strong> · {blockerText(item)}</span>
              </div>
            )) : (
              <div className="qmi-command__blocker" style={{color:"#8da0b8", borderColor:"rgba(148,163,184,.08)", background:"rgba(148,163,184,.025)"}}>
                <CheckCircle2 size={11} /> No active blockers reported
              </div>
            )}
          </div>
        </div>
      </div>

      <div className={`qmi-command__evolution ${evolutionTone(evolutionTrajectory?.state)}`}>
        <div className="qmi-command__evolution-head">
          <div>
            <span>DE-DI-003 · Decision Evolution</span>
            <strong>{pretty(evolutionTrajectory?.state || "Insufficient History")}</strong>
          </div>
          <div className="qmi-command__evolution-score">{formatScore(evolutionTrajectory?.score)}</div>
        </div>

        {evolution?.available ? (
          <>
            <div className="qmi-command__evolution-flow">
              <div>
                <span>Persisted Baseline</span>
                <strong>{pretty(evolutionPrevious?.state)}</strong>
                <small>{pretty(evolutionBaseline?.freshness)} · snapshot #{evolutionPrevious?.snapshot_id ?? "--"}</small>
              </div>
              <ArrowRight size={15} />
              <div>
                <span>Live State</span>
                <strong>{pretty(evolutionCurrent?.state)}</strong>
                <small>{pretty(evolutionCurrent?.posture)} posture</small>
              </div>
            </div>

            <div className="qmi-command__evolution-metrics">
              {[
                ["Direction", evolutionPrevious?.direction_score, evolutionCurrent?.direction_score, evolutionDeltas?.direction_score, evolutionSignals?.direction?.state],
                ["Readiness", evolutionPrevious?.transition_readiness, evolutionCurrent?.transition_readiness, evolutionDeltas?.transition_readiness, evolutionSignals?.transition_readiness?.state],
                ["Transition Prob.", evolutionPrevious?.transition_probability, evolutionCurrent?.transition_probability, evolutionDeltas?.transition_probability, evolutionSignals?.transition_probability?.state],
                ["Risk Score", evolutionPrevious?.risk_score, evolutionCurrent?.risk_score, evolutionDeltas?.risk_score, evolutionSignals?.risk?.state],
              ].map(([label, previousValue, currentValue, delta, state]) => (
                <div className={`qmi-command__evolution-metric ${evolutionTone(state)}`} key={label}>
                  <span>{label}</span>
                  <div><small>{previousValue ?? "--"}</small><ArrowRight size={10} /><strong>{currentValue ?? "--"}</strong></div>
                  <em>{signedDelta(delta)} · {pretty(state)}</em>
                </div>
              ))}
            </div>

            {evolution?.driver_evolution?.available && (
              <div className="qmi-command__driver-evolution">
                <div className="qmi-command__card-title">Driver Evolution History</div>
                <div className="qmi-command__driver-evolution-head"><span>Driver</span><span>Previous</span><span>Current</span><span>Delta</span></div>
                {evolution.driver_evolution.drivers.map((driver) => (
                  <div className={`qmi-command__driver-evolution-row ${evolutionTone(driver?.state)}`} key={driver.engine}>
                    <strong>{pretty(driver.engine)}</strong><span>{formatScore(driver.previous_score)}</span>
                    <span>{formatScore(driver.current_score)}</span><em>{signedDelta(driver.delta)} · {pretty(driver.state)}</em>
                  </div>
                ))}
                <div className="qmi-command__driver-evolution-summary">
                  <span>Driver trajectory <strong>{pretty(evolution.driver_evolution.trajectory)}</strong></span>
                  <span>Average Δ <strong>{signedDelta(evolution.driver_evolution.average_score_delta)}</strong></span>
                </div>
              </div>
            )}
            <div className="qmi-command__evolution-note">{evolution?.interpretation}</div>
          </>
        ) : (
          <div className="qmi-command__evolution-note">
            No persisted technical-state baseline is available yet. Decision Evolution activates automatically when history exists.
          </div>
        )}
      </div>

      <div className="qmi-command__memory">
        <div className="qmi-command__memory-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-010 · Decision Memory</div>
            <div className="qmi-type-section">Historical analogues</div>
          </div>
          <div className="qmi-type-label">{pretty(memory?.readiness || "Insufficient History")}</div>
        </div>

        {memory?.available ? (
          <>
            <div className="qmi-command__memory-grid">
              <div className="qmi-command__memory-card">
                <div className="qmi-type-secondary">Similar configurations</div>
                <div className="qmi-type-value">{memory?.matches_found || 0}</div>
              </div>
              <div className="qmi-command__memory-card">
                <div className="qmi-type-secondary">Average similarity</div>
                <div className="qmi-type-value">{memory?.average_similarity == null ? "N/A" : formatPercent(memory.average_similarity)}</div>
              </div>
              <div className="qmi-command__memory-card">
                <div className="qmi-type-secondary">Dominant historical posture</div>
                <div className="qmi-type-value">{pretty(memory?.dominant_historical_posture || "Unknown")}</div>
              </div>
            </div>

            <div style={{ marginTop: 14 }}>
              {memoryMatches.map((item) => (
                <div className="qmi-command__memory-match" key={item?.snapshot_id}>
                  <div>
                    <div className="qmi-type-value">{formatPercent(item?.similarity_score || 0)}</div>
                    <div className="qmi-type-secondary">Similarity</div>
                  </div>
                  <div className="qmi-command__memory-bar">
                    <i style={{ width: `${Math.max(0, Math.min(100, item?.similarity_score || 0))}%` }} />
                  </div>
                  <div>
                    <div className="qmi-type-label">{pretty(item?.decision_posture || item?.state || "Unknown")}</div>
                    <div className="qmi-type-secondary">{item?.common_dimensions || 0} dimensions</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{memory?.summary}</div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Decision Memory activates automatically when sufficiently similar persisted technical configurations are available.
          </div>
        )}
      </div>

      <div className="qmi-command__outcome-memory">
        <div className="qmi-command__outcome-memory-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-011 · Historical Outcome Memory</div>
            <div className="qmi-type-section">What happened after similar setups</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="qmi-type-value">{pretty(outcomeMemory?.historical_bias || "Unavailable")}</div>
            <div className="qmi-type-label">{pretty(outcomeMemory?.readiness || "Insufficient History")}</div>
          </div>
        </div>
        {outcomeMemory?.available ? (
          <>
            <div className="qmi-command__outcome-memory-grid">
              {outcomeMemoryHorizons.map((item) => (
                <div className="qmi-command__outcome-memory-card" key={item?.horizon}>
                  <div className="qmi-type-label">After {item?.horizon}</div>
                  <div className="qmi-type-value" style={{ marginTop: 6 }}>
                    {item?.average_return_pct == null ? "N/A" : `${item.average_return_pct >= 0 ? "+" : ""}${Number(item.average_return_pct).toFixed(2)}%`}
                  </div>
                  <div className="qmi-type-secondary" style={{ marginTop: 8 }}>
                    Bullish {item?.bullish_pct == null ? "N/A" : formatPercent(item.bullish_pct)} · Bearish {item?.bearish_pct == null ? "N/A" : formatPercent(item.bearish_pct)} · n={item?.sample_size || 0}
                  </div>
                </div>
              ))}
            </div>
            <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{outcomeMemory?.summary}</div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Historical Outcome Memory activates automatically when similar persisted configurations complete a 1D, 5D or 20D evaluation horizon.
          </div>
        )}
      </div>

      <div className="qmi-command__historical-edge">
        <div className="qmi-command__historical-edge-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-012 · Historical Edge</div>
            <div className="qmi-type-section">Historical decision edge</div>
          </div>
          <div className="qmi-command__historical-edge-score">
            <strong>{edge?.edge_score == null ? "N/A" : `${edge.edge_score >= 0 ? "+" : ""}${Number(edge.edge_score).toFixed(1)}`}</strong>
            <div className="qmi-type-label">{pretty(edge?.bias || "Unavailable")}</div>
          </div>
        </div>

        {edge?.available ? (
          <>
            <div className="qmi-command__historical-edge-grid">
              {edgeHorizons.map((item) => (
                <div className="qmi-command__historical-edge-card" key={item?.horizon}>
                  <div className="qmi-type-label">{item?.horizon} Edge</div>
                  <div className="qmi-type-value" style={{ marginTop: 6 }}>
                    {item?.edge_score == null ? "N/A" : `${item.edge_score >= 0 ? "+" : ""}${Number(item.edge_score).toFixed(1)}`}
                  </div>
                  <div className="qmi-type-secondary" style={{ marginTop: 7 }}>
                    {pretty(item?.bias || "Neutral")} · Avg. {item?.average_return_pct == null ? "N/A" : `${Number(item.average_return_pct).toFixed(2)}%`} · n={item?.sample_size || 0}
                  </div>
                </div>
              ))}
            </div>

            <div className="qmi-command__historical-edge-quality">
              <div className="qmi-command__historical-edge-card">
                <div className="qmi-type-secondary">Similarity</div>
                <div className="qmi-type-value">{edge?.average_similarity == null ? "N/A" : formatPercent(edge.average_similarity)}</div>
              </div>
              <div className="qmi-command__historical-edge-card">
                <div className="qmi-type-secondary">Evidence</div>
                <div className="qmi-type-value">{pretty(edge?.evidence || "Insufficient History")}</div>
              </div>
              <div className="qmi-command__historical-edge-card">
                <div className="qmi-type-secondary">Directional consistency</div>
                <div className="qmi-type-value">{pretty(edge?.directional_consistency || "Unavailable")}</div>
              </div>
            </div>

            <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{edge?.summary}</div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Historical Edge activates automatically when comparable historical configurations complete evaluation horizons.
          </div>
        )}
      </div>

      <div className="qmi-command__alignment">
        <div className="qmi-command__alignment-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-013 · Decision Evidence Alignment</div>
            <div className="qmi-type-section">Live decision vs historical evidence</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div className="qmi-type-value">{pretty(alignment?.alignment || "Unavailable")}</div>
            <div className="qmi-type-label">
              {alignment?.alignment_confidence == null ? "Insufficient History" : `${Number(alignment.alignment_confidence).toFixed(1)}% confidence`}
            </div>
          </div>
        </div>

        {alignment?.available ? (
          <>
            <div className="qmi-command__alignment-grid">
              <div className="qmi-command__alignment-card">
                <div className="qmi-type-secondary">Live posture</div>
                <div className="qmi-type-value">{pretty(alignment?.live_posture || "Unknown")}</div>
              </div>
              <div className="qmi-command__alignment-card">
                <div className="qmi-type-secondary">Live direction</div>
                <div className="qmi-type-value">{pretty(alignment?.live_direction || "Unknown")}</div>
              </div>
              <div className="qmi-command__alignment-card">
                <div className="qmi-type-secondary">Historical direction</div>
                <div className="qmi-type-value">{pretty(alignment?.historical_direction || "Unavailable")}</div>
              </div>
              <div className="qmi-command__alignment-card">
                <div className="qmi-type-secondary">Historical edge</div>
                <div className="qmi-type-value">{alignment?.historical_edge_score == null ? "N/A" : `${alignment.historical_edge_score >= 0 ? "+" : ""}${Number(alignment.historical_edge_score).toFixed(1)}`}</div>
              </div>
            </div>
            <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{alignment?.message}</div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Evidence Alignment activates automatically when Historical Edge has sufficient completed evidence.
          </div>
        )}
      </div>

      <div className="qmi-command__evidence-score">
        <div className="qmi-command__evidence-score-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-014 · Decision Evidence Score</div>
            <div className="qmi-type-section">Total evidence supporting the decision</div>
          </div>
          <div className="qmi-command__evidence-score-main">
            <strong>{evidenceScore?.score == null ? "N/A" : `${Number(evidenceScore.score).toFixed(1)}`}</strong>
            <div className="qmi-type-label">{pretty(evidenceScore?.quality || "Insufficient Evidence")}</div>
          </div>
        </div>

        {evidenceScore?.available ? (
          <>
            <div className="qmi-command__evidence-score-grid">
              <div className="qmi-command__evidence-score-card">
                <div className="qmi-type-secondary">Live evidence</div>
                <div className="qmi-type-value">{evidenceScore?.live_evidence?.score == null ? "N/A" : Number(evidenceScore.live_evidence.score).toFixed(1)}</div>
                <div className="qmi-type-secondary">Weight {evidenceScore?.live_evidence?.weight_pct ?? 0}%</div>
              </div>
              <div className="qmi-command__evidence-score-card">
                <div className="qmi-type-secondary">Historical evidence</div>
                <div className="qmi-type-value">{evidenceScore?.historical_evidence?.support_score == null ? "N/A" : Number(evidenceScore.historical_evidence.support_score).toFixed(1)}</div>
                <div className="qmi-type-secondary">Weight {evidenceScore?.historical_evidence?.weight_pct ?? 0}%</div>
              </div>
              <div className="qmi-command__evidence-score-card">
                <div className="qmi-type-secondary">Alignment</div>
                <div className="qmi-type-value">{pretty(evidenceScore?.alignment?.state || "Unavailable")}</div>
                <div className="qmi-type-secondary">{evidenceScore?.alignment?.confidence == null ? "N/A" : `${Number(evidenceScore.alignment.confidence).toFixed(1)}% confidence`}</div>
              </div>
            </div>

            <div className="qmi-command__evidence-score-components">
              {Object.entries(liveEvidenceComponents).map(([key, value]) => (
                <div className="qmi-command__evidence-score-card" key={key}>
                  <div className="qmi-type-secondary">{pretty(key)}</div>
                  <div className="qmi-type-value">{value == null ? "N/A" : Number(value).toFixed(1)}</div>
                </div>
              ))}
            </div>
            <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{evidenceScore?.support}</div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Decision Evidence Score activates when live confidence or historical evidence is available.
          </div>
        )}
      </div>

      <div className="qmi-command__evidence-gate">
        <div className="qmi-command__evidence-gate-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-015 · Decision Evidence Gate</div>
            <div className="qmi-type-section">Formal decision validation</div>
          </div>
          <div className={`qmi-command__evidence-gate-status is-${String(evidenceGate?.gate || "").toLowerCase()}`}>
            <strong>{pretty(evidenceGate?.gate || "Blocked")}</strong>
            <div className="qmi-type-label">{pretty(evidenceGate?.validation_strength || "Insufficient")}</div>
          </div>
        </div>

        <div className="qmi-command__evidence-gate-grid">
          <div className="qmi-command__evidence-gate-card">
            <div className="qmi-type-secondary">Current decision</div>
            <div className="qmi-type-value">{pretty(evidenceGate?.decision_posture || posture || "Unknown")}</div>
          </div>
          <div className="qmi-command__evidence-gate-card">
            <div className="qmi-type-secondary">Evidence score</div>
            <div className="qmi-type-value">{evidenceGate?.evidence_score == null ? "N/A" : Number(evidenceGate.evidence_score).toFixed(1)}</div>
          </div>
          <div className="qmi-command__evidence-gate-card">
            <div className="qmi-type-secondary">Live evidence</div>
            <div className="qmi-type-value">{evidenceGate?.live_evidence_score == null ? "N/A" : Number(evidenceGate.live_evidence_score).toFixed(1)}</div>
          </div>
          <div className="qmi-command__evidence-gate-card">
            <div className="qmi-type-secondary">Historical alignment</div>
            <div className="qmi-type-value">{pretty(evidenceGate?.historical_alignment || "Unavailable")}</div>
          </div>
          <div className="qmi-command__evidence-gate-card">
            <div className="qmi-type-secondary">Historical maturity</div>
            <div className="qmi-type-value">{pretty(evidenceGate?.historical_maturity || "Insufficient History")}</div>
          </div>
        </div>

        <div className="qmi-command__evidence-gate-checks">
          {evidenceGateChecks.map((check) => (
            <div className={`qmi-command__evidence-gate-check is-${String(check?.state || "pending").toLowerCase()}`} key={check?.key}>
              <span className="qmi-command__gate-dot" />
              <div>
                <div className="qmi-type-label">{check?.label}</div>
                <div className="qmi-type-secondary">{check?.detail}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{evidenceGate?.assessment}</div>
      </div>

      <div className="qmi-command__validation-state">
        <div className="qmi-command__validation-state-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-016 · Decision Validation State</div>
            <div className="qmi-type-section">Persisted validation trajectory</div>
          </div>
          <div className={`qmi-command__validation-state-status is-${String(validationState?.validation_state || "unvalidated").toLowerCase()}`}>
            <strong>{pretty(validationState?.validation_state || "Unvalidated")}</strong>
            <div className="qmi-type-label">{pretty(validationState?.trajectory || "Baseline")}</div>
          </div>
        </div>

        <div className="qmi-command__validation-state-grid">
          <div className="qmi-command__validation-state-card">
            <div className="qmi-type-secondary">Current decision</div>
            <div className="qmi-type-value">{pretty(validationState?.decision_posture || posture || "Unknown")}</div>
          </div>
          <div className="qmi-command__validation-state-card">
            <div className="qmi-type-secondary">Evidence gate</div>
            <div className="qmi-type-value">{pretty(validationState?.evidence_gate || "Blocked")}</div>
          </div>
          <div className="qmi-command__validation-state-card">
            <div className="qmi-type-secondary">Evidence score</div>
            <div className="qmi-type-value">{validationState?.evidence_score == null ? "N/A" : Number(validationState.evidence_score).toFixed(1)}</div>
          </div>
          <div className="qmi-command__validation-state-card">
            <div className="qmi-type-secondary">Evidence Δ</div>
            <div className="qmi-type-value">{validationState?.evidence_delta == null ? "Baseline" : signedDelta(validationState.evidence_delta)}</div>
          </div>
          <div className="qmi-command__validation-state-card">
            <div className="qmi-type-secondary">Persistence</div>
            <div className="qmi-type-value">{validationState?.persistence_snapshots || 0} snapshots</div>
          </div>
        </div>

        {validationHistory.length > 0 && (
          <div className="qmi-command__validation-history">
            {validationHistory.map((state, index) => (
              <span key={`${state}-${index}`} style={{ display: "contents" }}>
                {index > 0 && <span className="qmi-command__validation-arrow">→</span>}
                <span className="qmi-command__validation-node">{pretty(state)}</span>
              </span>
            ))}
          </div>
        )}

        <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{validationState?.assessment}</div>
      </div>

      <div className="qmi-command__validation-momentum">
        <div className="qmi-command__validation-momentum-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-017 · Validation Momentum</div>
            <div className="qmi-type-section">Evidence acceleration and decay</div>
          </div>
          <div className={`qmi-command__validation-momentum-status is-${String(validationMomentum?.state || "insufficient_history").toLowerCase()}`}>
            <strong>{pretty(validationMomentum?.state || "Insufficient History")}</strong>
            <div className="qmi-type-label">{validationMomentum?.momentum_score == null ? "N/A" : Number(validationMomentum.momentum_score).toFixed(1)}</div>
          </div>
        </div>

        {validationMomentum?.available ? (
          <>
            <div className="qmi-command__validation-momentum-grid">
              <div className="qmi-command__validation-momentum-card"><div className="qmi-type-secondary">Momentum score</div><div className="qmi-type-value">{Number(validationMomentum.momentum_score).toFixed(1)}</div></div>
              <div className="qmi-command__validation-momentum-card"><div className="qmi-type-secondary">Recent slope</div><div className="qmi-type-value">{signedDelta(validationMomentum.recent_slope)}</div></div>
              <div className="qmi-command__validation-momentum-card"><div className="qmi-type-secondary">Acceleration</div><div className="qmi-type-value">{signedDelta(validationMomentum.acceleration)}</div></div>
              <div className="qmi-command__validation-momentum-card"><div className="qmi-type-secondary">Observations</div><div className="qmi-type-value">{validationMomentum.point_count}</div></div>
            </div>
            <div className="qmi-command__validation-momentum-bar">
              <div className="qmi-command__validation-momentum-marker" style={{ left: `${Math.max(0, Math.min(100, (Number(validationMomentum.momentum_score || 0) + 100) / 2))}%` }} />
            </div>
          </>
        ) : (
          <div className="qmi-type-secondary" style={{ marginTop: 14 }}>
            Validation Momentum activates automatically after {validationMomentum?.minimum_points || 3} persisted validation observations.
          </div>
        )}
        <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{validationMomentum?.assessment}</div>
      </div>

      <div className="qmi-command__contradiction-guard">
        <div className="qmi-command__contradiction-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-018 · Contradiction Guard</div>
            <div className="qmi-type-section">Cross-engine coherence control</div>
          </div>
          <div className={`qmi-command__contradiction-status is-${String(contradictionGuard?.guard_state || "clear").toLowerCase()}`}>
            <strong>{pretty(contradictionGuard?.guard_state || "Clear")}</strong>
            <div className="qmi-type-label">Coherence {contradictionGuard?.coherence_score == null ? "N/A" : Number(contradictionGuard.coherence_score).toFixed(1)}</div>
          </div>
        </div>
        <div className="qmi-command__contradiction-grid">
          <div className="qmi-command__contradiction-card"><div className="qmi-type-secondary">Current decision</div><div className="qmi-type-value">{pretty(contradictionGuard?.decision_posture || posture || "Unknown")}</div></div>
          <div className="qmi-command__contradiction-card"><div className="qmi-type-secondary">Direction</div><div className="qmi-type-value">{pretty(contradictionGuard?.decision_direction || "Neutral")}</div></div>
          <div className="qmi-command__contradiction-card"><div className="qmi-type-secondary">Contradictions</div><div className="qmi-type-value">{contradictionGuard?.contradiction_count ?? 0}</div></div>
          <div className="qmi-command__contradiction-card"><div className="qmi-type-secondary">High severity</div><div className="qmi-type-value">{contradictionGuard?.high_severity_count ?? 0}</div></div>
        </div>
        {contradictionItems.length > 0 && (
          <div className="qmi-command__contradiction-list">
            {contradictionItems.map((item) => (
              <div className="qmi-command__contradiction-item" key={item?.code}>
                <span className={`qmi-command__severity is-${String(item?.severity || "low").toLowerCase()}`}>{item?.severity}</span>
                <div><div className="qmi-type-label">{item?.message}</div><div className="qmi-type-secondary">{pretty(item?.code)}</div></div>
                <div className="qmi-type-secondary">{item?.source}</div>
              </div>
            ))}
          </div>
        )}
        <div className="qmi-type-secondary" style={{ marginTop: 12 }}>{contradictionGuard?.assessment}</div>
      </div>

      <div className="qmi-command__shadow-adaptive">
        <div className="qmi-command__shadow-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-019 · Shadow Adaptive Decision</div>
            <div className="qmi-type-section">Historical overlay · simulation only</div>
          </div>
          <div className="qmi-command__shadow-status">
            <strong>{shadowAdaptive?.adaptive_eligible ? "SHADOW ACTIVE" : "SHADOW LOCKED"}</strong>
            <div className="qmi-type-label">{pretty(shadowAdaptive?.influence || "None")}</div>
          </div>
        </div>
        <div className="qmi-command__shadow-comparison">
          <div><div className="qmi-type-secondary">LIVE</div><div className="qmi-command__shadow-posture">{pretty(shadowAdaptive?.live_posture || posture || "Unknown")}</div></div>
          <div className="qmi-command__shadow-arrow">→</div>
          <div><div className="qmi-type-secondary">SHADOW</div><div className="qmi-command__shadow-posture">{pretty(shadowAdaptive?.shadow_posture || "Unknown")}</div></div>
        </div>
        <div className="qmi-command__shadow-grid">
          <div className="qmi-command__shadow-card"><div className="qmi-type-secondary">Historical direction</div><div className="qmi-type-value">{pretty(shadowAdaptive?.historical_direction || "Unavailable")}</div></div>
          <div className="qmi-command__shadow-card"><div className="qmi-type-secondary">Historical edge</div><div className="qmi-type-value">{shadowAdaptive?.historical_edge_score == null ? "N/A" : Number(shadowAdaptive.historical_edge_score).toFixed(1)}</div></div>
          <div className="qmi-command__shadow-card"><div className="qmi-type-secondary">Evidence score</div><div className="qmi-type-value">{shadowAdaptive?.evidence_score == null ? "N/A" : Number(shadowAdaptive.evidence_score).toFixed(1)}</div></div>
          <div className="qmi-command__shadow-card"><div className="qmi-type-secondary">Evidence gate</div><div className="qmi-type-value">{pretty(shadowAdaptive?.evidence_gate || "Blocked")}</div></div>
          <div className="qmi-command__shadow-card"><div className="qmi-type-secondary">Contradiction guard</div><div className="qmi-type-value">{pretty(shadowAdaptive?.contradiction_guard || "Clear")}</div></div>
        </div>
        <div className="qmi-command__shadow-note">
          <div className="qmi-type-label">{shadowAdaptive?.reason}</div>
          <div className="qmi-type-secondary" style={{marginTop:4}}>{shadowAdaptive?.assessment}</div>
        </div>
      </div>

      <div className="qmi-command__quality-control">
        <div className="qmi-command__quality-head">
          <div>
            <div className="qmi-type-eyebrow">DE-DI-020 · Decision Intelligence Quality Control</div>
            <div className="qmi-type-section">Final integrity and coherence audit</div>
          </div>
          <div className={`qmi-command__quality-status is-${String(qualityControl?.quality_state || "failed").toLowerCase()}`}>
            <strong>{pretty(qualityControl?.quality_state || "Unavailable")}</strong>
            <div className="qmi-type-label">{qualityControl?.quality_score == null ? "N/A" : `${Number(qualityControl.quality_score).toFixed(1)}%`}</div>
          </div>
        </div>

        <div className="qmi-command__quality-grid">
          <div className="qmi-command__quality-card"><div className="qmi-type-secondary">Release target</div><div className="qmi-type-value">{qualityControl?.release_target || "Decision Intelligence v1.0"}</div></div>
          <div className="qmi-command__quality-card"><div className="qmi-type-secondary">Checks passed</div><div className="qmi-type-value">{qualityControl?.checks_passed ?? 0} / {qualityControl?.checks_total ?? 0}</div></div>
          <div className="qmi-command__quality-card"><div className="qmi-type-secondary">Failures</div><div className="qmi-type-value">{qualityControl?.failure_count ?? 0}</div></div>
          <div className="qmi-command__quality-card"><div className="qmi-type-secondary">Critical failures</div><div className="qmi-type-value">{qualityControl?.critical_failure_count ?? 0}</div></div>
        </div>

        <div className="qmi-command__quality-checks">
          {qualityChecks.map((check) => (
            <div className={`qmi-command__quality-check is-${String(check?.state || "fail").toLowerCase()}`} key={check?.code}>
              <span className="qmi-command__quality-dot" />
              <div><div className="qmi-type-label">{check?.label}</div><div className="qmi-type-secondary">{check?.detail}</div></div>
            </div>
          ))}
        </div>
        <div className="qmi-type-secondary" style={{marginTop:12}}>{qualityControl?.assessment}</div>
      </div>

      <div className="qmi-command__calibration">
        <div className="qmi-command__calibration-head">
          <div>
            <div className="qmi-command__calibration-kicker">DE-DI-009 · Adaptive Decision Calibration</div>
            <div className="qmi-command__calibration-title">Calibration evidence</div>
          </div>
          <div className="qmi-command__calibration-state">{pretty(calibration?.readiness || "Insufficient History")}</div>
        </div>

        {calibration?.available ? (
          <>
            <div className="qmi-command__calibration-grid">
              <div className="qmi-command__calibration-card">
                <span>Strongest evidence</span>
                <strong>{pretty(calibration?.strongest_evidence?.name || "None")}</strong>
                <small>{calibration?.strongest_evidence?.score == null ? "No qualified positive edge" : `${formatPercent(calibration.strongest_evidence.score)} · ${calibration.strongest_evidence.sample_size} observations`}</small>
              </div>
              <div className="qmi-command__calibration-card">
                <span>Weakest evidence</span>
                <strong>{pretty(calibration?.weakest_evidence?.name || "None")}</strong>
                <small>{calibration?.weakest_evidence?.score == null ? "No qualified weak edge" : `${formatPercent(calibration.weakest_evidence.score)} · ${calibration.weakest_evidence.sample_size} observations`}</small>
              </div>
            </div>
            <div className="qmi-command__calibration-note">{calibration?.recommendation}</div>
            <div className="qmi-command__calibration-guard">Diagnostic only · No automatic weight, threshold or execution changes</div>
          </>
        ) : (
          <div className="qmi-command__evolution-note">
            Calibration activates when Reliability and Outcome accumulate qualified historical samples.
          </div>
        )}
      </div>

      <div className="qmi-command__outcome">
        <div className="qmi-command__outcome-head">
          <div>
            <div className="qmi-command__outcome-kicker">DE-DI-008 · Decision Outcome</div>
            <div className="qmi-command__outcome-title">Historical decision performance</div>
          </div>
          <div className="qmi-command__outcome-score">
            <strong>{outcome?.quality_score == null ? "N/A" : formatPercent(outcome.quality_score)}</strong>
            <span>{pretty(outcome?.quality || "Insufficient History")}</span>
          </div>
        </div>
        {outcome?.available ? (
          <>
            <div className="qmi-command__outcome-grid">
              {outcomePostures.map((item) => (
                <div className="qmi-command__outcome-card" key={item?.posture}>
                  <span>{pretty(item?.posture)}</span>
                  <strong>{item?.success_rate_pct == null ? "N/A" : formatPercent(item.success_rate_pct)}</strong>
                  <small>{item?.evaluations || 0} decisions · Avg {item?.average_outcome_pct == null ? "N/A" : `${item.average_outcome_pct >= 0 ? "+" : ""}${item.average_outcome_pct.toFixed(2)}%`}</small>
                </div>
              ))}
            </div>
            <div className="qmi-command__outcome-meta">
              <span>1D primary horizon</span>
              <span>Sample · {outcome?.sample_size || 0}</span>
              <span>Successful · {outcome?.successful || 0}</span>
              <span>Unsuccessful · {outcome?.unsuccessful || 0}</span>
            </div>
          </>
        ) : (
          <div className="qmi-command__evolution-note">
            Outcome measurement activates automatically when persisted decision postures have completed a 1D evaluation horizon.
          </div>
        )}
      </div>

      <div className="qmi-command__reliability">
        <div className="qmi-command__reliability-head">
          <div>
            <span>DE-DI-006 · Decision Reliability</span>
            <strong>Historical technical reliability</strong>
          </div>
          <div className="qmi-command__reliability-score">
            <strong>{reliability?.reliability_pct == null ? "N/A" : formatPercent(reliability.reliability_pct)}</strong>
            <span>{pretty(reliability?.quality || "Insufficient History")}</span>
          </div>
        </div>

        {reliability?.available ? (
          <>
            <div className="qmi-command__reliability-grid">
              {reliabilityHorizons.map((item) => (
                <div className="qmi-command__reliability-horizon" key={item?.horizon}>
                  <span>{item?.horizon} horizon</span>
                  <strong>{item?.hit_rate_pct == null ? "N/A" : formatPercent(item.hit_rate_pct)}</strong>
                  <small>{item?.correct || 0} correct · {item?.evaluations || 0} evaluated</small>
                </div>
              ))}
            </div>
            <div className="qmi-command__reliability-meta">
              <span>Sample · {reliability?.sample_size || 0}</span>
              <span>Correct · {reliability?.correct || 0}</span>
              <span>Incorrect · {reliability?.incorrect || 0}</span>
              <span>Persisted observations only</span>
            </div>
          </>
        ) : (
          <div className="qmi-command__evolution-note">
            Reliability will activate automatically when persisted snapshots are old enough to complete a 1D evaluation horizon. No synthetic backfill is used.
          </div>
        )}
      </div>

      <div className="qmi-command__reliability-breakdown">
        <span>DE-DI-007 · Reliability Breakdown</span>
        <h3>Where QMI performs best</h3>
        {reliabilityBreakdown?.available ? (
          <>
            <div className="qmi-command__segment-grid">
              {[...(reliabilityBreakdown?.by_direction || []), ...(reliabilityBreakdown?.by_strength || [])].map((item) => (
                <div className="qmi-command__segment" key={item.segment}>
                  <span>{pretty(item.segment)}</span>
                  <strong>{item.hit_rate_pct == null ? "N/A" : formatPercent(item.hit_rate_pct)}</strong>
                  <small>{item.correct || 0} correct · {item.evaluations || 0} evaluated</small>
                </div>
              ))}
            </div>
            <div className="qmi-command__segment-note">{reliabilityBreakdown?.interpretation}</div>
          </>
        ) : <div className="qmi-command__evolution-note">Segment reliability activates when completed 1D observations are available.</div>}
      </div>

      <div className="qmi-command__confidence-decomp">
        <div className="qmi-command__confidence-decomp-head"><div><span>DE-DI-005 · Decision Confidence Decomposition</span><strong>Confidence structure</strong></div><div className="qmi-command__confidence-score"><strong>{formatPercent(confidenceDecomposition?.overall)}</strong><span>{pretty(confidenceDecomposition?.quality || "Unavailable")}</span></div></div>
        <div className="qmi-command__confidence-bars">
          {[["Technical Agreement",confidenceComponents?.technical_agreement],["Driver Consistency",confidenceComponents?.driver_consistency],["State Stability",confidenceComponents?.state_stability],["Transition Certainty",confidenceComponents?.transition_certainty],["Execution Confidence",confidenceComponents?.execution_confidence]].map(([label,value])=>{const numeric=Math.max(0,Math.min(100,Number(value)||0));return <div className="qmi-command__confidence-row" key={label}><span>{label}</span><div className="qmi-command__confidence-track"><div className="qmi-command__confidence-fill" style={{width:`${numeric}%`}} /></div><strong>{value === null || value === undefined ? "N/A" : formatPercent(value)}</strong></div>;})}
        </div>
        <div className="qmi-command__confidence-footer"><div className="qmi-command__confidence-source"><span>Main confidence source</span><strong>{pretty(confidenceDecomposition?.main_confidence_source||"Unavailable")}</strong></div><div className="qmi-command__confidence-source"><span>Main uncertainty source</span><strong>{pretty(confidenceDecomposition?.main_uncertainty_source||"Unavailable")}</strong></div></div>
      </div>

      <div className="qmi-command__attribution">
        <div className="qmi-command__attribution-head">
          <div>
            <span>DE-DI-004 · Decision Change Attribution</span>
            <strong>
              {postureChange?.detectable
                ? `${pretty(postureChange?.previous)} → ${pretty(postureChange?.current)}`
                : `Current posture · ${pretty(postureChange?.current || posture)}`}
            </strong>
          </div>
          <div className={`qmi-command__attribution-pressure ${evolutionTone(attributionPressure?.state)}`}>
            {pretty(attributionPressure?.state || "Insufficient History")} · {formatScore(attributionPressure?.net_score)}
          </div>
        </div>
        {attribution?.available ? (
          <>
            <div className="qmi-command__attribution-summary">{attribution?.summary}</div>
            <div className="qmi-command__attribution-grid">
              <div className="qmi-command__cause is-positive">
                <span>Primary improvement</span>
                <strong>{pretty(attribution?.primary_improvement?.engine || "None")}</strong>
                <em>{attribution?.primary_improvement ? `${signedDelta(attribution.primary_improvement.score_delta)} score · ${formatPercent(attribution.primary_improvement.effective_weight_pct)} weight` : "No material improving driver"}</em>
              </div>
              <div className="qmi-command__cause is-negative">
                <span>Primary deterioration</span>
                <strong>{pretty(attribution?.primary_deterioration?.engine || "None")}</strong>
                <em>{attribution?.primary_deterioration ? `${signedDelta(attribution.primary_deterioration.score_delta)} score · ${formatPercent(attribution.primary_deterioration.effective_weight_pct)} weight` : "No material deteriorating driver"}</em>
              </div>
            </div>
            <div className="qmi-command__metric-pressure">
              {(attribution?.metric_causes || []).map((metric) => (
                <span className={evolutionTone(metric?.direction)} key={metric?.metric}>
                  {metric?.metric}: {signedDelta(metric?.delta)} · {pretty(metric?.direction)}
                </span>
              ))}
            </div>
          </>
        ) : (
          <div className="qmi-command__evolution-note">Attribution activates automatically when a persisted baseline is available.</div>
        )}
      </div>

      <div className="qmi-command__timeline">
        <div className="qmi-command__timeline-head">
          <div><span>FE-DI-003 · Evolution Timeline</span><strong>Technical trajectory across persisted snapshots</strong></div>
          <div>{timeline?.point_count || 0} observations</div>
        </div>
        {timeline?.available ? (
          <>
            <div className="qmi-command__timeline-grid">
              <MiniTimeline label="Direction" values={timelinePoints.map((p) => p?.direction_score)} />
              <MiniTimeline label="Readiness" values={timelinePoints.map((p) => p?.transition_readiness)} suffix="%" />
              <MiniTimeline label="Transition" values={timelinePoints.map((p) => p?.transition_probability)} suffix="%" />
              <MiniTimeline label="Risk" values={timelinePoints.map((p) => p?.risk_score)} invert />
            </div>
            {Object.keys(timelineDrivers).length > 0 && (
              <div className="qmi-command__timeline-drivers">
                <div className="qmi-command__timeline-drivers-title">Driver trajectories</div>
                {Object.entries(timelineDrivers).slice(0, 7).map(([engine, points]) => (
                  <MiniTimeline key={engine} label={pretty(engine)} values={(points || []).map((point) => point?.score)} />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="qmi-command__evolution-note">Timeline activates automatically after at least two persisted observations.</div>
        )}
      </div>

      <div className="qmi-command__bottom">
        <div className="qmi-command__card">
          <div className="qmi-command__card-title"><CheckCircle2 size={12} /> What QMI allows</div>
          <div className="qmi-command__permissions">
            {actionKeys.map((key) => {
              const value = permissionValue(permissions, key);
              const tone = permissionTone(value);
              const Icon = tone === "is-negative" ? Ban : CheckCircle2;
              return (
                <div className={`qmi-command__permission ${tone}`} key={key}>
                  <span>{key}</span>
                  <strong><Icon size={10} /> {pretty(value)}</strong>
                </div>
              );
            })}
          </div>
        </div>

        <div className="qmi-command__card">
          <div className="qmi-command__card-title"><ArrowRight size={12} /> What changes the decision</div>
          <div className="qmi-command__conditions">
            {changeConditions.length ? changeConditions.map((item, index) => (
              <div className="qmi-command__condition" key={`decision-condition-${index}`}>
                <div className="qmi-command__condition-index">{index + 1}</div>
                <div>
                  <strong>{conditionText(item)}</strong>
                  <small>
                    {pretty(item?.status || "OPEN")} · {pretty(item?.engine || item?.condition || "Decision release condition")}
                  </small>
                </div>
              </div>
            )) : (
              <div className="qmi-command__condition">
                <div className="qmi-command__condition-index">–</div>
                <div><strong>No release conditions reported</strong></div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

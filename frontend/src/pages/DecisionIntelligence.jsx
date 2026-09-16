import { useEffect, useState } from "react";
import {
  AlertTriangle,
  RefreshCw,
  Search,
} from "lucide-react";

import DecisionCommandPanel from "../components/decision/DecisionCommandPanel";
import { getTechnicalUiSnapshot } from "../services/technicalService";
import "../styles/qmi-typography.css";

function pretty(value) {
  if (value === null || value === undefined || value === "") return "--";
  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(digits)}%`;
}

export default function DecisionIntelligence({ token = "" }) {
  const [symbol, setSymbol] = useState("NIO");
  const [submittedSymbol, setSubmittedSymbol] = useState("NIO");
  const [period, setPeriod] = useState("1y");
  const [interval, setInterval] = useState("1d");
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadDecisionWorkspace() {
      setLoading(true);
      setError("");

      try {
        const result = await getTechnicalUiSnapshot(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          historyLimit: 500,
          token,
          signal: controller.signal,
        });

        setSnapshot(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load Decision Intelligence workspace:", requestError);
          setSnapshot(null);
          setError(
            requestError?.message ||
              "Unable to load QMI Decision Intelligence from the backend"
          );
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    loadDecisionWorkspace();
    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  const synthesis = snapshot?.decision_synthesis || null;
  const synthesisCore =
    synthesis?.technical_decision_synthesis ||
    synthesis?.decision_synthesis ||
    {};

  const transition = synthesisCore?.transition || {};
  const marketContext = synthesisCore?.market_context || {};
  const setup = snapshot?.technical_setup?.technical_setup || {};
  const pricePlan = snapshot?.technical_price_plan?.technical_price_plan || {};
  const executionPlan =
    snapshot?.execution_plan?.technical_execution_plan ||
    snapshot?.execution_plan?.execution_plan ||
    {};
  const executionState = executionPlan?.execution_state || {};



  function submit(event) {
    event.preventDefault();
    const normalized = symbol.trim().toUpperCase();
    if (!normalized) return;
    setSymbol(normalized);
    setSubmittedSymbol(normalized);
  }

  return (
    <div className="qmi-di-workspace">
      <style>{`
        .qmi-di-workspace { display:grid; gap:16px; }
        .qmi-di-workspace__hero,
        .qmi-di-workspace__toolbar,
        .qmi-di-workspace__context {
          border:1px solid var(--border,rgba(148,163,184,.16));
          border-radius:16px;
          background:var(--panel-bg,rgba(15,23,42,.78));
          box-shadow:0 14px 34px rgba(2,6,23,.09);
        }
        .qmi-di-workspace__hero {
          padding:22px;
          display:flex;
          align-items:flex-start;
          justify-content:space-between;
          gap:18px;
          background:
            radial-gradient(circle at 86% 5%,rgba(37,99,235,.12),transparent 30%),
            linear-gradient(135deg,rgba(37,99,235,.055),rgba(15,23,42,.78) 48%);
        }
        .qmi-di-workspace__eyebrow { color:#60a5fa; font-size:11px; font-weight:950; letter-spacing:.1em; text-transform:uppercase; }
        .qmi-di-workspace__hero h1 { margin:6px 0 5px; font-size:30px; line-height:1.05; font-weight:950; letter-spacing:-.035em; }
        .qmi-di-workspace__hero p { margin:0; max-width:760px; color:#9eabbc; font-size:13px; line-height:1.55; font-weight:700; }
        .qmi-di-workspace__scope { padding:8px 11px; border:1px solid rgba(96,165,250,.2); border-radius:10px; color:#60a5fa; background:rgba(37,99,235,.07); font-size:11px; font-weight:900; white-space:nowrap; }
        .qmi-di-workspace__toolbar { padding:14px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
        .qmi-di-workspace__search { position:relative; flex:1 1 360px; }
        .qmi-di-workspace__search svg { position:absolute; left:13px; top:50%; transform:translateY(-50%); opacity:.55; }
        .qmi-di-workspace__search input,
        .qmi-di-workspace__toolbar select {
          min-height:42px; border:1px solid var(--border,rgba(148,163,184,.18)); border-radius:10px;
          background:var(--surface,rgba(15,23,42,.55)); color:inherit; outline:none;
        }
        .qmi-di-workspace__search input { width:100%; padding:0 12px 0 40px; font-size:15px; font-weight:900; letter-spacing:.04em; box-sizing:border-box; }
        .qmi-di-workspace__toolbar select { padding:0 12px; font-weight:800; }
        .qmi-di-workspace__toolbar button { min-height:42px; padding:0 15px; display:inline-flex; align-items:center; gap:7px; border:0; border-radius:10px; background:#2563eb; color:white; font-weight:900; cursor:pointer; }
        .qmi-di-workspace__context { padding:16px; }
        .qmi-di-workspace__context-head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }
        .qmi-di-workspace__context-head span { color:#8b9ab0; font-size:10px; font-weight:900; letter-spacing:.065em; text-transform:uppercase; }
        .qmi-di-workspace__context-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px; }
        .qmi-di-workspace__context-item { padding:10px 11px; border-radius:10px; background:rgba(2,6,23,.12); border:1px solid rgba(148,163,184,.09); }
        .qmi-di-workspace__context-item span { display:block; color:#8190a5; font-size:9px; font-weight:900; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-di-workspace__context-item strong { display:block; margin-top:5px; font-size:13px; font-weight:900; }
        .qmi-di-workspace__evidence-label { display:flex; align-items:flex-end; justify-content:space-between; gap:12px; padding:2px 2px 0; }
        .qmi-di-workspace__evidence-label span { color:#8b9ab0; font-size:10px; font-weight:950; letter-spacing:.08em; text-transform:uppercase; }
        .qmi-di-workspace__evidence-label small { color:#68778b; font-size:10px; font-weight:750; }
        .qmi-di-workspace__error { padding:14px; display:flex; align-items:center; gap:8px; border:1px solid rgba(255,97,120,.18); border-radius:12px; color:#ff8798; background:rgba(255,97,120,.05); font-size:12px; font-weight:800; }
        @media(max-width:1100px){ .qmi-di-workspace__context-grid{grid-template-columns:repeat(2,minmax(0,1fr));} }
        @media(max-width:650px){ .qmi-di-workspace__hero{flex-direction:column;} .qmi-di-workspace__context-grid{grid-template-columns:1fr;} }
      `}</style>

      <section className="qmi-di-workspace__hero">
        <div>
          <span className="qmi-di-workspace__eyebrow">FE-DI-001 · Decision Intelligence Panel</span>
          <h1>Decision Intelligence</h1>
          <p>
            Decision command center. QMI compresses the technical pipeline into one readable view:
            what to do, why, what is allowed and what must change before the decision can evolve.
          </p>
        </div>
        <div className="qmi-di-workspace__scope">DECISION COMMAND · LIVE</div>
      </section>

      <form className="qmi-di-workspace__toolbar" onSubmit={submit}>
        <div className="qmi-di-workspace__search">
          <Search size={16} />
          <input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="Ticker" />
        </div>
        <select value={period} onChange={(event) => setPeriod(event.target.value)}>
          <option value="3mo">3M</option>
          <option value="6mo">6M</option>
          <option value="1y">1Y</option>
          <option value="2y">2Y</option>
          <option value="5y">5Y</option>
        </select>
        <select value={interval} onChange={(event) => setInterval(event.target.value)}>
          <option value="1d">1D</option>
          <option value="1wk">1W</option>
        </select>
        <button type="submit" disabled={loading}>
          <RefreshCw size={15} /> {loading ? "Analyzing" : "Analyze"}
        </button>
      </form>

      {error && (
        <div className="qmi-di-workspace__error">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      <DecisionCommandPanel
        symbol={submittedSymbol}
        decisionSynthesis={synthesis}
        executionPlan={snapshot?.execution_plan}
        confluence={snapshot?.confluence}
        decisionEvolution={snapshot?.decision_evolution}
        evolutionTimeline={snapshot?.evolution_timeline}
        decisionChangeAttribution={snapshot?.decision_change_attribution}
        decisionConfidenceDecomposition={snapshot?.decision_confidence_decomposition}
        decisionReliability={snapshot?.decision_reliability}
        decisionReliabilityBreakdown={snapshot?.decision_reliability_breakdown}
        decisionOutcome={snapshot?.decision_outcome}
        decisionCalibration={snapshot?.decision_calibration}
        decisionMemory={snapshot?.decision_memory}
        historicalOutcomeMemory={snapshot?.historical_outcome_memory}
        historicalEdge={snapshot?.historical_edge}
        decisionEvidenceAlignment={snapshot?.decision_evidence_alignment}
        decisionEvidenceScore={snapshot?.decision_evidence_score}
        decisionEvidenceGate={snapshot?.decision_evidence_gate}
        decisionValidationState={snapshot?.decision_validation_state}
        decisionValidationMomentum={snapshot?.decision_validation_momentum}
        decisionContradictionGuard={snapshot?.decision_contradiction_guard}
        shadowAdaptiveDecision={snapshot?.shadow_adaptive_decision}
        decisionIntelligenceQualityControl={snapshot?.decision_intelligence_quality_control}
        loading={loading}
        error={error}
      />

      <section className="qmi-di-workspace__context">
        <div className="qmi-di-workspace__context-head">
          <span>Execution Context</span>
          <span>{submittedSymbol} · {period.toUpperCase()} · {interval.toUpperCase()}</span>
        </div>
        <div className="qmi-di-workspace__context-grid">
          <div className="qmi-di-workspace__context-item"><span>Setup Status</span><strong>{pretty(setup?.setup_status)}</strong></div>
          <div className="qmi-di-workspace__context-item"><span>Setup Direction</span><strong>{pretty(setup?.direction)}</strong></div>
          <div className="qmi-di-workspace__context-item"><span>Price Authorization</span><strong>{pretty(pricePlan?.authorization)}</strong></div>
          <div className="qmi-di-workspace__context-item"><span>Execution State</span><strong>{pretty(executionState?.state)}</strong></div>
        </div>
      </section>
    </div>
  );
}

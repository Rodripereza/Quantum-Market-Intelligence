import { Activity, AlertTriangle, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";

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

function formatScore(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const number = Number(value);
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function toneFor(value) {
  const normalized = String(value || "").trim().toUpperCase();
  if (["PERMITTED", "PRIMARY", "BUY", "ENTER", "ADD", "BULLISH", "POSITIVE"].includes(normalized)) {
    return "is-positive";
  }
  if (["BLOCKED", "PROHIBITED", "HIGH", "HARD_BLOCK", "BEARISH", "NEGATIVE", "EXIT"].includes(normalized)) {
    return "is-negative";
  }
  if (["WATCH", "CONDITIONAL", "EARLY", "WAIT", "NEUTRAL", "REDUCE"].includes(normalized)) {
    return "is-watch";
  }
  return "";
}

export default function DecisionIntelligencePanel({
  symbol = "",
  decisionSynthesis = null,
  loading = false,
  error = "",
}) {
  const core =
    decisionSynthesis?.technical_decision_synthesis ||
    decisionSynthesis?.decision_synthesis ||
    {};

  const transition = core?.transition || {};
  const marketContext = core?.market_context || {};
  const trace = core?.decision_trace || {};
  const permissions = trace?.action_permissions || core?.action_permissions || {};
  const blockers = Array.isArray(core?.blockers) ? core.blockers : [];

  const posture = core?.final_posture || trace?.final_posture || "--";
  const conviction = core?.conviction ?? core?.conviction_score;
  const timing = core?.timing || "--";
  const risk = core?.risk_state || core?.risk || "--";
  const executionState = core?.execution_state || transition?.execution_state || "--";
  const currentState = transition?.current_state || core?.current_state || "--";
  const targetState = transition?.target_state || transition?.next_state || core?.target_state || "--";
  const scenario = marketContext?.primary_scenario || core?.primary_scenario || "--";
  const direction = marketContext?.direction_score ?? core?.direction_score;
  const executionConfidence = marketContext?.execution_confidence ?? core?.execution_confidence;
  const rationale = core?.rationale || "";
  const blockerCount = trace?.blocker_count ?? core?.blocker_count ?? blockers.length;

  const permission = (key) => {
    const value = permissions?.[key] ?? permissions?.[String(key).toUpperCase()] ?? "--";
    return typeof value === "object"
      ? value?.state || value?.permission || value?.status || "--"
      : value;
  };

  const actionKeys = ["WAIT", "ENTER", "ADD", "REDUCE", "EXIT"];

  return (
    <section className="qmi-di-panel">
      <style>{`
        .qmi-di-panel {
          padding: 18px;
          background:
            radial-gradient(circle at 86% 10%, rgba(37,99,235,.11), transparent 30%),
            linear-gradient(145deg, rgba(37,99,235,.055), rgba(15,23,42,.78) 44%);
          border: 1px solid var(--border, rgba(148,163,184,.16));
          border-radius: 16px;
          box-shadow: 0 16px 38px rgba(2,6,23,.10);
          min-width: 0;
        }
        .qmi-di__header { display:flex; align-items:flex-start; justify-content:space-between; gap:14px; margin-bottom:12px; }
        .qmi-di__identity { display:flex; align-items:center; gap:11px; min-width:0; }
        .qmi-di__icon { width:40px; height:40px; border-radius:11px; display:grid; place-items:center; flex:0 0 auto; color:#60a5fa; background:rgba(37,99,235,.12); border:1px solid rgba(96,165,250,.14); }
        .qmi-di__kicker { display:block; color:#7f8da3; font-size:10px; line-height:1.2; font-weight:900; letter-spacing:.085em; text-transform:uppercase; }
        .qmi-di__title { margin:3px 0 0; color:var(--text,#f8fafc); font-size:18px; line-height:1.2; font-weight:900; letter-spacing:-.015em; }
        .qmi-di__badge { min-width:118px; padding:8px 11px; border-radius:10px; text-align:center; font-size:12px; font-weight:950; color:#f4c542; background:rgba(244,197,66,.07); border:1px solid rgba(244,197,66,.26); }
        .qmi-di__status { display:flex; align-items:center; gap:8px; min-height:48px; color:#9aa7b9; font-size:13px; font-weight:800; }
        .qmi-di__status.is-error { color:#ff8798; }
        .qmi-di__hero { display:grid; grid-template-columns:1.2fr 1.35fr repeat(4,minmax(0,1fr)); gap:7px; }
        .qmi-di__card { min-width:0; padding:10px 11px; border:1px solid rgba(148,163,184,.11); border-radius:10px; background:rgba(148,163,184,.028); }
        .qmi-di__card span, .qmi-di__strip span { display:block; margin-bottom:5px; color:#8b9ab0; font-size:10px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-di__card strong { display:block; color:var(--text,#f8fafc); font-size:14px; line-height:1.25; font-weight:950; overflow-wrap:anywhere; }
        .qmi-di__card small { display:block; margin-top:4px; color:#9eabbc; font-size:10px; line-height:1.35; font-weight:700; }
        .qmi-di__card.is-posture strong { color:#f4c542; font-size:17px; }
        .qmi-di__transition { display:flex; align-items:center; gap:6px; flex-wrap:wrap; color:#60a5fa !important; }
        .qmi-di__permissions { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:6px; margin-top:7px; }
        .qmi-di__permission { padding:8px 9px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.14); }
        .qmi-di__permission span { display:block; margin-bottom:3px; color:#7f8da3; font-size:9px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-di__permission strong { display:flex; align-items:center; gap:5px; color:#c8d2e1; font-size:11px; line-height:1.15; font-weight:900; }
        .qmi-di__permission.is-positive strong { color:#31d890; }
        .qmi-di__permission.is-negative strong { color:#ff6178; }
        .qmi-di__permission.is-watch strong { color:#f4c542; }
        .qmi-di__footer { display:grid; grid-template-columns:minmax(180px,.8fr) minmax(0,2.2fr); gap:7px; margin-top:7px; }
        .qmi-di__strip { min-width:0; padding:8px 10px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.11); }
        .qmi-di__strip-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
        .qmi-di__strip-head strong { font-size:16px; font-weight:950; color:var(--text,#f8fafc); }
        .qmi-di__blockers { display:flex; flex-wrap:wrap; gap:5px; margin-top:5px; }
        .qmi-di__blocker { padding:4px 6px; border-radius:7px; color:#ff8798; background:rgba(255,97,120,.055); border:1px solid rgba(255,97,120,.11); font-size:9px; font-weight:800; }
        .qmi-di__rationale { color:#a7b3c4; font-size:12px; line-height:1.45; font-weight:700; }
        @media (max-width:1380px) { .qmi-di__hero { grid-template-columns:repeat(3,minmax(0,1fr)); } }
        @media (max-width:900px) { .qmi-di__hero { grid-template-columns:repeat(2,minmax(0,1fr)); } .qmi-di__footer { grid-template-columns:1fr; } }
        @media (max-width:620px) { .qmi-di__header { flex-direction:column; } .qmi-di__hero,.qmi-di__permissions { grid-template-columns:1fr; } .qmi-di__badge { min-width:0; } }
      `}</style>

      <div className="qmi-di__header">
        <div className="qmi-di__identity">
          <div className="qmi-di__icon"><ShieldCheck size={19} strokeWidth={1.8} /></div>
          <div>
            <span className="qmi-di__kicker">FE-DI-001 · DECISION INTELLIGENCE · {symbol}</span>
            <h2 className="qmi-di__title">QMI Decision Intelligence Panel</h2>
          </div>
        </div>
        <div className="qmi-di__badge">{pretty(posture)}</div>
      </div>

      {loading && !decisionSynthesis ? (
        <div className="qmi-di__status"><Activity size={15} /> Building final decision intelligence...</div>
      ) : error ? (
        <div className="qmi-di__status is-error"><AlertTriangle size={15} /> Decision intelligence unavailable: {error}</div>
      ) : (
        <>
          <div className="qmi-di__hero">
            <div className="qmi-di__card is-posture">
              <span>Final Posture</span>
              <strong>{pretty(posture)}</strong>
              <small>Conviction {formatNumber(conviction, 1)}</small>
            </div>
            <div className="qmi-di__card">
              <span>State Transition</span>
              <strong className="qmi-di__transition">{pretty(currentState)} <ArrowRight size={13} /> {pretty(targetState)}</strong>
              <small>{pretty(executionState)}</small>
            </div>
            <div className="qmi-di__card"><span>Timing</span><strong>{pretty(timing)}</strong><small>Execution timing</small></div>
            <div className="qmi-di__card"><span>Risk</span><strong>{pretty(risk)}</strong><small>Technical risk state</small></div>
            <div className="qmi-di__card"><span>Primary Scenario</span><strong>{pretty(scenario)}</strong><small>Direction {formatScore(direction)}</small></div>
            <div className="qmi-di__card"><span>Execution Confidence</span><strong>{formatPercent(executionConfidence)}</strong><small>Final pipeline confidence</small></div>
          </div>

          <div className="qmi-di__permissions">
            {actionKeys.map((key) => {
              const value = permission(key);
              const tone = toneFor(value);
              return (
                <div className={`qmi-di__permission ${tone}`} key={key}>
                  <span>{key}</span>
                  <strong><CheckCircle2 size={11} /> {pretty(value)}</strong>
                </div>
              );
            })}
          </div>

          <div className="qmi-di__footer">
            <div className="qmi-di__strip">
              <div className="qmi-di__strip-head"><span>Active Blockers</span><strong>{blockerCount}</strong></div>
              {blockers.length > 0 && (
                <div className="qmi-di__blockers">
                  {blockers.slice(0, 5).map((item, index) => (
                    <div className="qmi-di__blocker" key={`di-blocker-${index}`}>
                      {pretty(item?.severity)} · {pretty(item?.reason || item?.type)}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="qmi-di__strip">
              <span>QMI Rationale</span>
              <div className="qmi-di__rationale">
                {rationale || "Final deterministic synthesis of the technical decision pipeline."}
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

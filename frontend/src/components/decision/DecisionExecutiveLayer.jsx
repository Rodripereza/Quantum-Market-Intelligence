import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Ban,
  CheckCircle2,
  CircleDot,
  ShieldAlert,
  Target,
} from "lucide-react";

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

function permissionValue(permissions, key) {
  const value = permissions?.[key] ?? permissions?.[String(key).toUpperCase()] ?? "--";
  return typeof value === "object"
    ? value?.state || value?.permission || value?.status || "--"
    : value;
}

function permissionClass(value) {
  const normalized = String(value || "").toUpperCase();
  if (["PRIMARY", "PERMITTED", "ALLOWED", "ENTER", "BUY"].includes(normalized)) return "is-positive";
  if (["BLOCKED", "PROHIBITED", "HARD_BLOCK", "DENIED"].includes(normalized)) return "is-negative";
  if (["CONDITIONAL", "WATCH", "WAIT", "REDUCE"].includes(normalized)) return "is-watch";
  return "";
}

function postureClass(value) {
  const normalized = String(value || "").toUpperCase();
  if (["ENTER", "BUY", "ADD", "ACCUMULATE", "LONG"].includes(normalized)) return "is-positive";
  if (["REDUCE", "EXIT", "SELL", "DEFENSIVE"].includes(normalized)) return "is-negative";
  return "is-watch";
}

export default function DecisionExecutiveLayer({
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
  const risk = core?.risk_state || core?.risk || "--";
  const timing = core?.timing || "--";
  const scenario = marketContext?.primary_scenario || core?.primary_scenario || "--";
  const executionConfidence =
    marketContext?.execution_confidence ?? core?.execution_confidence;
  const rationale = core?.rationale || "";
  const currentState = transition?.current_state || core?.current_state || "--";
  const targetState =
    transition?.target_state || transition?.next_state || core?.target_state || "--";

  const actionKeys = ["WAIT", "ENTER", "ADD", "REDUCE", "EXIT"];

  if (loading && !decisionSynthesis) {
    return (
      <section className="qmi-exec-layer qmi-exec-layer--status">
        <Activity size={17} /> Building executive decision layer...
      </section>
    );
  }

  if (error) {
    return (
      <section className="qmi-exec-layer qmi-exec-layer--status is-error">
        <AlertTriangle size={17} /> Executive decision unavailable: {error}
      </section>
    );
  }

  return (
    <section className={`qmi-exec-layer ${postureClass(posture)}`}>
      <style>{`
        .qmi-exec-layer {
          position:relative;
          overflow:hidden;
          padding:20px;
          border:1px solid rgba(148,163,184,.16);
          border-radius:16px;
          background:
            radial-gradient(circle at 89% 8%, rgba(59,130,246,.15), transparent 31%),
            linear-gradient(135deg, rgba(15,23,42,.96), rgba(9,15,27,.92));
          box-shadow:0 18px 42px rgba(2,6,23,.13);
        }
        .qmi-exec-layer::before {
          content:"";
          position:absolute;
          inset:0 auto 0 0;
          width:3px;
          background:#f4c542;
        }
        .qmi-exec-layer.is-positive::before { background:#31d890; }
        .qmi-exec-layer.is-negative::before { background:#ff6178; }
        .qmi-exec-layer--status { display:flex; align-items:center; gap:8px; color:#9eabbc; font-size:13px; font-weight:800; }
        .qmi-exec-layer--status.is-error { color:#ff8798; }
        .qmi-exec__top { display:grid; grid-template-columns:minmax(240px,.9fr) minmax(0,2.1fr); gap:14px; }
        .qmi-exec__directive {
          min-width:0;
          padding:16px;
          border:1px solid rgba(148,163,184,.12);
          border-radius:13px;
          background:rgba(2,6,23,.18);
        }
        .qmi-exec__eyebrow { color:#60a5fa; font-size:9px; line-height:1.2; font-weight:950; letter-spacing:.11em; text-transform:uppercase; }
        .qmi-exec__symbol { margin-left:6px; color:#7f8da3; }
        .qmi-exec__posture { margin:8px 0 6px; color:#f4c542; font-size:34px; line-height:.98; font-weight:950; letter-spacing:-.045em; text-transform:uppercase; }
        .qmi-exec-layer.is-positive .qmi-exec__posture { color:#31d890; }
        .qmi-exec-layer.is-negative .qmi-exec__posture { color:#ff6178; }
        .qmi-exec__transition { display:flex; align-items:center; flex-wrap:wrap; gap:6px; margin-top:8px; color:#9eabbc; font-size:11px; font-weight:800; }
        .qmi-exec__metrics { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:7px; margin-top:13px; }
        .qmi-exec__metric { min-width:0; padding:9px 10px; border:1px solid rgba(148,163,184,.09); border-radius:9px; background:rgba(148,163,184,.025); }
        .qmi-exec__metric span { display:block; color:#7f8da3; font-size:8px; font-weight:900; letter-spacing:.065em; text-transform:uppercase; }
        .qmi-exec__metric strong { display:block; margin-top:4px; color:#f8fafc; font-size:12px; line-height:1.2; font-weight:950; overflow-wrap:anywhere; }
        .qmi-exec__reason {
          min-width:0;
          padding:16px;
          border:1px solid rgba(148,163,184,.11);
          border-radius:13px;
          background:rgba(148,163,184,.025);
        }
        .qmi-exec__section-title { display:flex; align-items:center; gap:7px; color:#dbe7f7; font-size:10px; font-weight:950; letter-spacing:.075em; text-transform:uppercase; }
        .qmi-exec__rationale { margin-top:10px; color:#c0cbda; font-size:13px; line-height:1.5; font-weight:800; }
        .qmi-exec__blockers { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
        .qmi-exec__blocker { display:flex; align-items:center; gap:5px; padding:5px 7px; border:1px solid rgba(255,97,120,.14); border-radius:7px; background:rgba(255,97,120,.055); color:#ff8798; font-size:9px; line-height:1.3; font-weight:850; }
        .qmi-exec__permissions { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:7px; margin-top:10px; }
        .qmi-exec__permission { min-width:0; padding:10px 11px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.15); }
        .qmi-exec__permission span { display:block; color:#7f8da3; font-size:8px; font-weight:900; letter-spacing:.065em; text-transform:uppercase; }
        .qmi-exec__permission strong { display:flex; align-items:center; gap:5px; margin-top:4px; color:#c7d2e0; font-size:11px; font-weight:950; }
        .qmi-exec__permission.is-positive strong { color:#31d890; }
        .qmi-exec__permission.is-negative strong { color:#ff6178; }
        .qmi-exec__permission.is-watch strong { color:#f4c542; }
        .qmi-exec__permission-icon { flex:0 0 auto; }
        @media(max-width:1100px){
          .qmi-exec__top{grid-template-columns:1fr;}
          .qmi-exec__metrics{grid-template-columns:repeat(2,minmax(0,1fr));}
        }
        @media(max-width:760px){
          .qmi-exec__permissions{grid-template-columns:repeat(2,minmax(0,1fr));}
        }
        @media(max-width:520px){
          .qmi-exec__metrics,.qmi-exec__permissions{grid-template-columns:1fr;}
          .qmi-exec__posture{font-size:28px;}
        }
      `}</style>

      <div className="qmi-exec__top">
        <div className="qmi-exec__directive">
          <div className="qmi-exec__eyebrow">
            QMI Executive Decision <span className="qmi-exec__symbol">· {symbol}</span>
          </div>
          <div className="qmi-exec__posture">{pretty(posture)}</div>
          <div className="qmi-exec__transition">
            <CircleDot size={11} /> {pretty(currentState)} <ArrowRight size={12} /> {pretty(targetState)}
          </div>

          <div className="qmi-exec__metrics">
            <div className="qmi-exec__metric"><span>Conviction</span><strong>{formatPercent(conviction)}</strong></div>
            <div className="qmi-exec__metric"><span>Execution Conf.</span><strong>{formatPercent(executionConfidence)}</strong></div>
            <div className="qmi-exec__metric"><span>Risk</span><strong>{pretty(risk)}</strong></div>
            <div className="qmi-exec__metric"><span>Timing</span><strong>{pretty(timing)}</strong></div>
          </div>
        </div>

        <div className="qmi-exec__reason">
          <div className="qmi-exec__section-title"><Target size={13} /> Why now</div>
          <div className="qmi-exec__rationale">
            {rationale || `Primary scenario: ${pretty(scenario)}.`}
          </div>
          <div className="qmi-exec__blockers">
            {blockers.length ? blockers.slice(0, 6).map((item, index) => (
              <div className="qmi-exec__blocker" key={`exec-blocker-${index}`}>
                <ShieldAlert size={10} /> {pretty(item?.severity)} · {pretty(item?.reason || item?.type)}
              </div>
            )) : (
              <div className="qmi-exec__blocker" style={{ color: "#9eabbc", borderColor: "rgba(148,163,184,.10)", background: "rgba(148,163,184,.03)" }}>
                No active blockers reported
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="qmi-exec__permissions">
        {actionKeys.map((key) => {
          const value = permissionValue(permissions, key);
          const tone = permissionClass(value);
          const Icon = tone === "is-negative" ? Ban : CheckCircle2;
          return (
            <div className={`qmi-exec__permission ${tone}`} key={`exec-${key}`}>
              <span>{key}</span>
              <strong><Icon className="qmi-exec__permission-icon" size={11} /> {pretty(value)}</strong>
            </div>
          );
        })}
      </div>
    </section>
  );
}

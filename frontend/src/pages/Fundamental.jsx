import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Building2,
  CheckCircle2,
  Database,
  Gauge,
  GitMerge,
  Target,
  RefreshCw,
  Search,
  ShieldCheck,
  TrendingDown,
  TrendingUp,
  WalletCards,
} from "lucide-react";

import { getFundamental } from "../services/fundamentalService";
import { getQMIDecision } from "../services/qmiDecisionService";

function n(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function compactMoney(value, currency = "USD") {
  const number = n(value);

  if (number === null) return "--";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency || "USD",
    notation: Math.abs(number) >= 1_000_000 ? "compact" : "standard",
    maximumFractionDigits: 2,
  }).format(number);
}

function ratio(value, digits = 2) {
  const number = n(value);
  return number === null ? "--" : number.toFixed(digits);
}

function percent(value, digits = 1) {
  const number = n(value);
  if (number === null) return "--";
  return `${(number * 100).toFixed(digits)}%`;
}

function scorePercent(value, digits = 1) {
  const number = n(value);
  if (number === null) return "--";
  return `${number.toFixed(digits)}%`;
}

function signedPercent(value, digits = 1) {
  const number = n(value);
  if (number === null) return "--";
  const pct = number * 100;
  return `${pct > 0 ? "+" : ""}${pct.toFixed(digits)}%`;
}

function toneFromNumber(value) {
  const number = n(value);
  if (number === null) return "neutral";
  if (number > 0) return "positive";
  if (number < 0) return "negative";
  return "neutral";
}

function ratingTone(rating) {
  const value = String(rating || "").toLowerCase();
  if (value.includes("excellent") || value.includes("good")) return "positive";
  if (value.includes("poor") || value.includes("weak")) return "negative";
  return "neutral";
}

function stateTone(state) {
  const value = String(state || "").toUpperCase();

  if (
    ["STRONG", "EXPANSION", "IMPROVING", "PROFITABLE"].includes(value)
  ) {
    return "positive";
  }

  if (
    ["WEAK", "DETERIORATING", "LOSS_MAKING"].includes(value)
  ) {
    return "negative";
  }

  if (["RECOVERING", "STABLE", "ADEQUATE", "MIXED"].includes(value)) {
    return "warning";
  }

  return "neutral";
}

function prettyState(value) {
  if (!value) return "--";
  return String(value).replaceAll("_", " ");
}

function decisionTone(stance) {
  const value = String(stance || "").toUpperCase();

  if (["VERY_POSITIVE", "POSITIVE"].includes(value)) return "positive";
  if (value === "CONSTRUCTIVE") return "constructive";
  if (value === "CAUTIOUS") return "warning";
  if (value === "NEGATIVE") return "negative";

  return "neutral";
}


function integratedDecisionTone(posture) {
  const value = String(posture || "").toUpperCase();

  if (["FAVORABLE", "CONSTRUCTIVE"].includes(value)) return "positive";
  if (["CONSTRUCTIVE_BUT_WAIT", "CAUTIOUS"].includes(value)) return "warning";
  if (value === "DEFENSIVE") return "negative";
  if (value === "SELECTIVE") return "constructive";

  return "neutral";
}

function IntelligenceCard({ label, block }) {
  const state = block?.state || "UNKNOWN";
  const tone = stateTone(state);

  return (
    <div className={`qmi-fa-intel-card is-${tone}`}>
      <span>{label}</span>
      <strong>{prettyState(state)}</strong>
      <div className="qmi-fa-intel-meta">
        <b>{n(block?.score) === null ? "--" : n(block?.score).toFixed(1)}</b>
        <small>{block?.confidence || "LOW"} confidence</small>
      </div>
    </div>
  );
}


function QualityCard({ label, block, footer }) {
  const state = block?.state || "UNKNOWN";
  const tone = stateTone(state);

  return (
    <div className={`qmi-fa-quality-intel-card is-${tone}`}>
      <div>
        <span>{label}</span>
        <strong>{prettyState(state)}</strong>
      </div>

      <div className="qmi-fa-quality-intel-score">
        {n(block?.score) === null ? "--" : n(block?.score).toFixed(1)}
      </div>

      <div className="qmi-fa-quality-intel-footer">
        <small>{block?.confidence || "LOW"} confidence</small>
        {footer ? <em>{footer}</em> : null}
      </div>
    </div>
  );
}

function Metric({ label, value, detail, tone = "neutral" }) {
  return (
    <div className={`qmi-fa-metric is-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

function ListPanel({ title, icon: Icon, items = [], tone = "neutral", empty }) {
  return (
    <div className={`qmi-fa-list-panel is-${tone}`}>
      <div className="qmi-fa-list-title">
        <Icon size={16} />
        <strong>{title}</strong>
      </div>

      {items.length ? (
        <ul>
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <div className="qmi-fa-empty">{empty}</div>
      )}
    </div>
  );
}

export default function Fundamental({ token }) {
  const [symbol, setSymbol] = useState("NIO");
  const [submittedSymbol, setSubmittedSymbol] = useState("NIO");
  const [fundamental, setFundamental] = useState(null);
  const [qmiDecisionResponse, setQmiDecisionResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [qmiDecisionLoading, setQmiDecisionLoading] = useState(false);
  const [qmiDecisionError, setQmiDecisionError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadFundamental() {
      setLoading(true);
      setError("");

      try {
        const result = await getFundamental(submittedSymbol, {
          token,
          signal: controller.signal,
        });

        setFundamental(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load fundamental analysis:", requestError);
          setFundamental(null);
          setError(
            requestError?.message ||
              "Unable to load QMI Fundamental Engine"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadFundamental();

    return () => controller.abort();
  }, [submittedSymbol, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadQMIDecision() {
      setQmiDecisionLoading(true);
      setQmiDecisionError("");

      try {
        const result = await getQMIDecision(submittedSymbol, {
          period: "1y",
          interval: "1d",
          pivotWindow: 3,
          historyLimit: 500,
          token,
          signal: controller.signal,
        });

        setQmiDecisionResponse(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load QMI cross-engine decision:", requestError);
          setQmiDecisionResponse(null);
          setQmiDecisionError(
            requestError?.message ||
              "Unable to load QMI Cross-Engine Decision Fusion"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setQmiDecisionLoading(false);
        }
      }
    }

    loadQMIDecision();

    return () => controller.abort();
  }, [submittedSymbol, token]);

  const data = fundamental?.data || {};
  const profile = data?.profile || {};
  const valuation = data?.valuation || {};
  const profitability = data?.profitability || {};
  const growth = data?.growth || {};
  const health = data?.financial_health || {};
  const trends = data?.trends || {};
  const quality = data?.data_quality || {};
  const statements = data?.statements || {};
  const statementIntelligence = data?.statement_intelligence || {};
  const qualityIntelligence = data?.quality_intelligence || {};
  const decision = fundamental?.decision || {};
  const qmiDecision = qmiDecisionResponse?.qmi_decision || {};
  const qmiTechnical = qmiDecision?.technical || {};
  const qmiFundamental = qmiDecision?.fundamental || {};
  const qmiAlignment = qmiDecision?.alignment || {};
  const qmiSupportingEvidence = Array.isArray(qmiDecision?.supporting_evidence)
    ? qmiDecision.supporting_evidence
    : [];
  const qmiConflicts = Array.isArray(qmiDecision?.conflicts)
    ? qmiDecision.conflicts
    : [];

  const marketCurrency =
    profile?.market_currency || profile?.currency || "USD";
  const financialCurrency =
    profile?.financial_currency || profile?.currency || marketCurrency;

  const statementCoverage = useMemo(
    () => [
      {
        label: "Annual Income",
        value: quality?.annual_income_periods ?? statements?.annual_income?.length ?? 0,
      },
      {
        label: "Quarterly Income",
        value: quality?.quarterly_income_periods ?? statements?.quarterly_income?.length ?? 0,
      },
      {
        label: "Annual Balance",
        value: quality?.annual_balance_periods ?? statements?.annual_balance_sheet?.length ?? 0,
      },
      {
        label: "Quarterly Balance",
        value: quality?.quarterly_balance_periods ?? statements?.quarterly_balance_sheet?.length ?? 0,
      },
      {
        label: "Annual Cash Flow",
        value: quality?.annual_cash_flow_periods ?? statements?.annual_cash_flow?.length ?? 0,
      },
      {
        label: "Quarterly Cash Flow",
        value: quality?.quarterly_cash_flow_periods ?? statements?.quarterly_cash_flow?.length ?? 0,
      },
    ],
    [quality, statements]
  );

  function submit(event) {
    event.preventDefault();
    const normalized = symbol.trim().toUpperCase();

    if (!normalized) return;

    setSymbol(normalized);
    setSubmittedSymbol(normalized);
  }

  const rating = fundamental?.rating || "--";
  const score = n(fundamental?.score);
  const ratingClass = ratingTone(rating);
  const qualityScore = n(quality?.completeness_score);

  return (
    <div className="qmi-fa-page">
      <style>{`
        .qmi-fa-page {
          display: grid;
          gap: 18px;
        }

        .qmi-fa-page * {
          box-sizing: border-box;
        }

        .qmi-fa-panel {
          border: 1px solid rgba(148, 163, 184, .14);
          border-radius: 16px;
          background: rgba(15, 23, 42, .72);
          box-shadow: 0 16px 38px rgba(2, 6, 23, .10);
        }

        .qmi-fa-command {
          padding: 20px;
        }

        .qmi-fa-command-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
        }

        .qmi-fa-kicker {
          display: block;
          margin-bottom: 5px;
          color: #60a5fa;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .08em;
          text-transform: uppercase;
        }

        .qmi-fa-command h2,
        .qmi-fa-section-title h2 {
          margin: 0;
          color: #f8fafc;
          font-size: 24px;
          font-weight: 950;
          letter-spacing: -.03em;
        }

        .qmi-fa-command p,
        .qmi-fa-section-title p {
          margin: 6px 0 0;
          color: #94a3b8;
          font-size: 12px;
          line-height: 1.55;
        }

        .qmi-fa-search {
          display: flex;
          gap: 9px;
          margin-top: 18px;
        }

        .qmi-fa-search-box {
          min-width: 260px;
          flex: 1;
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 13px;
          height: 46px;
          border: 1px solid rgba(148, 163, 184, .16);
          border-radius: 11px;
          background: rgba(2, 6, 23, .32);
        }

        .qmi-fa-search-box input {
          width: 100%;
          border: 0;
          outline: 0;
          background: transparent;
          color: #f8fafc;
          font-size: 15px;
          font-weight: 850;
          text-transform: uppercase;
        }

        .qmi-fa-search button {
          min-width: 122px;
          border: 1px solid rgba(59, 130, 246, .55);
          border-radius: 11px;
          background: rgba(37, 99, 235, .92);
          color: white;
          font-weight: 900;
          cursor: pointer;
        }

        .qmi-fa-search button:disabled {
          cursor: not-allowed;
          opacity: .65;
        }

        .qmi-fa-status {
          display: flex;
          align-items: center;
          gap: 8px;
          min-width: 142px;
          padding: 9px 11px;
          border-radius: 10px;
          border: 1px solid rgba(34, 197, 94, .22);
          background: rgba(34, 197, 94, .06);
          color: #86efac;
          font-size: 11px;
          font-weight: 850;
        }

        .qmi-fa-status.is-loading {
          border-color: rgba(96, 165, 250, .25);
          background: rgba(96, 165, 250, .06);
          color: #93c5fd;
        }

        .qmi-fa-status.is-error {
          border-color: rgba(248, 113, 113, .25);
          background: rgba(248, 113, 113, .06);
          color: #fca5a5;
        }

        .qmi-fa-spin {
          animation: qmi-fa-spin 1s linear infinite;
        }

        @keyframes qmi-fa-spin {
          to { transform: rotate(360deg); }
        }

        .qmi-fa-alert {
          padding: 14px 16px;
          border: 1px solid rgba(248, 113, 113, .30);
          border-radius: 12px;
          background: rgba(248, 113, 113, .08);
          color: #fecaca;
          font-size: 12px;
          font-weight: 750;
        }

        .qmi-fa-hero {
          display: grid;
          grid-template-columns: 1.3fr repeat(3, minmax(0, .72fr));
          gap: 10px;
          margin-top: 14px;
        }

        .qmi-fa-company,
        .qmi-fa-metric {
          min-width: 0;
          padding: 16px;
          border: 1px solid rgba(148, 163, 184, .12);
          border-radius: 12px;
          background: rgba(148, 163, 184, .035);
        }

        .qmi-fa-company span,
        .qmi-fa-metric span,
        .qmi-fa-data-row span,
        .qmi-fa-coverage-card span {
          display: block;
          margin-bottom: 7px;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-company strong {
          display: block;
          color: #f8fafc;
          font-size: 22px;
          font-weight: 950;
          overflow-wrap: anywhere;
        }

        .qmi-fa-company small,
        .qmi-fa-metric small {
          display: block;
          margin-top: 7px;
          color: #94a3b8;
          font-size: 11px;
          line-height: 1.4;
          font-weight: 650;
        }

        .qmi-fa-metric strong {
          display: block;
          color: #e2e8f0;
          font-size: 20px;
          font-weight: 950;
          overflow-wrap: anywhere;
        }

        .qmi-fa-metric.is-positive strong { color: #4ade80; }
        .qmi-fa-metric.is-negative strong { color: #fb7185; }
        .qmi-fa-metric.is-neutral strong { color: #e2e8f0; }

        .qmi-fa-section {
          padding: 18px;
        }

        .qmi-fa-section-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 15px;
          margin-bottom: 14px;
        }

        .qmi-fa-section-title {
          display: flex;
          align-items: center;
          gap: 11px;
        }

        .qmi-fa-icon-box {
          display: grid;
          width: 34px;
          height: 34px;
          place-items: center;
          border: 1px solid rgba(96, 165, 250, .20);
          border-radius: 10px;
          background: rgba(59, 130, 246, .07);
          color: #93c5fd;
        }

        .qmi-fa-section-title h2 {
          font-size: 18px;
        }

        .qmi-fa-grid-4 {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-grid-3 {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-data-card {
          padding: 13px 14px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-data-row {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 12px;
          padding: 9px 0;
          border-bottom: 1px solid rgba(148, 163, 184, .08);
        }

        .qmi-fa-data-row:last-child {
          border-bottom: 0;
        }

        .qmi-fa-data-row span {
          margin: 0;
        }

        .qmi-fa-data-row strong {
          color: #e2e8f0;
          font-size: 13px;
          font-weight: 900;
          text-align: right;
        }

        .qmi-fa-data-row strong.is-positive { color: #4ade80; }
        .qmi-fa-data-row strong.is-negative { color: #fb7185; }

        .qmi-fa-quality {
          display: grid;
          grid-template-columns: 1fr 2fr;
          gap: 10px;
        }

        .qmi-fa-quality-score {
          display: grid;
          place-items: center;
          min-height: 185px;
          padding: 16px;
          border: 1px solid rgba(96, 165, 250, .16);
          border-radius: 12px;
          background: rgba(59, 130, 246, .05);
          text-align: center;
        }

        .qmi-fa-quality-score span {
          color: #8ea0b8;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .06em;
          text-transform: uppercase;
        }

        .qmi-fa-quality-score strong {
          display: block;
          margin: 5px 0;
          color: #60a5fa;
          font-size: 42px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-quality-score small {
          color: #cbd5e1;
          font-size: 12px;
          font-weight: 800;
        }

        .qmi-fa-coverage-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 9px;
        }

        .qmi-fa-coverage-card {
          padding: 13px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 10px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-coverage-card strong {
          color: #f8fafc;
          font-size: 18px;
          font-weight: 950;
        }

        .qmi-fa-flags {
          display: flex;
          gap: 8px;
          margin-top: 9px;
          flex-wrap: wrap;
        }

        .qmi-fa-flag {
          padding: 6px 8px;
          border: 1px solid rgba(34, 197, 94, .18);
          border-radius: 8px;
          background: rgba(34, 197, 94, .05);
          color: #86efac;
          font-size: 10px;
          font-weight: 850;
        }

        .qmi-fa-flag.is-off {
          border-color: rgba(248, 113, 113, .16);
          background: rgba(248, 113, 113, .04);
          color: #fda4af;
        }

        .qmi-fa-lists {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-list-panel {
          padding: 14px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-list-title {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 10px;
          color: #cbd5e1;
        }

        .qmi-fa-list-panel.is-positive .qmi-fa-list-title { color: #86efac; }
        .qmi-fa-list-panel.is-negative .qmi-fa-list-title { color: #fda4af; }
        .qmi-fa-list-panel.is-warning .qmi-fa-list-title { color: #fcd34d; }

        .qmi-fa-list-panel ul {
          margin: 0;
          padding-left: 18px;
        }

        .qmi-fa-list-panel li,
        .qmi-fa-empty {
          margin: 6px 0;
          color: #aab6c7;
          font-size: 11px;
          line-height: 1.45;
        }

        .qmi-fa-footer {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          padding: 10px 4px 0;
          color: #64748b;
          font-size: 10px;
          font-weight: 750;
        }

        .qmi-fa-regime {
          display: grid;
          grid-template-columns: 1.15fr .85fr;
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-regime-main {
          min-height: 150px;
          padding: 18px;
          border: 1px solid rgba(96, 165, 250, .18);
          border-radius: 12px;
          background: rgba(59, 130, 246, .05);
        }

        .qmi-fa-regime-main span,
        .qmi-fa-intel-card > span,
        .qmi-fa-state-row span {
          display: block;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-regime-main strong {
          display: block;
          margin-top: 10px;
          font-size: 34px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-regime-main small {
          display: block;
          margin-top: 9px;
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-regime-score {
          display: grid;
          place-items: center;
          min-height: 150px;
          padding: 18px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 12px;
          background: rgba(148, 163, 184, .025);
          text-align: center;
        }

        .qmi-fa-regime-score span {
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-regime-score strong {
          display: block;
          margin: 6px 0;
          color: #60a5fa;
          font-size: 42px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-regime-score small {
          color: #cbd5e1;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-intel-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-intel-card {
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-intel-card strong {
          display: block;
          margin: 7px 0 11px;
          color: #e2e8f0;
          font-size: 18px;
          font-weight: 950;
        }

        .qmi-fa-intel-card.is-positive strong { color: #4ade80; }
        .qmi-fa-intel-card.is-negative strong { color: #fb7185; }
        .qmi-fa-intel-card.is-warning strong { color: #fbbf24; }

        .qmi-fa-intel-meta {
          display: flex;
          justify-content: space-between;
          gap: 10px;
          align-items: baseline;
        }

        .qmi-fa-intel-meta b {
          color: #f8fafc;
          font-size: 20px;
          font-weight: 950;
        }

        .qmi-fa-intel-meta small {
          color: #94a3b8;
          font-size: 10px;
          font-weight: 800;
          text-transform: uppercase;
        }

        .qmi-fa-state-matrix {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 9px;
          margin-top: 10px;
        }

        .qmi-fa-state-row {
          padding: 12px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 10px;
          background: rgba(148, 163, 184, .02);
        }

        .qmi-fa-state-row strong {
          display: block;
          margin-top: 7px;
          color: #e2e8f0;
          font-size: 13px;
          font-weight: 950;
        }

        .qmi-fa-state-row.is-positive strong { color: #4ade80; }
        .qmi-fa-state-row.is-negative strong { color: #fb7185; }
        .qmi-fa-state-row.is-warning strong { color: #fbbf24; }


        .qmi-fa-quality-intel-hero {
          display: grid;
          grid-template-columns: 1.15fr .85fr;
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-quality-intel-main,
        .qmi-fa-quality-intel-confidence {
          min-height: 154px;
          padding: 18px;
          border: 1px solid rgba(96, 165, 250, .18);
          border-radius: 12px;
          background: rgba(59, 130, 246, .05);
        }

        .qmi-fa-quality-intel-main span,
        .qmi-fa-quality-intel-confidence span,
        .qmi-fa-quality-intel-card span {
          display: block;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-quality-intel-main strong {
          display: block;
          margin-top: 8px;
          color: #60a5fa;
          font-size: 42px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-quality-intel-main b {
          display: block;
          margin-top: 8px;
          color: #f8fafc;
          font-size: 20px;
          font-weight: 950;
        }

        .qmi-fa-quality-intel-main small {
          display: block;
          margin-top: 8px;
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-quality-intel-confidence {
          display: grid;
          place-items: center;
          text-align: center;
          border-color: rgba(148, 163, 184, .10);
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-quality-intel-confidence strong {
          display: block;
          margin: 8px 0;
          color: #fbbf24;
          font-size: 26px;
          font-weight: 950;
        }

        .qmi-fa-quality-intel-confidence small {
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-quality-intel-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-quality-intel-card {
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
          min-width: 0;
        }

        .qmi-fa-quality-intel-card strong {
          display: block;
          margin-top: 7px;
          font-size: 17px;
          font-weight: 950;
          color: #e2e8f0;
        }

        .qmi-fa-quality-intel-card.is-positive strong { color: #4ade80; }
        .qmi-fa-quality-intel-card.is-negative strong { color: #fb7185; }
        .qmi-fa-quality-intel-card.is-warning strong { color: #fbbf24; }

        .qmi-fa-quality-intel-score {
          margin-top: 14px;
          color: #f8fafc;
          font-size: 24px;
          font-weight: 950;
        }

        .qmi-fa-quality-intel-footer {
          display: flex;
          justify-content: space-between;
          gap: 8px;
          align-items: end;
          margin-top: 12px;
        }

        .qmi-fa-quality-intel-footer small {
          color: #94a3b8;
          font-size: 10px;
          font-weight: 800;
          text-transform: uppercase;
        }

        .qmi-fa-quality-intel-footer em {
          color: #fbbf24;
          font-size: 9px;
          font-style: normal;
          font-weight: 900;
          text-transform: uppercase;
          text-align: right;
        }

        .qmi-fa-decision-hero {
          display: grid;
          grid-template-columns: 1.15fr .85fr;
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-decision-main,
        .qmi-fa-decision-score {
          min-height: 166px;
          padding: 18px;
          border: 1px solid rgba(96, 165, 250, .18);
          border-radius: 12px;
          background: rgba(59, 130, 246, .05);
        }

        .qmi-fa-decision-main span,
        .qmi-fa-decision-score span,
        .qmi-fa-decision-breakdown span,
        .qmi-fa-decision-list span {
          display: block;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-decision-main strong {
          display: block;
          margin-top: 9px;
          color: #e2e8f0;
          font-size: 34px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-decision-main.is-positive strong { color: #4ade80; }
        .qmi-fa-decision-main.is-constructive strong { color: #60a5fa; }
        .qmi-fa-decision-main.is-warning strong { color: #fbbf24; }
        .qmi-fa-decision-main.is-negative strong { color: #fb7185; }

        .qmi-fa-decision-main b {
          display: inline-block;
          margin-top: 12px;
          padding: 5px 9px;
          border: 1px solid rgba(96, 165, 250, .20);
          border-radius: 999px;
          color: #cbd5e1;
          background: rgba(59, 130, 246, .06);
          font-size: 10px;
          font-weight: 950;
          text-transform: uppercase;
        }

        .qmi-fa-decision-main small {
          display: block;
          margin-top: 10px;
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-decision-score {
          display: grid;
          place-items: center;
          text-align: center;
          border-color: rgba(148, 163, 184, .10);
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-decision-score strong {
          display: block;
          margin: 8px 0;
          color: #60a5fa;
          font-size: 46px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-decision-score small {
          color: #cbd5e1;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-decision-breakdown {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-decision-breakdown > div {
          padding: 14px 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-decision-breakdown strong {
          display: block;
          margin-top: 7px;
          color: #f8fafc;
          font-size: 22px;
          font-weight: 950;
        }

        .qmi-fa-decision-lists {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-fa-decision-list {
          min-height: 132px;
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-decision-list ul {
          margin: 10px 0 0;
          padding-left: 18px;
          color: #cbd5e1;
          font-size: 11px;
          line-height: 1.55;
        }

        .qmi-fa-decision-list.is-thesis span { color: #60a5fa; }
        .qmi-fa-decision-list.is-catalysts span { color: #4ade80; }
        .qmi-fa-decision-list.is-risks span { color: #fb7185; }

        .qmi-fa-decision-empty {
          margin-top: 10px;
          color: #64748b;
          font-size: 11px;
          font-weight: 700;
        }


        .qmi-fa-core-hero {
          display: grid;
          grid-template-columns: 1.15fr .85fr;
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-core-main,
        .qmi-fa-core-score {
          min-height: 170px;
          padding: 18px;
          border: 1px solid rgba(96, 165, 250, .18);
          border-radius: 12px;
          background: rgba(59, 130, 246, .05);
        }

        .qmi-fa-core-main span,
        .qmi-fa-core-score span,
        .qmi-fa-core-card span,
        .qmi-fa-core-list span {
          display: block;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-fa-core-main strong {
          display: block;
          margin-top: 9px;
          color: #e2e8f0;
          font-size: 34px;
          line-height: 1.05;
          font-weight: 950;
        }

        .qmi-fa-core-main.is-positive strong { color: #4ade80; }
        .qmi-fa-core-main.is-constructive strong { color: #60a5fa; }
        .qmi-fa-core-main.is-warning strong { color: #fbbf24; }
        .qmi-fa-core-main.is-negative strong { color: #fb7185; }

        .qmi-fa-core-main b {
          display: inline-block;
          margin-top: 12px;
          padding: 5px 9px;
          border: 1px solid rgba(96, 165, 250, .20);
          border-radius: 999px;
          color: #cbd5e1;
          background: rgba(59, 130, 246, .06);
          font-size: 10px;
          font-weight: 950;
          text-transform: uppercase;
        }

        .qmi-fa-core-main small {
          display: block;
          margin-top: 10px;
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
          line-height: 1.5;
        }

        .qmi-fa-core-score {
          display: grid;
          place-items: center;
          text-align: center;
          border-color: rgba(148, 163, 184, .10);
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-core-score strong {
          display: block;
          margin: 8px 0;
          color: #60a5fa;
          font-size: 46px;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-fa-core-score small {
          color: #cbd5e1;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-fa-core-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-core-card {
          min-height: 112px;
          padding: 14px 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-core-card strong {
          display: block;
          margin-top: 8px;
          color: #f8fafc;
          font-size: 20px;
          font-weight: 950;
        }

        .qmi-fa-core-card small {
          display: block;
          margin-top: 8px;
          color: #94a3b8;
          font-size: 10px;
          font-weight: 800;
          line-height: 1.45;
        }

        .qmi-fa-core-compare {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
          margin-bottom: 10px;
        }

        .qmi-fa-core-engine {
          padding: 16px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-core-engine-head {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          align-items: flex-start;
          margin-bottom: 13px;
        }

        .qmi-fa-core-engine-head span {
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .055em;
        }

        .qmi-fa-core-engine-head strong {
          display: block;
          margin-top: 6px;
          color: #f8fafc;
          font-size: 21px;
          font-weight: 950;
        }

        .qmi-fa-core-engine-head b {
          color: #60a5fa;
          font-size: 28px;
          font-weight: 950;
        }

        .qmi-fa-core-engine-meta {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 8px;
        }

        .qmi-fa-core-engine-meta div {
          padding: 9px;
          border-radius: 9px;
          background: rgba(2, 6, 23, .18);
        }

        .qmi-fa-core-engine-meta span {
          display: block;
          color: #64748b;
          font-size: 9px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .qmi-fa-core-engine-meta strong {
          display: block;
          margin-top: 5px;
          color: #cbd5e1;
          font-size: 11px;
          font-weight: 900;
          word-break: break-word;
        }

        .qmi-fa-core-lists {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }

        .qmi-fa-core-list {
          min-height: 132px;
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 11px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-fa-core-list.is-evidence span { color: #4ade80; }
        .qmi-fa-core-list.is-conflict span { color: #fbbf24; }

        .qmi-fa-core-list ul {
          margin: 10px 0 0;
          padding-left: 18px;
          color: #cbd5e1;
          font-size: 11px;
          line-height: 1.55;
        }

        .qmi-fa-core-status {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #94a3b8;
          font-size: 11px;
          font-weight: 800;
        }

        @media (max-width: 1150px) {
          .qmi-fa-hero { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .qmi-fa-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .qmi-fa-quality { grid-template-columns: 1fr; }
          .qmi-fa-regime { grid-template-columns: 1fr; }
          .qmi-fa-quality-intel-hero { grid-template-columns: 1fr; }
          .qmi-fa-decision-hero { grid-template-columns: 1fr; }
          .qmi-fa-core-hero { grid-template-columns: 1fr; }
          .qmi-fa-core-compare { grid-template-columns: 1fr; }
          .qmi-fa-decision-lists { grid-template-columns: 1fr; }
          .qmi-fa-quality-intel-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .qmi-fa-state-matrix { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .qmi-fa-decision-breakdown { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        }

        @media (max-width: 760px) {
          .qmi-fa-command-head,
          .qmi-fa-search,
          .qmi-fa-section-head {
            flex-direction: column;
          }

          .qmi-fa-search-box,
          .qmi-fa-search button {
            width: 100%;
            min-width: 0;
          }

          .qmi-fa-hero,
          .qmi-fa-grid-4,
          .qmi-fa-grid-3,
          .qmi-fa-coverage-grid,
          .qmi-fa-lists,
          .qmi-fa-intel-grid,
          .qmi-fa-quality-intel-grid,
          .qmi-fa-state-matrix,
          .qmi-fa-decision-breakdown,
          .qmi-fa-decision-lists,
          .qmi-fa-core-grid,
          .qmi-fa-core-lists {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <section className="qmi-fa-panel qmi-fa-command">
        <div className="qmi-fa-command-head">
          <div>
            <span className="qmi-fa-kicker">
              {data?.engine_version || "DE-FA"} · FUNDAMENTAL DATA ENGINE
            </span>
            <h2>QMI Fundamental Analysis</h2>
            <p>
              Normalized company fundamentals, financial statements,
              derived trends and dataset-quality diagnostics.
            </p>
          </div>

          <div
            className={`qmi-fa-status ${
              loading ? "is-loading" : error ? "is-error" : ""
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="qmi-fa-spin" size={14} />
                Analyzing
              </>
            ) : error ? (
              <>
                <AlertTriangle size={14} />
                Engine error
              </>
            ) : (
              <>
                <CheckCircle2 size={14} />
                Engine online
              </>
            )}
          </div>
        </div>

        <form className="qmi-fa-search" onSubmit={submit}>
          <div className="qmi-fa-search-box">
            <Search size={16} />
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="Ticker"
              aria-label="Ticker symbol"
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Loading..." : "Analyze"}
          </button>
        </form>

        {error ? (
          <div className="qmi-fa-alert" style={{ marginTop: 14 }}>
            {error}
          </div>
        ) : null}

        {fundamental ? (
          <div className="qmi-fa-hero">
            <div className="qmi-fa-company">
              <span>Company</span>
              <strong>
                {profile?.company_name || data?.symbol || submittedSymbol}
              </strong>
              <small>
                {data?.symbol || submittedSymbol} · {profile?.sector || "Sector unavailable"} ·{" "}
                {profile?.industry || "Industry unavailable"} · Market {marketCurrency} · Financial {financialCurrency}
              </small>
            </div>

            <Metric
              label="Fundamental Score"
              value={score === null ? "--" : score.toFixed(1)}
              detail="0–100 QMI score"
              tone={
                score === null
                  ? "neutral"
                  : score >= 70
                    ? "positive"
                    : score < 40
                      ? "negative"
                      : "neutral"
              }
            />

            <Metric
              label="Rating"
              value={rating}
              detail="QMI fundamental classification"
              tone={ratingClass}
            />

            <Metric
              label="Data Quality"
              value={
                qualityScore === null
                  ? "--"
                  : `${qualityScore.toFixed(1)}%`
              }
              detail={quality?.completeness_grade || "Coverage grade"}
              tone={
                qualityScore === null
                  ? "neutral"
                  : qualityScore >= 80
                    ? "positive"
                    : qualityScore < 55
                      ? "negative"
                      : "neutral"
              }
            />
          </div>
        ) : null}
      </section>

      {fundamental ? (
        <>
          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <WalletCards size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">VALUATION & QUALITY</span>
                  <h2>Market Valuation Snapshot</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-grid-4">
              <div className="qmi-fa-data-card">
                <div className="qmi-fa-data-row">
                  <span>Market Cap</span>
                  <strong>{compactMoney(valuation?.market_cap, marketCurrency)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Enterprise Value</span>
                  <strong>{compactMoney(valuation?.enterprise_value, marketCurrency)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Price / Sales</span>
                  <strong>{ratio(valuation?.price_to_sales)}</strong>
                </div>
              </div>

              <div className="qmi-fa-data-card">
                <div className="qmi-fa-data-row">
                  <span>Trailing P/E</span>
                  <strong>{ratio(valuation?.trailing_pe)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Forward P/E</span>
                  <strong>{ratio(valuation?.forward_pe)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Price / Book</span>
                  <strong>{ratio(valuation?.price_to_book)}</strong>
                </div>
              </div>

              <div className="qmi-fa-data-card">
                <div className="qmi-fa-data-row">
                  <span>EV / Revenue</span>
                  <strong>{ratio(valuation?.enterprise_to_revenue)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>EV / EBITDA</span>
                  <strong>{ratio(valuation?.enterprise_to_ebitda)}</strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Shares Outstanding</span>
                  <strong>{ratio(valuation?.shares_outstanding, 0)}</strong>
                </div>
              </div>

              <div className="qmi-fa-data-card">
                <div className="qmi-fa-data-row">
                  <span>Gross Margin</span>
                  <strong className={`is-${toneFromNumber(profitability?.gross_margin)}`}>
                    {percent(profitability?.gross_margin)}
                  </strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Operating Margin</span>
                  <strong className={`is-${toneFromNumber(profitability?.operating_margin)}`}>
                    {percent(profitability?.operating_margin)}
                  </strong>
                </div>
                <div className="qmi-fa-data-row">
                  <span>Net Margin</span>
                  <strong className={`is-${toneFromNumber(profitability?.net_margin)}`}>
                    {percent(profitability?.net_margin)}
                  </strong>
                </div>
              </div>
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <TrendingUp size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">{data?.engine_version || "DE-FA"} · DERIVED TRENDS</span>
                  <h2>Growth & Financial Trend Intelligence</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-grid-4">
              <Metric
                label="Revenue YoY"
                value={signedPercent(trends?.revenue_yoy)}
                detail="Latest annual change"
                tone={toneFromNumber(trends?.revenue_yoy)}
              />
              <Metric
                label="Revenue CAGR 3Y"
                value={signedPercent(trends?.revenue_cagr_3y)}
                detail="Three-year compound growth"
                tone={toneFromNumber(trends?.revenue_cagr_3y)}
              />
              <Metric
                label="Net Income YoY"
                value={signedPercent(trends?.net_income_yoy)}
                detail="Annual earnings change"
                tone={toneFromNumber(trends?.net_income_yoy)}
              />
              <Metric
                label="FCF YoY"
                value={signedPercent(trends?.free_cash_flow_yoy)}
                detail="Annual free cash-flow change"
                tone={toneFromNumber(trends?.free_cash_flow_yoy)}
              />
              <Metric
                label="Gross Margin TTM"
                value={percent(trends?.gross_margin_ttm)}
                detail="Trailing twelve months"
                tone={toneFromNumber(trends?.gross_margin_ttm)}
              />
              <Metric
                label="Operating Margin TTM"
                value={percent(trends?.operating_margin_ttm)}
                detail="Trailing twelve months"
                tone={toneFromNumber(trends?.operating_margin_ttm)}
              />
              <Metric
                label="Net Margin TTM"
                value={percent(trends?.net_margin_ttm)}
                detail="Trailing twelve months"
                tone={toneFromNumber(trends?.net_margin_ttm)}
              />
              <Metric
                label="FCF Margin TTM"
                value={percent(trends?.free_cash_flow_margin_ttm)}
                detail="Cash-generation efficiency"
                tone={toneFromNumber(trends?.free_cash_flow_margin_ttm)}
              />
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <Gauge size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">DE-FA-002.1 · STATEMENT INTELLIGENCE</span>
                  <h2>Fundamental Statement Intelligence</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-regime">
              <div className={`qmi-fa-regime-main is-${stateTone(statementIntelligence?.fundamental_regime)}`}>
                <span>Fundamental Regime</span>
                <strong style={{
                  color:
                    stateTone(statementIntelligence?.fundamental_regime) === "positive"
                      ? "#4ade80"
                      : stateTone(statementIntelligence?.fundamental_regime) === "negative"
                        ? "#fb7185"
                        : stateTone(statementIntelligence?.fundamental_regime) === "warning"
                          ? "#fbbf24"
                          : "#e2e8f0"
                }}>
                  {prettyState(statementIntelligence?.fundamental_regime)}
                </strong>
                <small>
                  {statementIntelligence?.confidence || "LOW"} confidence ·
                  Fundamental direction from normalized statements
                </small>
              </div>

              <div className="qmi-fa-regime-score">
                <div>
                  <span>Regime Score</span>
                  <strong>
                    {n(statementIntelligence?.regime_score) === null
                      ? "--"
                      : n(statementIntelligence?.regime_score).toFixed(1)}
                  </strong>
                  <small>0–100 statement intelligence</small>
                </div>
              </div>
            </div>

            <div className="qmi-fa-intel-grid">
              <IntelligenceCard
                label="Income Statement"
                block={statementIntelligence?.income_statement}
              />
              <IntelligenceCard
                label="Cash Flow"
                block={statementIntelligence?.cash_flow}
              />
              <IntelligenceCard
                label="Balance Sheet"
                block={statementIntelligence?.balance_sheet}
              />
            </div>

            <div className="qmi-fa-state-matrix">
              {[
                ["Revenue Trend", statementIntelligence?.revenue_trend],
                ["Margin Trend", statementIntelligence?.margin_trend],
                ["Profitability", statementIntelligence?.profitability_state],
                ["Liquidity", statementIntelligence?.liquidity_state],
              ].map(([label, state]) => (
                <div
                  className={`qmi-fa-state-row is-${stateTone(state)}`}
                  key={label}
                >
                  <span>{label}</span>
                  <strong>{prettyState(state)}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <ShieldCheck size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">DE-FA-003.1 · QUALITY INTELLIGENCE</span>
                  <h2>Fundamental Quality Intelligence</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-quality-intel-hero">
              <div className="qmi-fa-quality-intel-main">
                <span>Fundamental Quality Score</span>
                <strong>
                  {n(qualityIntelligence?.quality_score) === null
                    ? "--"
                    : n(qualityIntelligence?.quality_score).toFixed(1)}
                </strong>
                <b>{prettyState(qualityIntelligence?.quality_regime)}</b>
                <small>
                  Composite business, financial and growth quality.
                  Valuation is excluded when FX comparability is limited.
                </small>
              </div>

              <div className="qmi-fa-quality-intel-confidence">
                <div>
                  <span>Quality Confidence</span>
                  <strong>{qualityIntelligence?.confidence || "LOW"}</strong>
                  <small>
                    Valuation state: {prettyState(qualityIntelligence?.valuation_state)}
                  </small>
                </div>
              </div>
            </div>

            <div className="qmi-fa-quality-intel-grid">
              <QualityCard
                label="Business Quality"
                block={qualityIntelligence?.business_quality}
              />
              <QualityCard
                label="Financial Quality"
                block={qualityIntelligence?.financial_quality}
              />
              <QualityCard
                label="Growth Quality"
                block={qualityIntelligence?.growth_quality}
              />
              <QualityCard
                label="Valuation Context"
                block={qualityIntelligence?.valuation_context}
                footer={
                  quality?.currency_mismatch
                    ? `FX limited · ${marketCurrency}/${financialCurrency}`
                    : ""
                }
              />
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <Target size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">DE-FA-004.0 · FUNDAMENTAL DECISION ENGINE</span>
                  <h2>Fundamental Decision</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-decision-hero">
              <div className={`qmi-fa-decision-main is-${decisionTone(decision?.stance)}`}>
                <span>Fundamental Stance</span>
                <strong>{prettyState(decision?.stance)}</strong>
                <b>{decision?.conviction || "LOW"} conviction</b>
                <small>
                  Consolidated posture from quality, statement regime and legacy fundamental score.
                </small>
              </div>

              <div className="qmi-fa-decision-score">
                <div>
                  <span>Decision Score</span>
                  <strong>
                    {n(decision?.decision_score) === null
                      ? "--"
                      : n(decision?.decision_score).toFixed(1)}
                  </strong>
                  <small>0–100 fundamental decision intelligence</small>
                </div>
              </div>
            </div>

            <div className="qmi-fa-decision-breakdown">
              <div>
                <span>Quality Score</span>
                <strong>
                  {n(decision?.quality_score) === null
                    ? "--"
                    : n(decision?.quality_score).toFixed(1)}
                </strong>
              </div>
              <div>
                <span>Regime Score</span>
                <strong>
                  {n(decision?.regime_score) === null
                    ? "--"
                    : n(decision?.regime_score).toFixed(1)}
                </strong>
              </div>
              <div>
                <span>Legacy Score</span>
                <strong>
                  {n(decision?.legacy_score) === null
                    ? "--"
                    : n(decision?.legacy_score).toFixed(1)}
                </strong>
              </div>
            </div>

            <div className="qmi-fa-decision-lists">
              <div className="qmi-fa-decision-list is-thesis">
                <span>Thesis</span>
                {decision?.thesis?.length ? (
                  <ul>
                    {decision.thesis.map((item, index) => (
                      <li key={`decision-thesis-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="qmi-fa-decision-empty">No thesis evidence available.</div>
                )}
              </div>

              <div className="qmi-fa-decision-list is-catalysts">
                <span>Catalysts</span>
                {decision?.catalysts?.length ? (
                  <ul>
                    {decision.catalysts.map((item, index) => (
                      <li key={`decision-catalyst-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="qmi-fa-decision-empty">No catalysts identified.</div>
                )}
              </div>

              <div className="qmi-fa-decision-list is-risks">
                <span>Risks</span>
                {decision?.risks?.length ? (
                  <ul>
                    {decision.risks.map((item, index) => (
                      <li key={`decision-risk-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="qmi-fa-decision-empty">No material risks identified.</div>
                )}
              </div>
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <GitMerge size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">DE-CORE-004.0 · CROSS-ENGINE DECISION FUSION</span>
                  <h2>QMI Integrated Decision</h2>
                </div>
              </div>

              {qmiDecisionLoading ? (
                <div className="qmi-fa-core-status">
                  <RefreshCw className="qmi-fa-spin" size={14} />
                  Fusing Technical + Fundamental
                </div>
              ) : qmiDecisionError ? (
                <div className="qmi-fa-core-status" style={{ color: "#fb7185" }}>
                  <AlertTriangle size={14} />
                  Cross-engine unavailable
                </div>
              ) : (
                <div className="qmi-fa-core-status" style={{ color: "#4ade80" }}>
                  <CheckCircle2 size={14} />
                  Fusion operational
                </div>
              )}
            </div>

            {qmiDecisionError ? (
              <div className="qmi-fa-alert" style={{ marginBottom: 10 }}>
                {qmiDecisionError}
              </div>
            ) : null}

            <div className="qmi-fa-core-hero">
              <div className={`qmi-fa-core-main is-${integratedDecisionTone(qmiDecision?.integrated_posture)}`}>
                <span>Integrated QMI Posture</span>
                <strong>
                  {qmiDecisionLoading && !qmiDecisionResponse
                    ? "CALCULATING"
                    : prettyState(qmiDecision?.integrated_posture)}
                </strong>
                <b>{qmiDecision?.confidence || "LOW"} confidence</b>
                <small>
                  {qmiDecision?.thesis ||
                    "Technical timing and fundamental direction fused under preserved risk gates."}
                </small>
              </div>

              <div className="qmi-fa-core-score">
                <div>
                  <span>Combined Score</span>
                  <strong>
                    {n(qmiDecision?.combined_score) === null
                      ? "--"
                      : n(qmiDecision?.combined_score).toFixed(1)}
                  </strong>
                  <small>0–100 cross-engine decision intelligence</small>
                </div>
              </div>
            </div>

            <div className="qmi-fa-core-grid">
              <div className="qmi-fa-core-card">
                <span>Alignment</span>
                <strong>{prettyState(qmiAlignment?.state)}</strong>
                <small>
                  Score{" "}
                  {n(qmiAlignment?.score) === null
                    ? "--"
                    : n(qmiAlignment?.score).toFixed(1)}
                </small>
              </div>

              <div className="qmi-fa-core-card">
                <span>Timing Gate</span>
                <strong>{prettyState(qmiDecision?.timing_gate)}</strong>
                <small>Technical execution gate preserved</small>
              </div>

              <div className="qmi-fa-core-card">
                <span>Technical Posture</span>
                <strong>{prettyState(qmiTechnical?.posture)}</strong>
                <small>
                  Conviction{" "}
                  {n(qmiTechnical?.conviction) === null
                    ? "--"
                    : n(qmiTechnical?.conviction).toFixed(1)}
                </small>
              </div>

              <div className="qmi-fa-core-card">
                <span>Fundamental Stance</span>
                <strong>{prettyState(qmiFundamental?.stance)}</strong>
                <small>{qmiFundamental?.conviction || "LOW"} conviction</small>
              </div>
            </div>

            <div className="qmi-fa-core-compare">
              <div className="qmi-fa-core-engine">
                <div className="qmi-fa-core-engine-head">
                  <div>
                    <span>Technical Engine · DE-TA-015.0</span>
                    <strong>{prettyState(qmiTechnical?.posture)}</strong>
                  </div>
                  <b>
                    {n(qmiTechnical?.score) === null
                      ? "--"
                      : n(qmiTechnical?.score).toFixed(1)}
                  </b>
                </div>

                <div className="qmi-fa-core-engine-meta">
                  <div>
                    <span>Timing</span>
                    <strong>{prettyState(qmiTechnical?.timing)}</strong>
                  </div>
                  <div>
                    <span>Risk</span>
                    <strong>{prettyState(qmiTechnical?.risk_state)}</strong>
                  </div>
                  <div>
                    <span>Execution</span>
                    <strong>{prettyState(qmiTechnical?.execution_state)}</strong>
                  </div>
                </div>
              </div>

              <div className="qmi-fa-core-engine">
                <div className="qmi-fa-core-engine-head">
                  <div>
                    <span>Fundamental Engine · DE-FA-004.0</span>
                    <strong>{prettyState(qmiFundamental?.stance)}</strong>
                  </div>
                  <b>
                    {n(qmiFundamental?.score) === null
                      ? "--"
                      : n(qmiFundamental?.score).toFixed(1)}
                  </b>
                </div>

                <div className="qmi-fa-core-engine-meta">
                  <div>
                    <span>Quality</span>
                    <strong>
                      {n(qmiFundamental?.quality_score) === null
                        ? "--"
                        : n(qmiFundamental?.quality_score).toFixed(1)}
                    </strong>
                  </div>
                  <div>
                    <span>Regime</span>
                    <strong>
                      {n(qmiFundamental?.regime_score) === null
                        ? "--"
                        : n(qmiFundamental?.regime_score).toFixed(1)}
                    </strong>
                  </div>
                  <div>
                    <span>Legacy</span>
                    <strong>
                      {n(qmiFundamental?.legacy_score) === null
                        ? "--"
                        : n(qmiFundamental?.legacy_score).toFixed(1)}
                    </strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="qmi-fa-core-lists">
              <div className="qmi-fa-core-list is-evidence">
                <span>Supporting Evidence</span>
                {qmiSupportingEvidence.length ? (
                  <ul>
                    {qmiSupportingEvidence.map((item, index) => (
                      <li key={`qmi-evidence-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="qmi-fa-decision-empty">
                    No cross-engine supporting evidence available.
                  </div>
                )}
              </div>

              <div className="qmi-fa-core-list is-conflict">
                <span>Conflicts & Constraints</span>
                {qmiConflicts.length ? (
                  <ul>
                    {qmiConflicts.map((item, index) => (
                      <li key={`qmi-conflict-${index}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="qmi-fa-decision-empty">
                    No material cross-engine conflicts detected.
                  </div>
                )}
              </div>
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <Building2 size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">FINANCIAL HEALTH</span>
                  <h2>Liquidity, Leverage & Cash Flow</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-grid-4">
              <Metric
                label="Total Revenue"
                value={compactMoney(health?.total_revenue, financialCurrency)}
                detail="Current provider snapshot"
              />
              <Metric
                label="EBITDA"
                value={compactMoney(health?.ebitda, financialCurrency)}
                detail="Operating earnings proxy"
                tone={toneFromNumber(health?.ebitda)}
              />
              <Metric
                label="Free Cash Flow"
                value={compactMoney(health?.free_cash_flow, financialCurrency)}
                detail="Current FCF snapshot"
                tone={toneFromNumber(health?.free_cash_flow)}
              />
              <Metric
                label="Net Cash"
                value={compactMoney(trends?.net_cash, financialCurrency)}
                detail="Cash minus total debt"
                tone={toneFromNumber(trends?.net_cash)}
              />
              <Metric
                label="Total Cash"
                value={compactMoney(health?.total_cash, financialCurrency)}
                detail="Cash and equivalents"
              />
              <Metric
                label="Total Debt"
                value={compactMoney(health?.total_debt, financialCurrency)}
                detail="Provider debt snapshot"
              />
              <Metric
                label="Current Ratio"
                value={ratio(health?.current_ratio)}
                detail="Short-term liquidity"
                tone={
                  n(health?.current_ratio) === null
                    ? "neutral"
                    : n(health?.current_ratio) >= 1
                      ? "positive"
                      : "negative"
                }
              />
              <Metric
                label="Debt / Cash"
                value={ratio(trends?.debt_to_cash)}
                detail="Balance-sheet leverage context"
                tone={
                  n(trends?.debt_to_cash) === null
                    ? "neutral"
                    : n(trends?.debt_to_cash) <= 1
                      ? "positive"
                      : "negative"
                }
              />
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <Database size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">DATA QUALITY ENGINE</span>
                  <h2>Financial Statement Coverage</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-quality">
              <div className="qmi-fa-quality-score">
                <div>
                  <span>Completeness Score</span>
                  <strong>
                    {qualityScore === null ? "--" : qualityScore.toFixed(1)}
                  </strong>
                  <small>{quality?.completeness_grade || "Unknown"}</small>
                </div>
              </div>

              <div>
                <div className="qmi-fa-coverage-grid">
                  {statementCoverage.map((item) => (
                    <div className="qmi-fa-coverage-card" key={item.label}>
                      <span>{item.label}</span>
                      <strong>{item.value}</strong>
                    </div>
                  ))}
                </div>

                <div className="qmi-fa-flags">
                  <div className={`qmi-fa-flag ${quality?.has_ttm_income ? "" : "is-off"}`}>
                    TTM Income {quality?.has_ttm_income ? "✓" : "—"}
                  </div>
                  <div className={`qmi-fa-flag ${quality?.has_ttm_cash_flow ? "" : "is-off"}`}>
                    TTM Cash Flow {quality?.has_ttm_cash_flow ? "✓" : "—"}
                  </div>
                  <div className={`qmi-fa-flag ${quality?.has_latest_balance_sheet ? "" : "is-off"}`}>
                    Latest Balance {quality?.has_latest_balance_sheet ? "✓" : "—"}
                  </div>
                  <div className="qmi-fa-flag">
                    Snapshot {quality?.snapshot_fields_available ?? 0}/
                    {quality?.snapshot_fields_total ?? 0}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="qmi-fa-panel qmi-fa-section">
            <div className="qmi-fa-section-head">
              <div className="qmi-fa-section-title">
                <div className="qmi-fa-icon-box">
                  <Gauge size={17} />
                </div>
                <div>
                  <span className="qmi-fa-kicker">QMI INTERPRETATION</span>
                  <h2>Strengths, Weaknesses & Warnings</h2>
                </div>
              </div>
            </div>

            <div className="qmi-fa-lists">
              <ListPanel
                title="Strengths"
                icon={CheckCircle2}
                items={fundamental?.strengths || []}
                tone="positive"
                empty="No material strengths detected."
              />
              <ListPanel
                title="Weaknesses"
                icon={TrendingDown}
                items={fundamental?.weaknesses || []}
                tone="negative"
                empty="No material weaknesses detected."
              />
              <ListPanel
                title="Warnings"
                icon={AlertTriangle}
                items={[
                  ...(fundamental?.warnings || []),
                  ...(quality?.warnings || []),
                ]}
                tone="warning"
                empty="No dataset or fundamental warnings."
              />
            </div>

            <div className="qmi-fa-footer">
              <span>
                Provider: {data?.data_source || quality?.provider || "yfinance"}
              </span>
              <span>
                Currency: {marketCurrency} market · {financialCurrency} financial
                {quality?.currency_mismatch ? " · FX separation active" : ""}
              </span>
              <span>
                Engine: {data?.engine_version || "--"}
              </span>
              <span>
                Generated:{" "}
                {data?.generated_at
                  ? new Date(data.generated_at).toLocaleString()
                  : "--"}
              </span>
            </div>
          </section>
        </>
      ) : null}
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  ArrowDownRight,
  ArrowUpRight,
  Gauge,
  RefreshCw,
  Search,
  ShieldAlert,
  Waves,
  GitBranch,
  Layers3,
  ShieldCheck
} from "lucide-react";

import {
  getMarketStructure,
  getSupportResistance,
  getTechnicalAnalysis,
  getTechnicalMarketHistory,
  getLiquidity,
  getTechnicalConfluence,
  getTechnicalDecision
} from "../services/technicalService";

import InstitutionalChart from "../components/technical/InstitutionalChart";

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, Number(value || 0)));
}

function formatScore(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }

  const number = Number(value);
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(digits)}`;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }

  return Number(value).toFixed(digits);
}

function formatPercent(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }

  return `${Number(value).toFixed(digits)}%`;
}

function pretty(value) {
  if (!value) {
    return "--";
  }

  return String(value)
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function DirectionBar({ value }) {
  const score = clamp(value, -100, 100);
  const marker = ((score + 100) / 200) * 100;

  return (
    <div className="qmi-ta-direction">
      <div className="qmi-ta-direction-labels">
        <span>-100 Bearish</span>
        <span>0</span>
        <span>+100 Bullish</span>
      </div>

      <div className="qmi-ta-direction-track">
        <div
          className="qmi-ta-direction-marker"
          style={{ left: `${marker}%` }}
        />
      </div>
    </div>
  );
}

function LevelBar({ value }) {
  const score = clamp(value, 0, 100);

  return (
    <div className="qmi-ta-level-track">
      <div
        className="qmi-ta-level-fill"
        style={{ width: `${score}%` }}
      />
    </div>
  );
}

function EngineCard({
  title,
  icon: Icon,
  score,
  state,
  confidence,
  directional = false,
  children
}) {
  return (
    <section className="qmi-ta-engine-card">
      <div className="qmi-ta-card-head">
        <div className="qmi-ta-engine-title">
          <div className="qmi-ta-icon-box">
            <Icon size={18} strokeWidth={1.8} />
          </div>

          <div>
            <span className="qmi-ta-kicker">ENGINE</span>
            <h3>{title}</h3>
          </div>
        </div>

        <div className="qmi-ta-card-score">
          {directional ? formatScore(score) : formatNumber(score, 1)}
        </div>
      </div>

      <div className="qmi-ta-engine-state">{pretty(state)}</div>

      {directional ? (
        <DirectionBar value={score} />
      ) : (
        <LevelBar value={score} />
      )}

      {confidence !== undefined && confidence !== null && (
        <div className="qmi-ta-confidence-row">
          <span>Confidence</span>
          <strong>{formatPercent(confidence)}</strong>
        </div>
      )}

      {children}
    </section>
  );
}

function Metric({ label, value, strong = false }) {
  return (
    <div className="qmi-ta-metric">
      <span>{label}</span>
      <strong className={strong ? "qmi-ta-metric-strong" : ""}>
        {value}
      </strong>
    </div>
  );
}

function ConfluenceContribution({ item }) {
  const score = Number(item?.normalized_contribution || 0);
  const magnitude = Math.min(100, Math.abs(score) * 3.2);
  const tone =
    score > 0.01
      ? "is-positive"
      : score < -0.01
        ? "is-negative"
        : "is-neutral";

  return (
    <div className={`qmi-confluence__engine ${tone}`}>
      <div className="qmi-confluence__engine-head">
        <div>
          <span>{pretty(item?.engine)}</span>
          <small>
            {pretty(item?.vote)} · weight{" "}
            {formatPercent(item?.effective_weight_pct)}
          </small>
        </div>

        <strong>{formatScore(score, 2)}</strong>
      </div>

      <div className="qmi-confluence__engine-track">
        <div className="qmi-confluence__engine-center" />
        <div
          className="qmi-confluence__engine-fill"
          style={{
            width: `${magnitude / 2}%`,
            left: score >= 0 ? "50%" : `${50 - magnitude / 2}%`
          }}
        />
      </div>

      <div className="qmi-confluence__engine-foot">
        <span>Engine score {formatScore(item?.score)}</span>
        <span>Confidence {formatPercent(item?.confidence)}</span>
      </div>
    </div>
  );
}

export default function Technical({ token = "" }) {
  const [symbol, setSymbol] = useState("NIO");
  const [submittedSymbol, setSubmittedSymbol] = useState("NIO");
  const [period, setPeriod] = useState("1y");
  const [interval, setInterval] = useState("1d");
  const [technical, setTechnical] = useState(null);
  const [marketStructure, setMarketStructure] = useState(null);
  const [supportResistance, setSupportResistance] = useState(null);
  const [chartHistory, setChartHistory] = useState([]);
  const [liquidity, setLiquidity] = useState(null);
  const [confluence, setConfluence] = useState(null);
  const [technicalDecision, setTechnicalDecision] = useState(null);
  const [loading, setLoading] = useState(true);
  const [structureLoading, setStructureLoading] = useState(true);
  const [zonesLoading, setZonesLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [liquidityLoading, setLiquidityLoading] = useState(true);
  const [confluenceLoading, setConfluenceLoading] = useState(true);
  const [decisionLoading, setDecisionLoading] = useState(true);
  const [error, setError] = useState("");
  const [structureError, setStructureError] = useState("");
  const [zonesError, setZonesError] = useState("");
  const [chartError, setChartError] = useState("");
  const [liquidityError, setLiquidityError] = useState("");
  const [confluenceError, setConfluenceError] = useState("");
  const [decisionError, setDecisionError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError("");

      try {
        const result = await getTechnicalAnalysis(submittedSymbol, {
          period,
          interval,
          token,
          signal: controller.signal
        });

        setTechnical(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load technical analysis:", requestError);
          setTechnical(null);
          setError(
            requestError?.message ||
              "Unable to load technical analysis from QMI backend"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadStructure() {
      setStructureLoading(true);
      setStructureError("");

      try {
        const result = await getMarketStructure(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          maxSwings: 20,
          token,
          signal: controller.signal
        });

        setMarketStructure(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load market structure:", requestError);
          setMarketStructure(null);
          setStructureError(
            requestError?.message ||
              "Unable to load market structure from QMI backend"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setStructureLoading(false);
        }
      }
    }

    loadStructure();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadZones() {
      setZonesLoading(true);
      setZonesError("");

      try {
        const result = await getSupportResistance(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          minTouches: 2,
          maxZones: 6,
          token,
          signal: controller.signal
        });

        setSupportResistance(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error(
            "Unable to load support/resistance zones:",
            requestError
          );
          setSupportResistance(null);
          setZonesError(
            requestError?.message ||
              "Unable to load support/resistance zones"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setZonesLoading(false);
        }
      }
    }

    loadZones();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadChartHistory() {
      setChartLoading(true);
      setChartError("");

      try {
        const result = await getTechnicalMarketHistory(
          submittedSymbol,
          {
            period,
            interval,
            token,
            signal: controller.signal
          }
        );

        setChartHistory(
          Array.isArray(result)
            ? result
            : Array.isArray(result?.history)
              ? result.history
              : []
        );
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error(
            "Unable to load institutional chart history:",
            requestError
          );
          setChartHistory([]);
          setChartError(
            requestError?.message ||
              "Unable to load OHLC chart history"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setChartLoading(false);
        }
      }
    }

    loadChartHistory();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadLiquidity() {
      setLiquidityLoading(true);
      setLiquidityError("");

      try {
        const result = await getLiquidity(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          tolerancePct: 0.6,
          minTouches: 2,
          maxPools: 8,
          token,
          signal: controller.signal
        });

        setLiquidity(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load liquidity engine:", requestError);
          setLiquidity(null);
          setLiquidityError(
            requestError?.message ||
              "Unable to load liquidity analysis from QMI backend"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLiquidityLoading(false);
        }
      }
    }

    loadLiquidity();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadConfluence() {
      setConfluenceLoading(true);
      setConfluenceError("");

      try {
        const result = await getTechnicalConfluence(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          token,
          signal: controller.signal
        });

        setConfluence(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error(
            "Unable to load technical confluence:",
            requestError
          );
          setConfluence(null);
          setConfluenceError(
            requestError?.message ||
              "Unable to load Technical Confluence Engine"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setConfluenceLoading(false);
        }
      }
    }

    loadConfluence();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);


  useEffect(() => {
    const controller = new AbortController();

    async function loadTechnicalDecision() {
      setDecisionLoading(true);
      setDecisionError("");

      try {
        const result = await getTechnicalDecision(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          token,
          signal: controller.signal
        });

        setTechnicalDecision(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load technical decision:", requestError);
          setTechnicalDecision(null);
          setDecisionError(
            requestError?.message ||
              "Unable to load QMI Technical Decision Layer"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setDecisionLoading(false);
        }
      }
    }

    loadTechnicalDecision();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  const scoring = technical?.scoring || {};
  const trend = scoring?.trend || {};
  const strength = scoring?.strength || {};
  const regime = scoring?.regime || {};
  const momentum = scoring?.momentum || {};
  const volatility = scoring?.volatility_engine || {};
  const volume = scoring?.volume || {};

  const structureTrend = marketStructure?.trend || {};
  const latestStructure = marketStructure?.latest_structure || {};
  const structureSwings = Array.isArray(marketStructure?.swings)
    ? marketStructure.swings
    : [];
  const latestStructureEvent = marketStructure?.latest_event || null;
  const structureEvents = Array.isArray(marketStructure?.events)
    ? marketStructure.events
    : [];
  const structuralState = marketStructure?.structural_state || "NEUTRAL";
  const protectedLevels = marketStructure?.protected_levels || {};
  const protectedHigh = protectedLevels?.protected_high || null;
  const protectedLow = protectedLevels?.protected_low || null;
  const lastBos = marketStructure?.last_bos || null;
  const lastChoch = marketStructure?.last_choch || null;
  const structureValidation = marketStructure?.validation || {};
  const validationComponents = structureValidation?.components || {};
  const validationDiagnostics = structureValidation?.diagnostics || {};
  const validationWarnings = Array.isArray(structureValidation?.warnings)
    ? structureValidation.warnings
    : [];

  const zoneSummary = supportResistance?.summary || {};
  const nearestSupport = zoneSummary?.nearest_support || null;
  const nearestResistance = zoneSummary?.nearest_resistance || null;
  const activeZone = zoneSummary?.active_zone || null;
  const structuralZones = Array.isArray(supportResistance?.zones)
    ? supportResistance.zones
    : [];

  const technicalConfluence = confluence?.technical_confluence || {};
  const confluenceDiagnostics = technicalConfluence?.diagnostics || {};
  const confluenceContributions = Array.isArray(
    confluenceDiagnostics?.engine_contributions
  )
    ? confluenceDiagnostics.engine_contributions
    : [];
  const confluenceConflicts = Array.isArray(technicalConfluence?.conflicts)
    ? technicalConfluence.conflicts
    : [];


  const decisionCore = technicalDecision?.technical_decision || {};
  const decisionPosture = decisionCore?.posture || {};
  const decisionReadiness = decisionCore?.readiness || {};
  const exposureContext = decisionCore?.exposure_context || {};
  const decisionRisk = decisionCore?.risk || decisionCore?.risk_context || {};
  const decisionBlockers = Array.isArray(decisionCore?.blockers)
    ? decisionCore.blockers
    : Array.isArray(decisionReadiness?.blockers)
      ? decisionReadiness.blockers
      : [];
  const reversalRequirements = Array.isArray(decisionCore?.reversal_requirements)
    ? decisionCore.reversal_requirements
    : Array.isArray(decisionCore?.requirements)
      ? decisionCore.requirements
      : [];
  const riskFlags = Array.isArray(decisionCore?.risk_flags)
    ? decisionCore.risk_flags
    : Array.isArray(decisionRisk?.flags)
      ? decisionRisk.flags
      : [];

  const decisionScore = Number(
    decisionCore?.direction_score ??
      technicalDecision?.direction_score ??
      0
  );

  const decisionTone =
    decisionScore >= 25
      ? "positive"
      : decisionScore <= -25
        ? "negative"
        : "neutral";

  const confluenceTone =
    Number(technicalConfluence?.direction_score || 0) >= 25
      ? "positive"
      : Number(technicalConfluence?.direction_score || 0) <= -25
        ? "negative"
        : "neutral";

  const structureTone =
    structureTrend.state === "BULLISH"
      ? "positive"
      : structureTrend.state === "BEARISH"
        ? "negative"
        : "neutral";

  const marketContext = useMemo(() => {
    if (!technical) {
      return [];
    }

    return [
      {
        label: "Last Price",
        value:
          technical.last_price === null || technical.last_price === undefined
            ? "--"
            : `$${formatNumber(technical.last_price, 2)}`
      },
      {
        label: "Observations",
        value: technical.observations ?? "--"
      },
      {
        label: "Regime Confidence",
        value: formatPercent(regime.confidence)
      },
      {
        label: "Data Quality",
        value: formatPercent(
          Math.min(
            Number(trend.data_quality ?? 100),
            Number(strength.data_quality ?? 100),
            Number(momentum.data_quality ?? 100),
            Number(volatility.data_quality ?? 100),
            Number(volume.data_quality ?? 100)
          )
        )
      }
    ];
  }, [technical, trend, strength, regime, momentum, volatility, volume]);

  function submit(event) {
    event.preventDefault();

    const normalized = symbol.trim().toUpperCase();

    if (!normalized) {
      return;
    }

    setSymbol(normalized);
    setSubmittedSymbol(normalized);
  }

  return (
    <div className="qmi-ta-page">
      <style>{`
        .qmi-ta-page {
          display: grid;
          gap: 20px;
        }

        .qmi-ta-toolbar,
        .qmi-ta-regime-panel,
        .qmi-ta-engine-card,
        .qmi-ta-detail-panel {
          background: var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 12px 32px rgba(2, 6, 23, 0.08);
        }

        .qmi-ta-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 16px;
          flex-wrap: wrap;
        }

        .qmi-ta-search {
          display: flex;
          gap: 10px;
          align-items: center;
          flex: 1 1 420px;
        }

        .qmi-ta-search-box {
          position: relative;
          flex: 1;
          min-width: 180px;
        }

        .qmi-ta-search-box svg {
          position: absolute;
          left: 13px;
          top: 50%;
          transform: translateY(-50%);
          opacity: 0.55;
        }

        .qmi-ta-search-box input,
        .qmi-ta-toolbar select {
          width: 100%;
          min-height: 42px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.2));
          border-radius: 10px;
          background: var(--surface, rgba(15, 23, 42, 0.55));
          color: inherit;
          padding: 0 12px;
          outline: none;
        }

        .qmi-ta-search-box input {
          padding-left: 40px;
          font-weight: 900;
          font-size: 16px;
          letter-spacing: 0.04em;
        }

        .qmi-ta-toolbar-selects {
          display: flex;
          gap: 10px;
        }

        .qmi-ta-toolbar button {
          min-height: 42px;
          border: 0;
          border-radius: 10px;
          padding: 0 16px;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-weight: 900;
          font-size: 14px;
          cursor: pointer;
          background: #2563eb;
          color: #fff;
        }

        .qmi-ta-toolbar button:disabled {
          cursor: default;
          opacity: 0.6;
        }

        .qmi-ta-regime-panel {
          padding: 22px;
          display: grid;
          grid-template-columns: minmax(260px, 1fr) 2fr;
          gap: 24px;
        }

        .qmi-ta-regime-name {
          font-size: clamp(34px, 4.6vw, 56px);
          margin: 6px 0 6px;
          font-weight: 900;
          letter-spacing: -0.04em;
        }

        .qmi-ta-kicker {
          font-size: 12px;
          letter-spacing: 0.16em;
          font-weight: 900;
          opacity: 0.55;
        }

        .qmi-ta-regime-sub {
          opacity: 0.66;
          font-size: 13px;
        }

        .qmi-ta-context-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(110px, 1fr));
          gap: 10px;
          align-content: center;
        }

        .qmi-ta-context {
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          background: rgba(148, 163, 184, 0.04);
          border-radius: 12px;
          padding: 14px;
        }

        .qmi-ta-context span,
        .qmi-ta-metric span,
        .qmi-ta-confidence-row span {
          display: block;
          font-size: 12px;
          opacity: 0.66;
          margin-bottom: 6px;
        }

        .qmi-ta-context strong {
          font-size: 22px;
          font-weight: 900;
        }

        .qmi-ta-engine-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 14px;
        }

        .qmi-ta-engine-card {
          padding: 20px;
          min-width: 0;
        }

        .qmi-ta-card-head {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 10px;
        }

        .qmi-ta-engine-title {
          display: flex;
          align-items: center;
          gap: 10px;
          min-width: 0;
        }

        .qmi-ta-engine-title h3 {
          margin: 2px 0 0;
          font-size: 18px;
        }

        .qmi-ta-icon-box {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: grid;
          place-items: center;
          background: rgba(37, 99, 235, 0.12);
        }

        .qmi-ta-card-score {
          font-size: 34px;
          font-weight: 900;
          letter-spacing: -0.04em;
        }
        .qmi-ta-engine-card:nth-child(1) .qmi-ta-card-score,
        .qmi-ta-engine-card:nth-child(1) .qmi-ta-engine-state {
          color: #ff5a52;
        }

        .qmi-ta-engine-card:nth-child(2) .qmi-ta-card-score,
        .qmi-ta-engine-card:nth-child(2) .qmi-ta-engine-state {
          color: #f4c542;
        }

        .qmi-ta-engine-card:nth-child(3) .qmi-ta-card-score {
          color: #5ee35a;
        }

        .qmi-ta-engine-card:nth-child(4) .qmi-ta-card-score,
        .qmi-ta-engine-card:nth-child(4) .qmi-ta-engine-state {
          color: #4ea1ff;
        }

        .qmi-ta-engine-card:nth-child(5) .qmi-ta-card-score,
        .qmi-ta-engine-card:nth-child(5) .qmi-ta-engine-state {
          color: #5ee35a;
        }


        .qmi-ta-engine-state {
          margin: 16px 0 10px;
          font-size: 15px;
          font-weight: 900;
          min-height: 22px;
        }

        .qmi-ta-direction-labels {
          display: flex;
          justify-content: space-between;
          font-size: 10px;
          opacity: 0.45;
          margin-bottom: 5px;
        }

        .qmi-ta-direction-track,
        .qmi-ta-level-track {
          position: relative;
          height: 7px;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.16);
          overflow: visible;
        }

        .qmi-ta-direction-track::after {
          content: "";
          position: absolute;
          left: 50%;
          top: -2px;
          bottom: -2px;
          width: 1px;
          background: rgba(148, 163, 184, 0.55);
        }

        .qmi-ta-direction-marker {
          position: absolute;
          top: 50%;
          width: 12px;
          height: 12px;
          border-radius: 50%;
          transform: translate(-50%, -50%);
          background: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.16);
          z-index: 2;
        }

        .qmi-ta-level-track {
          overflow: hidden;
        }

        .qmi-ta-level-fill {
          height: 100%;
          border-radius: inherit;
          background: #2563eb;
        }

        .qmi-ta-confidence-row {
          margin-top: 14px;
          display: flex;
          justify-content: space-between;
          align-items: end;
        }

        .qmi-ta-confidence-row span {
          margin: 0;
        }

        .qmi-ta-metrics {
          display: grid;
          gap: 12px;
          margin-top: 18px;
        }

        .qmi-ta-metric {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          font-size: 12px;
        }

        .qmi-ta-metric span {
          margin: 0;
        }

        .qmi-ta-metric strong {
          font-size: 13px;
          text-align: right;
        }

        .qmi-ta-metric-strong {
          font-weight: 900;
        }

        .qmi-ta-detail-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
        }

        .qmi-ta-detail-panel {
          padding: 20px;
        }

        .qmi-ta-detail-panel h3 {
          font-size: 17px;
          margin: 0 0 16px;
        }

        .qmi-ta-detail-list {
          display: grid;
          gap: 10px;
        }

        .qmi-ta-chart-panel {
          padding: 18px 18px 14px;
          background: #0a101a;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 18px 44px rgba(0, 0, 0, 0.16);
          overflow: hidden;
        }

        .qmi-ta-chart-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 12px;
        }

        .qmi-ta-chart-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .qmi-ta-chart-title h2 {
          margin: 3px 0 0;
          font-size: 22px;
          font-weight: 900;
          letter-spacing: -0.025em;
        }

        .qmi-ichart {
          min-width: 0;
        }

        .qmi-ichart__header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: 9px 12px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-bottom: 0;
          background: #080d15;
          border-radius: 10px 10px 0 0;
        }

        .qmi-ichart__header > div:first-child span {
          display: block;
          color: #7c8aa0;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.11em;
        }

        .qmi-ichart__header > div:first-child strong {
          display: block;
          margin-top: 3px;
          font-size: 11px;
        }

        .qmi-ichart__right {
          display: flex;
          align-items: flex-end;
          flex-direction: column;
          gap: 8px;
        }

        .qmi-ichart__ohlc {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          color: #9aa7b9;
          font-family: var(--font-family-mono, monospace);
          font-size: 10px;
          font-weight: 700;
        }

        .qmi-ichart__controls {
          display: flex;
          flex-wrap: wrap;
          justify-content: flex-end;
          gap: 7px;
        }

        .qmi-ichart__range,
        .qmi-ichart__layers {
          display: flex;
          gap: 4px;
        }

        .qmi-ichart__controls button {
          min-height: 25px;
          padding: 4px 8px;
          color: #667489;
          background: rgba(148, 163, 184, 0.03);
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-radius: 6px;
          font-size: 9px;
          font-weight: 800;
          cursor: pointer;
        }

        .qmi-ichart__controls button:hover {
          color: #c9d4e4;
          background: rgba(148, 163, 184, 0.06);
        }

        .qmi-ichart__controls button.is-active {
          color: #dfe8f7;
          background: rgba(78, 161, 255, 0.10);
          border-color: rgba(78, 161, 255, 0.22);
        }

        .qmi-ichart__viewport {
          border: 1px solid rgba(148, 163, 184, 0.10);
          background: #070c13;
          overflow: hidden;
        }

        .qmi-ichart__viewport svg {
          display: block;
          width: 100%;
          min-width: 920px;
          height: auto;
        }

        .qmi-ichart__background {
          fill: #070c13;
        }

        .qmi-ichart__grid {
          stroke: rgba(148, 163, 184, 0.075);
          stroke-width: 1;
        }

        .qmi-ichart__axis-label,
        .qmi-ichart__date-label {
          fill: #677386;
          font-family: var(--font-family-mono, monospace);
          font-size: 10px;
        }

        .qmi-ichart__candle.is-up {
          color: #31d890;
        }

        .qmi-ichart__candle.is-down {
          color: #ff6178;
        }

        .qmi-ichart__wick {
          stroke: currentColor;
          stroke-width: 1.15;
          opacity: 0.92;
        }

        .qmi-ichart__body {
          fill: currentColor;
        }

        .qmi-ichart__zone.is-support {
          fill: rgba(49, 216, 144, 0.07);
          stroke: rgba(49, 216, 144, 0.18);
        }

        .qmi-ichart__zone.is-resistance {
          fill: rgba(255, 97, 120, 0.07);
          stroke: rgba(255, 97, 120, 0.18);
        }

        .qmi-ichart__zone-label {
          font-size: 9px;
          font-weight: 900;
          letter-spacing: 0.05em;
        }

        .qmi-ichart__zone-label.is-support {
          fill: rgba(49, 216, 144, 0.75);
        }

        .qmi-ichart__zone-label.is-resistance {
          fill: rgba(255, 97, 120, 0.78);
        }

        .qmi-ichart__swing-dot.is-high {
          fill: #4ea1ff;
        }

        .qmi-ichart__swing-dot.is-low {
          fill: #f4c542;
        }

        .qmi-ichart__swing-label {
          font-size: 9px;
          font-weight: 950;
        }

        .qmi-ichart__swing-label.is-high {
          fill: #63adff;
        }

        .qmi-ichart__swing-label.is-low {
          fill: #ffd45c;
        }

        .qmi-ichart__event-line {
          stroke-width: 1.4;
          stroke-dasharray: 4 3;
        }

        .qmi-ichart__event-line.is-bullish {
          stroke: rgba(49, 216, 144, 0.82);
        }

        .qmi-ichart__event-line.is-bearish {
          stroke: rgba(255, 97, 120, 0.82);
        }

        .qmi-ichart__event-label {
          font-size: 9px;
          font-weight: 950;
        }

        .qmi-ichart__event-label.is-bullish {
          fill: #31d890;
        }

        .qmi-ichart__event-label.is-bearish {
          fill: #ff6178;
        }

        .qmi-ichart__event-line.is-latest {
          stroke-width: 2.2;
          stroke-dasharray: 6 3;
        }

        .qmi-ichart__event-label.is-latest {
          font-size: 10px;
          font-weight: 1000;
        }

        .qmi-ichart__latest-event {
          display: grid;
          grid-template-columns: auto auto 1fr;
          align-items: center;
          gap: 8px;
          margin-top: 10px;
          padding: 8px 10px;
          border-radius: 8px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          background: rgba(148, 163, 184, 0.025);
          font-size: 9px;
        }

        .qmi-ichart__latest-event span {
          color: #738096;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .qmi-ichart__latest-event strong {
          font-size: 10px;
          font-weight: 950;
        }

        .qmi-ichart__latest-event small {
          color: #748196;
        }

        .qmi-ichart__latest-event.is-bullish strong {
          color: #31d890;
        }

        .qmi-ichart__latest-event.is-bearish strong {
          color: #ff6178;
        }

        .qmi-ichart__protected {
          stroke-width: 1.2;
          stroke-dasharray: 8 5;
        }

        .qmi-ichart__protected.is-high {
          stroke: rgba(78, 161, 255, 0.72);
        }

        .qmi-ichart__protected.is-low {
          stroke: rgba(244, 197, 66, 0.72);
        }

        .qmi-ichart__protected-label {
          font-size: 9px;
          font-weight: 950;
        }

        .qmi-ichart__protected-label.is-high {
          fill: #4ea1ff;
        }

        .qmi-ichart__protected-label.is-low {
          fill: #f4c542;
        }

        .qmi-ichart__last-price {
          stroke: rgba(255, 255, 255, 0.32);
          stroke-width: 1;
          stroke-dasharray: 2 3;
        }

        .qmi-ichart__last-price-label {
          fill: #f8fafc;
          font-family: var(--font-family-mono, monospace);
          font-size: 10px;
          font-weight: 900;
        }

        .qmi-ichart__legend {
          display: flex;
          flex-wrap: wrap;
          gap: 14px;
          padding: 10px 12px 0;
          color: #748196;
          font-size: 9px;
          font-weight: 700;
        }

        .qmi-ichart__legend span {
          display: inline-flex;
          align-items: center;
          gap: 5px;
        }

        .qmi-ichart__legend i {
          width: 8px;
          height: 8px;
          border-radius: 2px;
        }

        .qmi-ichart__legend i.is-support {
          background: #31d890;
        }

        .qmi-ichart__legend i.is-resistance {
          background: #ff6178;
        }

        .qmi-ichart__legend i.is-protected {
          background: #4ea1ff;
        }

        .qmi-ichart-empty {
          padding: 60px 20px;
          text-align: center;
          color: #718096;
          font-size: 12px;
        }

        .qmi-ta-zones-panel {
          padding: 22px;
          background: var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 12px 32px rgba(2, 6, 23, 0.08);
        }

        .qmi-ta-zones-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 16px;
        }

        .qmi-ta-zones-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .qmi-ta-zones-title h2 {
          margin: 3px 0 0;
          font-size: 22px;
          font-weight: 900;
          letter-spacing: -0.025em;
        }

        .qmi-ta-zone-summary {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-ta-zone-summary > div,
        .qmi-ta-zone-card {
          min-width: 0;
          padding: 14px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-ta-zone-summary span,
        .qmi-ta-zone-card span {
          display: block;
          margin-bottom: 7px;
          font-size: 10px;
          font-weight: 800;
          opacity: 0.58;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .qmi-ta-zone-summary strong {
          display: block;
          font-size: 18px;
          font-weight: 900;
        }

        .qmi-ta-zones-strip {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
          margin-top: 14px;
        }

        .qmi-ta-zone-card {
          position: relative;
          overflow: hidden;
        }

        .qmi-ta-zone-card::before {
          position: absolute;
          top: 0;
          bottom: 0;
          left: 0;
          width: 3px;
          content: "";
        }

        .qmi-ta-zone-card.is-support::before {
          background: #34d399;
        }

        .qmi-ta-zone-card.is-resistance::before {
          background: #fb7185;
        }

        .qmi-ta-zone-card strong {
          display: block;
          font-size: 16px;
          font-weight: 900;
        }

        .qmi-ta-zone-card small {
          display: block;
          margin-top: 6px;
          font-size: 10px;
          opacity: 0.58;
          line-height: 1.45;
        }

        .qmi-ta-zone-strength {
          margin-top: 9px;
          height: 4px;
          overflow: hidden;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.12);
        }

        .qmi-ta-zone-strength > div {
          height: 100%;
          background: currentColor;
          border-radius: inherit;
        }

        .qmi-ta-zone-card.is-support {
          color: #34d399;
        }

        .qmi-ta-zone-card.is-resistance {
          color: #fb7185;
        }

        .qmi-ta-zone-card.is-support small,
        .qmi-ta-zone-card.is-resistance small {
          color: var(--text, #f8fafc);
        }

        .qmi-ta-structure-panel {
          padding: 22px;
          background: var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 12px 32px rgba(2, 6, 23, 0.08);
        }

        .qmi-ta-structure-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          margin-bottom: 18px;
        }

        .qmi-ta-structure-title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .qmi-ta-structure-title h2 {
          margin: 3px 0 0;
          font-size: 22px;
          font-weight: 900;
          letter-spacing: -0.025em;
        }

        .qmi-ta-structure-badge {
          min-width: 112px;
          padding: 9px 12px;
          border-radius: 10px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(148, 163, 184, 0.05);
          text-align: center;
          font-size: 14px;
          font-weight: 900;
        }

        .qmi-ta-structure-badge.is-positive {
          color: #5ee35a;
          border-color: rgba(94, 227, 90, 0.24);
          background: rgba(94, 227, 90, 0.07);
        }

        .qmi-ta-structure-badge.is-negative {
          color: #ff5a52;
          border-color: rgba(255, 90, 82, 0.24);
          background: rgba(255, 90, 82, 0.07);
        }

        .qmi-ta-structure-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-ta-structure-metric {
          padding: 14px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          border-radius: 12px;
          background: rgba(148, 163, 184, 0.035);
          min-width: 0;
        }

        .qmi-ta-structure-metric span {
          display: block;
          margin-bottom: 7px;
          font-size: 11px;
          opacity: 0.6;
        }

        .qmi-ta-structure-metric strong {
          display: block;
          overflow: hidden;
          font-size: 20px;
          font-weight: 900;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .qmi-ta-structure-reason {
          margin-top: 14px;
          padding: 12px 14px;
          border-left: 3px solid #2563eb;
          border-radius: 8px;
          background: rgba(37, 99, 235, 0.055);
          font-size: 13px;
          line-height: 1.55;
          opacity: 0.85;
        }

        .qmi-ta-swing-strip {
          display: flex;
          gap: 8px;
          margin-top: 16px;
          padding-top: 14px;
          overflow-x: auto;
          border-top: 1px solid var(--border, rgba(148, 163, 184, 0.12));
        }

        .qmi-ta-swing-chip {
          flex: 0 0 auto;
          min-width: 86px;
          padding: 8px 10px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.14));
          border-radius: 9px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-ta-swing-chip strong {
          display: block;
          font-size: 15px;
          font-weight: 900;
        }

        .qmi-ta-swing-chip span {
          display: block;
          margin-top: 3px;
          font-size: 10px;
          opacity: 0.58;
        }

        .qmi-ta-swing-chip.is-high strong {
          color: #4ea1ff;
        }

        .qmi-ta-swing-chip.is-low strong {
          color: #f4c542;
        }

        .qmi-ta-validation {
          display: grid;
          grid-template-columns: 1.3fr repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-top: 16px;
        }

        .qmi-ta-validation > div {
          min-width: 0;
          padding: 14px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-ta-validation__score {
          background: rgba(34, 197, 94, 0.055) !important;
          border-color: rgba(34, 197, 94, 0.18) !important;
        }

        .qmi-ta-validation span,
        .qmi-ta-validation-diagnostics span {
          display: block;
          font-size: 10px;
          font-weight: 800;
          opacity: 0.58;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .qmi-ta-validation strong {
          display: block;
          margin-top: 7px;
          font-size: 17px;
          font-weight: 900;
        }

        .qmi-ta-validation small {
          display: block;
          margin-top: 6px;
          font-size: 10px;
          opacity: 0.58;
        }

        .qmi-ta-validation-diagnostics {
          display: flex;
          flex-wrap: wrap;
          gap: 18px;
          margin-top: 10px;
          padding: 10px 12px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.10));
          border-radius: 9px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-ta-validation-diagnostics span {
          display: inline-flex;
          gap: 5px;
          align-items: center;
        }

        .qmi-ta-validation-diagnostics strong {
          color: var(--text, #f8fafc);
          opacity: 1;
        }

        .qmi-ta-validation-warning {
          margin-top: 10px;
          padding: 10px 12px;
          color: #f5c451;
          background: rgba(245, 196, 81, 0.06);
          border: 1px solid rgba(245, 196, 81, 0.14);
          border-radius: 9px;
          font-size: 11px;
          line-height: 1.5;
        }

        .qmi-ta-state-machine {
          display: grid;
          grid-template-columns: 1.25fr repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-top: 16px;
        }

        .qmi-ta-state-machine > div {
          min-width: 0;
          padding: 14px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-ta-state-machine__primary {
          background: rgba(37, 99, 235, 0.07) !important;
          border-color: rgba(37, 99, 235, 0.22) !important;
        }

        .qmi-ta-state-machine span {
          display: block;
          margin-bottom: 7px;
          font-size: 10px;
          font-weight: 800;
          opacity: 0.58;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .qmi-ta-state-machine strong {
          display: block;
          overflow: hidden;
          font-size: 16px;
          font-weight: 900;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .qmi-ta-state-machine small {
          display: block;
          margin-top: 6px;
          overflow: hidden;
          font-size: 10px;
          opacity: 0.55;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .qmi-ta-event-grid {
          display: grid;
          grid-template-columns: 1.2fr repeat(4, minmax(0, 1fr));
          gap: 10px;
          margin-top: 16px;
        }

        .qmi-ta-event-card {
          padding: 13px 14px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.13));
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-ta-event-card span {
          display: block;
          margin-bottom: 6px;
          font-size: 10px;
          opacity: 0.58;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .qmi-ta-event-card strong {
          display: block;
          font-size: 15px;
          font-weight: 900;
        }

        .qmi-ta-event-card.is-bullish strong { color: #5ee35a; }
        .qmi-ta-event-card.is-bearish strong { color: #ff5a52; }

        .qmi-ta-event-history {
          display: flex;
          gap: 7px;
          margin-top: 12px;
          overflow-x: auto;
        }

        .qmi-ta-event-chip {
          flex: 0 0 auto;
          padding: 7px 9px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.12));
          border-radius: 8px;
          font-size: 10px;
          opacity: 0.8;
        }

        .qmi-ta-structure-status {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          margin-top: 14px;
          font-size: 12px;
          opacity: 0.7;
        }

        .qmi-ta-alert,
        .qmi-ta-loading {
          border-radius: 14px;
          padding: 18px;
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
        }

        .qmi-ta-alert {
          background: rgba(220, 38, 38, 0.08);
        }

        .qmi-ta-loading {
          display: flex;
          gap: 10px;
          align-items: center;
          opacity: 0.7;
        }

        .qmi-ta-spin {
          animation: qmi-ta-spin 0.9s linear infinite;
        }

        @keyframes qmi-ta-spin {
          to {
            transform: rotate(360deg);
          }
        }

        @media (max-width: 1150px) {
          .qmi-ta-engine-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .qmi-ta-context-grid {
            grid-template-columns: repeat(2, minmax(110px, 1fr));
          }

          .qmi-ta-structure-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .qmi-ta-event-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .qmi-ta-state-machine {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .qmi-ta-validation {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }

          .qmi-ta-zone-summary,
          .qmi-ta-zones-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 760px) {
          .qmi-ta-regime-panel,
          .qmi-ta-detail-grid {
            grid-template-columns: 1fr;
          }

          .qmi-ta-engine-grid {
            grid-template-columns: 1fr;
          }

          .qmi-ta-context-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          .qmi-ta-structure-grid {
            grid-template-columns: 1fr 1fr;
          }

          .qmi-ta-event-grid {
            grid-template-columns: 1fr 1fr;
          }

          .qmi-ta-state-machine {
            grid-template-columns: 1fr 1fr;
          }

          .qmi-ta-validation {
            grid-template-columns: 1fr 1fr;
          }

          .qmi-ta-zone-summary,
          .qmi-ta-zones-strip {
            grid-template-columns: 1fr;
          }

          .qmi-ta-zones-head {
            align-items: flex-start;
            flex-direction: column;
          }

          .qmi-ta-structure-head {
            align-items: flex-start;
            flex-direction: column;
          }

          .qmi-ta-search {
            flex-wrap: wrap;
          }
        }




        /* DE-UI-008.2 — Technical Decision Panel */
        .qmi-decision {
          padding: 22px;
          background:
            linear-gradient(135deg, rgba(99, 102, 241, 0.07), rgba(15, 23, 42, 0.10) 48%, rgba(15, 23, 42, 0.02)),
            var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 16px 38px rgba(2, 6, 23, 0.10);
        }

        .qmi-decision__header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
          margin-bottom: 18px;
        }

        .qmi-decision__title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .qmi-decision__title h2 {
          margin: 3px 0 0;
          font-size: 24px;
          font-weight: 950;
          letter-spacing: -0.03em;
        }

        .qmi-decision__badge {
          min-width: 150px;
          padding: 10px 13px;
          border-radius: 10px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(148, 163, 184, 0.05);
          text-align: center;
          font-size: 14px;
          font-weight: 950;
        }

        .qmi-decision__badge.is-positive { color: #31d890; border-color: rgba(49,216,144,.24); background: rgba(49,216,144,.065); }
        .qmi-decision__badge.is-negative { color: #ff6178; border-color: rgba(255,97,120,.24); background: rgba(255,97,120,.065); }
        .qmi-decision__badge.is-neutral { color: #f4c542; }

        .qmi-decision__hero {
          display: grid;
          grid-template-columns: minmax(240px, .8fr) 2.2fr;
          gap: 12px;
        }

        .qmi-decision__posture {
          padding: 20px;
          border: 1px solid rgba(148, 163, 184, 0.13);
          border-radius: 13px;
          background: rgba(2, 6, 23, 0.20);
        }

        .qmi-decision__posture span,
        .qmi-decision__metric span,
        .qmi-decision__list span {
          display: block;
          margin-bottom: 7px;
          color: #7f8da3;
          font-size: 10px;
          font-weight: 850;
          letter-spacing: .05em;
          text-transform: uppercase;
        }

        .qmi-decision__posture strong {
          display: block;
          margin: 8px 0 4px;
          font-size: 34px;
          font-weight: 1000;
          letter-spacing: -.04em;
        }

        .qmi-decision__posture.is-positive strong { color: #31d890; }
        .qmi-decision__posture.is-negative strong { color: #ff6178; }
        .qmi-decision__posture.is-neutral strong { color: #f4c542; }

        .qmi-decision__posture small {
          display: block;
          margin-top: 7px;
          opacity: .6;
          line-height: 1.45;
        }

        .qmi-decision__metrics {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-decision__metric,
        .qmi-decision__list {
          min-width: 0;
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, 0.13);
          border-radius: 12px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-decision__metric strong {
          display: block;
          font-size: 21px;
          font-weight: 950;
          overflow-wrap: anywhere;
        }

        .qmi-decision__metric small {
          display: block;
          margin-top: 6px;
          font-size: 10px;
          opacity: .56;
        }

        .qmi-decision__lists {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
          margin-top: 12px;
        }

        .qmi-decision__list strong {
          display: block;
          font-size: 12px;
          line-height: 1.55;
          font-weight: 800;
        }

        .qmi-decision__direction {
          margin-top: 12px;
          padding: 14px 15px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-radius: 11px;
          background: rgba(2, 6, 23, 0.13);
        }

        @media (max-width: 1150px) {
          .qmi-decision__metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          .qmi-decision__lists { grid-template-columns: 1fr; }
        }

        @media (max-width: 760px) {
          .qmi-decision__hero { grid-template-columns: 1fr; }
          .qmi-decision__metrics { grid-template-columns: 1fr; }
          .qmi-decision__header { flex-direction: column; }
        }


        /* DE-UI-008.1 — Technical Confluence Panel */

        .qmi-confluence {
          padding: 22px;
          background:
            linear-gradient(
              135deg,
              rgba(37, 99, 235, 0.055),
              rgba(15, 23, 42, 0.12) 42%,
              rgba(15, 23, 42, 0.02)
            ),
            var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 16px 38px rgba(2, 6, 23, 0.10);
        }

        .qmi-confluence__header {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 18px;
          margin-bottom: 18px;
        }

        .qmi-confluence__title {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .qmi-confluence__title h2 {
          margin: 3px 0 0;
          font-size: 24px;
          font-weight: 950;
          letter-spacing: -0.03em;
        }

        .qmi-confluence__state {
          min-width: 150px;
          padding: 10px 13px;
          border-radius: 10px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(148, 163, 184, 0.05);
          text-align: center;
          font-size: 14px;
          font-weight: 950;
        }

        .qmi-confluence__state.is-positive {
          color: #31d890;
          border-color: rgba(49, 216, 144, 0.24);
          background: rgba(49, 216, 144, 0.065);
        }

        .qmi-confluence__state.is-negative {
          color: #ff6178;
          border-color: rgba(255, 97, 120, 0.24);
          background: rgba(255, 97, 120, 0.065);
        }

        .qmi-confluence__state.is-neutral {
          color: #f4c542;
        }

        .qmi-confluence__hero {
          display: grid;
          grid-template-columns: minmax(220px, 0.85fr) 2.15fr;
          gap: 18px;
          align-items: stretch;
        }

        .qmi-confluence__score {
          min-height: 180px;
          padding: 20px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          border: 1px solid rgba(148, 163, 184, 0.13);
          border-radius: 13px;
          background: rgba(2, 6, 23, 0.20);
        }

        .qmi-confluence__score > span {
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.11em;
          opacity: 0.55;
          text-transform: uppercase;
        }

        .qmi-confluence__score > strong {
          margin: 8px 0 3px;
          font-size: clamp(46px, 6vw, 70px);
          line-height: 0.95;
          font-weight: 1000;
          letter-spacing: -0.055em;
        }

        .qmi-confluence__score.is-positive > strong {
          color: #31d890;
        }

        .qmi-confluence__score.is-negative > strong {
          color: #ff6178;
        }

        .qmi-confluence__score.is-neutral > strong {
          color: #f4c542;
        }

        .qmi-confluence__score small {
          margin-top: 7px;
          font-size: 12px;
          opacity: 0.60;
        }

        .qmi-confluence__metrics {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-confluence__metric {
          min-width: 0;
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, 0.13);
          border-radius: 12px;
          background: rgba(148, 163, 184, 0.035);
        }

        .qmi-confluence__metric span {
          display: block;
          margin-bottom: 7px;
          color: #7f8da3;
          font-size: 10px;
          font-weight: 850;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }

        .qmi-confluence__metric strong {
          display: block;
          font-size: 24px;
          font-weight: 950;
          letter-spacing: -0.025em;
        }

        .qmi-confluence__metric small {
          display: block;
          margin-top: 6px;
          font-size: 10px;
          opacity: 0.56;
        }

        .qmi-confluence__direction {
          margin-top: 10px;
          padding: 14px 15px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-radius: 11px;
          background: rgba(2, 6, 23, 0.13);
        }

        .qmi-confluence__direction-head {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 9px;
          font-size: 10px;
          color: #78869a;
          font-weight: 800;
        }

        .qmi-confluence__contributions {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 9px;
          margin-top: 16px;
        }

        .qmi-confluence__engine {
          padding: 11px 12px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-radius: 10px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-confluence__engine-head,
        .qmi-confluence__engine-foot {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
        }

        .qmi-confluence__engine-head span {
          display: block;
          font-size: 11px;
          font-weight: 900;
        }

        .qmi-confluence__engine-head small,
        .qmi-confluence__engine-foot {
          color: #738096;
          font-size: 9px;
        }

        .qmi-confluence__engine-head strong {
          font-size: 15px;
          font-weight: 1000;
        }

        .qmi-confluence__engine.is-positive .qmi-confluence__engine-head strong {
          color: #31d890;
        }

        .qmi-confluence__engine.is-negative .qmi-confluence__engine-head strong {
          color: #ff6178;
        }

        .qmi-confluence__engine.is-neutral .qmi-confluence__engine-head strong {
          color: #f4c542;
        }

        .qmi-confluence__engine-track {
          position: relative;
          height: 5px;
          margin: 9px 0 7px;
          overflow: hidden;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.10);
        }

        .qmi-confluence__engine-center {
          position: absolute;
          left: 50%;
          top: 0;
          bottom: 0;
          width: 1px;
          z-index: 2;
          background: rgba(226, 232, 240, 0.30);
        }

        .qmi-confluence__engine-fill {
          position: absolute;
          top: 0;
          bottom: 0;
          border-radius: 999px;
        }

        .qmi-confluence__engine.is-positive .qmi-confluence__engine-fill {
          background: #31d890;
        }

        .qmi-confluence__engine.is-negative .qmi-confluence__engine-fill {
          background: #ff6178;
        }

        .qmi-confluence__engine.is-neutral .qmi-confluence__engine-fill {
          background: #f4c542;
        }

        .qmi-confluence__audit {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 10px;
          margin-top: 14px;
        }

        .qmi-confluence__audit > div {
          padding: 12px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          border-radius: 10px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-confluence__audit span {
          display: block;
          margin-bottom: 5px;
          color: #748196;
          font-size: 9px;
          font-weight: 850;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .qmi-confluence__audit strong {
          font-size: 12px;
          font-weight: 900;
        }

        .qmi-confluence__conflicts {
          margin-top: 12px;
          padding: 11px 13px;
          border-radius: 9px;
          border: 1px solid rgba(148, 163, 184, 0.10);
          background: rgba(148, 163, 184, 0.025);
          color: #7f8da3;
          font-size: 10px;
        }

        .qmi-confluence__conflicts.has-conflicts {
          color: #f4c542;
          border-color: rgba(244, 197, 66, 0.18);
          background: rgba(244, 197, 66, 0.045);
        }

        @media (max-width: 1150px) {
          .qmi-confluence__hero {
            grid-template-columns: 1fr;
          }

          .qmi-confluence__metrics {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 760px) {
          .qmi-confluence__header {
            flex-direction: column;
          }

          .qmi-confluence__metrics,
          .qmi-confluence__contributions,
          .qmi-confluence__audit {
            grid-template-columns: 1fr;
          }
        }

/* DE-UI-007.6 — Sweep Cluster Map Integration */

.qmi-ichart__cluster-band {
  stroke-width: 1;
}

.qmi-ichart__cluster.is-bsl .qmi-ichart__cluster-band {
  fill: #d946ef;
  stroke: rgba(217, 70, 239, 0.28);
}

.qmi-ichart__cluster.is-ssl .qmi-ichart__cluster-band {
  fill: #22d3ee;
  stroke: rgba(34, 211, 238, 0.28);
}

.qmi-ichart__cluster-line {
  stroke-width: 1.7;
  stroke-dasharray: 10 5;
}

.qmi-ichart__cluster.is-bsl .qmi-ichart__cluster-line,
.qmi-ichart__cluster.is-bsl .qmi-ichart__cluster-node {
  stroke: #d946ef;
}

.qmi-ichart__cluster.is-ssl .qmi-ichart__cluster-line,
.qmi-ichart__cluster.is-ssl .qmi-ichart__cluster-node {
  stroke: #22d3ee;
}

.qmi-ichart__cluster-node {
  fill: #070c13;
  stroke-width: 2;
}

.qmi-ichart__cluster.is-strong .qmi-ichart__cluster-node {
  stroke-width: 3;
}

.qmi-ichart__cluster-label {
  font-size: 9px;
  font-weight: 1000;
  letter-spacing: 0.04em;
}

.qmi-ichart__cluster.is-bsl .qmi-ichart__cluster-label {
  fill: #e879f9;
}

.qmi-ichart__cluster.is-ssl .qmi-ichart__cluster-label {
  fill: #67e8f9;
}

.qmi-ichart__latest-cluster {
  display: grid;
  grid-template-columns: auto auto 1fr;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(148, 163, 184, 0.10);
  background: rgba(148, 163, 184, 0.025);
  font-size: 9px;
}

.qmi-ichart__latest-cluster span {
  color: #738096;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.qmi-ichart__latest-cluster strong {
  font-size: 10px;
  font-weight: 950;
}

.qmi-ichart__latest-cluster small {
  color: #748196;
}

.qmi-ichart__latest-cluster.is-bullish strong {
  color: #22d3ee;
}

.qmi-ichart__latest-cluster.is-bearish strong {
  color: #d946ef;
}

.qmi-ichart__legend i.is-cluster {
  background: linear-gradient(
    90deg,
    #d946ef 0 50%,
    #22d3ee 50% 100%
  );
}
      `}</style>

      <form className="qmi-ta-toolbar" onSubmit={submit}>
        <div className="qmi-ta-search">
          <div className="qmi-ta-search-box">
            <Search size={17} />
            <input
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
              placeholder="Ticker"
              maxLength={16}
              aria-label="Ticker symbol"
            />
          </div>

          <div className="qmi-ta-toolbar-selects">
            <select
              value={period}
              onChange={(event) => setPeriod(event.target.value)}
              aria-label="Historical period"
            >
              <option value="1y">1 Year</option>
              <option value="2y">2 Years</option>
              <option value="5y">5 Years</option>
            </select>

            <select
              value={interval}
              onChange={(event) => setInterval(event.target.value)}
              aria-label="Historical interval"
            >
              <option value="1d">Daily</option>
              <option value="1wk">Weekly</option>
            </select>
          </div>

          <button type="submit" disabled={loading}>
            {loading ? (
              <RefreshCw className="qmi-ta-spin" size={16} />
            ) : (
              <Activity size={16} />
            )}
            Analyze
          </button>
        </div>
      </form>

      {error && <div className="qmi-ta-alert">{error}</div>}

      {loading && !technical && (
        <div className="qmi-ta-loading">
          <RefreshCw className="qmi-ta-spin" size={17} />
          QMI is calculating the technical state...
        </div>
      )}

      {technical && (
        <>
          <section className="qmi-ta-regime-panel">
            <div>
              <span className="qmi-ta-kicker">
                QMI MARKET REGIME · {submittedSymbol}
              </span>
              <div className="qmi-ta-regime-name">
                {pretty(regime.primary_regime)}
              </div>
              <div className="qmi-ta-regime-sub">
                {pretty(regime.transition_state)} · DMI{" "}
                {pretty(regime.dmi_direction)}
              </div>
            </div>

            <div className="qmi-ta-context-grid">
              {marketContext.map((item) => (
                <div className="qmi-ta-context" key={item.label}>
                  <span>{item.label}</span>
                  <strong>{item.value}</strong>
                </div>
              ))}
            </div>
          </section>

          <section className="qmi-confluence">
            <div className="qmi-confluence__header">
              <div className="qmi-confluence__title">
                <div className="qmi-ta-icon-box">
                  <Layers3 size={19} strokeWidth={1.8} />
                </div>

                <div>
                  <span className="qmi-ta-kicker">
                    DE-UI-008.1 · TECHNICAL CONFLUENCE
                  </span>
                  <h2>QMI Technical Confluence Engine</h2>
                </div>
              </div>

              <div className={`qmi-confluence__state is-${confluenceTone}`}>
                {confluenceLoading && !confluence
                  ? "CALCULATING"
                  : pretty(technicalConfluence?.state)}
              </div>
            </div>

            {confluenceLoading && !confluence ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Fusing technical evidence...
              </div>
            ) : confluenceError ? (
              <div className="qmi-ta-alert">{confluenceError}</div>
            ) : confluence ? (
              <>
                <div className="qmi-confluence__hero">
                  <div className={`qmi-confluence__score is-${confluenceTone}`}>
                    <span>Technical Direction Score</span>
                    <strong>
                      {formatScore(technicalConfluence?.direction_score)}
                    </strong>
                    <small>
                      -100 Bearish · 0 Neutral · +100 Bullish
                    </small>
                  </div>

                  <div>
                    <div className="qmi-confluence__metrics">
                      <div className="qmi-confluence__metric">
                        <span>Confidence</span>
                        <strong>
                          {formatPercent(technicalConfluence?.confidence)}
                        </strong>
                        <small>Reliability of current fused reading</small>
                      </div>

                      <div className="qmi-confluence__metric">
                        <span>Agreement</span>
                        <strong>
                          {formatPercent(technicalConfluence?.agreement)}
                        </strong>
                        <small>Directional engine alignment</small>
                      </div>

                      <div className="qmi-confluence__metric">
                        <span>Data Quality</span>
                        <strong>
                          {formatPercent(technicalConfluence?.data_quality)}
                        </strong>
                        <small>Weakest available engine quality</small>
                      </div>

                      <div className="qmi-confluence__metric">
                        <span>Engine Vote</span>
                        <strong>
                          {technicalConfluence?.bearish_engines ?? 0}B ·{" "}
                          {technicalConfluence?.bullish_engines ?? 0}U
                        </strong>
                        <small>
                          {technicalConfluence?.neutral_engines ?? 0} neutral
                        </small>
                      </div>
                    </div>

                    <div className="qmi-confluence__direction">
                      <div className="qmi-confluence__direction-head">
                        <span>BEARISH</span>
                        <strong>{pretty(technicalConfluence?.state)}</strong>
                        <span>BULLISH</span>
                      </div>
                      <DirectionBar
                        value={technicalConfluence?.direction_score}
                      />
                    </div>
                  </div>
                </div>

                {confluenceContributions.length > 0 && (
                  <div className="qmi-confluence__contributions">
                    {confluenceContributions.map((item) => (
                      <ConfluenceContribution
                        key={item.engine}
                        item={item}
                      />
                    ))}
                  </div>
                )}

                <div className="qmi-confluence__audit">
                  <div>
                    <span>Dominant Negative</span>
                    <strong>
                      {pretty(
                        confluenceDiagnostics?.dominant_negative_engine
                          ?.engine
                      )}{" "}
                      {formatScore(
                        confluenceDiagnostics?.dominant_negative_engine
                          ?.normalized_contribution,
                        2
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Dominant Positive</span>
                    <strong>
                      {pretty(
                        confluenceDiagnostics?.dominant_positive_engine
                          ?.engine
                      )}{" "}
                      {formatScore(
                        confluenceDiagnostics?.dominant_positive_engine
                          ?.normalized_contribution,
                        2
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>Volatility Modifier</span>
                    <strong>
                      {formatPercent(
                        confluenceDiagnostics?.confidence
                          ?.volatility_modifier
                      )}
                    </strong>
                  </div>
                </div>

                <div
                  className={`qmi-confluence__conflicts ${
                    confluenceConflicts.length > 0
                      ? "has-conflicts"
                      : ""
                  }`}
                >
                  {confluenceConflicts.length === 0
                    ? "No material directional conflicts detected between major engines."
                    : `${confluenceConflicts.length} conflict(s): ${confluenceConflicts
                        .map((item) => pretty(item.type))
                        .join(" · ")}`}
                </div>
              </>
            ) : null}
          </section>


          <section className="qmi-decision">
            <div className="qmi-decision__header">
              <div className="qmi-decision__title">
                <div className="qmi-ta-icon-box">
                  <ShieldCheck size={19} strokeWidth={1.8} />
                </div>
                <div>
                  <span className="qmi-ta-kicker">
                    DE-UI-008.2 · TECHNICAL DECISION
                  </span>
                  <h2>QMI Technical Decision Layer</h2>
                </div>
              </div>

              <div className={`qmi-decision__badge is-${decisionTone}`}>
                {decisionLoading && !technicalDecision
                  ? "CALCULATING"
                  : pretty(
                      decisionPosture?.state ||
                      decisionCore?.state ||
                      technicalDecision?.state
                    )}
              </div>
            </div>

            {decisionLoading && !technicalDecision ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Converting technical evidence into decision posture...
              </div>
            ) : decisionError ? (
              <div className="qmi-ta-alert">{decisionError}</div>
            ) : technicalDecision ? (
              <>
                <div className="qmi-decision__hero">
                  <div className={`qmi-decision__posture is-${decisionTone}`}>
                    <span>Decision Posture</span>
                    <strong>
                      {pretty(
                        decisionPosture?.state ||
                        decisionCore?.state ||
                        technicalDecision?.state
                      )}
                    </strong>
                    <small>
                      {pretty(
                        decisionPosture?.directional_state ||
                        decisionCore?.directional_state
                      )} · Conviction{" "}
                      {pretty(
                        decisionPosture?.conviction ||
                        decisionCore?.conviction
                      )}
                    </small>
                  </div>

                  <div className="qmi-decision__metrics">
                    <div className="qmi-decision__metric">
                      <span>Direction Score</span>
                      <strong>{formatScore(decisionScore)}</strong>
                      <small>-100 Bearish · +100 Bullish</small>
                    </div>

                    <div className="qmi-decision__metric">
                      <span>Confidence</span>
                      <strong>
                        {formatPercent(
                          decisionCore?.confidence ??
                          technicalDecision?.confidence
                        )}
                      </strong>
                      <small>Decision-layer reliability</small>
                    </div>

                    <div className="qmi-decision__metric">
                      <span>Readiness</span>
                      <strong>
                        {formatPercent(
                          decisionReadiness?.score ??
                          decisionReadiness?.readiness_score ??
                          decisionCore?.readiness_score
                        )}
                      </strong>
                      <small>
                        {pretty(
                          decisionReadiness?.state ||
                          decisionCore?.readiness_state
                        )}
                      </small>
                    </div>

                    <div className="qmi-decision__metric">
                      <span>Long Exposure</span>
                      <strong>
                        {pretty(
                          exposureContext?.new_long_exposure ||
                          exposureContext?.long_exposure ||
                          decisionCore?.new_long_exposure
                        )}
                      </strong>
                      <small>
                        {pretty(
                          exposureContext?.existing_long_exposure ||
                          decisionCore?.existing_long_exposure
                        )} existing
                      </small>
                    </div>
                  </div>
                </div>

                <div className="qmi-decision__direction">
                  <DirectionBar value={decisionScore} />
                </div>

                <div className="qmi-decision__lists">
                  <div className="qmi-decision__list">
                    <span>Decision Blockers</span>
                    <strong>
                      {decisionBlockers.length
                        ? decisionBlockers
                            .slice(0, 4)
                            .map((item) => {
                              if (typeof item === "string") {
                                return pretty(item);
                              }

                              const engine = pretty(item?.engine);
                              const score = formatScore(item?.score);
                              const severity = pretty(item?.severity);

                              return `${engine} ${score} · ${severity}`;
                            })
                            .join("  |  ")
                        : "None"}
                    </strong>
                  </div>

                  <div className="qmi-decision__list">
                    <span>Reversal Requirements</span>
                    <strong>
                      {reversalRequirements.length
                        ? reversalRequirements
                            .slice(0, 4)
                            .map((item) => {
                              if (typeof item === "string") {
                                return pretty(item);
                              }

                              const priority =
                                item?.priority !== undefined
                                  ? `P${item.priority} `
                                  : "";

                              return `${priority}${pretty(
                                item?.requirement
                              )} · ${item?.target || "--"}`;
                            })
                            .join("  |  ")
                        : "No active reversal requirement"}
                    </strong>
                  </div>

                  <div className="qmi-decision__list">
                    <span>Risk Flags</span>
                    <strong>
                      {riskFlags.length
                        ? riskFlags
                            .map((item) => {
                              if (typeof item === "string") {
                                return pretty(item);
                              }

                              return `${pretty(item?.flag)} · ${pretty(
                                item?.severity
                              )}`;
                            })
                            .join("  |  ")
                        : "No material risk flags"}
                    </strong>
                  </div>
                </div>
              </>
            ) : null}
          </section>

          <section className="qmi-ta-chart-panel">
            <div className="qmi-ta-chart-head">
              <div className="qmi-ta-chart-title">
                <div className="qmi-ta-icon-box">
                  <BarChart3 size={19} strokeWidth={1.8} />
                </div>

                <div>
                  <span className="qmi-ta-kicker">
                    DE-UI-007.6 · SWEEP CLUSTER MAP
                  </span>
                  <h2>Market Structure Price Map</h2>
                </div>
              </div>

              <div className="qmi-ta-structure-badge">
                {submittedSymbol}
              </div>
            </div>

            {chartLoading && chartHistory.length === 0 ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Rendering institutional price map...
              </div>
            ) : chartError ? (
              <div className="qmi-ta-alert">{chartError}</div>
            ) : (
              <InstitutionalChart
                history={chartHistory}
                marketStructure={marketStructure}
                supportResistance={supportResistance}
                liquidity={liquidity}
                maxBars={120}
              />
            )}
          </section>

          <section className="qmi-ta-structure-panel">
            <div className="qmi-ta-structure-head">
              <div className="qmi-ta-structure-title">
                <div className="qmi-ta-icon-box">
                  <GitBranch size={19} strokeWidth={1.8} />
                </div>

                <div>
                  <span className="qmi-ta-kicker">
                    DE-TA-005.4 · MARKET STRUCTURE
                  </span>
                  <h2>Confirmed Swing Structure</h2>
                </div>
              </div>

              <div
                className={`qmi-ta-structure-badge is-${structureTone}`}
              >
                {pretty(structureTrend.state)}
              </div>
            </div>

            {structureLoading && !marketStructure ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Detecting confirmed market structure...
              </div>
            ) : structureError ? (
              <div className="qmi-ta-alert">{structureError}</div>
            ) : marketStructure ? (
              <>
                <div className="qmi-ta-structure-grid">
                  <div className="qmi-ta-structure-metric">
                    <span>High Structure</span>
                    <strong>
                      {latestStructure.last_swing_high?.label || "--"}
                    </strong>
                  </div>

                  <div className="qmi-ta-structure-metric">
                    <span>Low Structure</span>
                    <strong>
                      {latestStructure.last_swing_low?.label || "--"}
                    </strong>
                  </div>

                  <div className="qmi-ta-structure-metric">
                    <span>Last Swing High</span>
                    <strong>
                      {latestStructure.last_swing_high?.price === undefined
                        ? "--"
                        : `$${formatNumber(
                            latestStructure.last_swing_high.price,
                            2
                          )}`}
                    </strong>
                  </div>

                  <div className="qmi-ta-structure-metric">
                    <span>Last Swing Low</span>
                    <strong>
                      {latestStructure.last_swing_low?.price === undefined
                        ? "--"
                        : `$${formatNumber(
                            latestStructure.last_swing_low.price,
                            2
                          )}`}
                    </strong>
                  </div>

                  <div className="qmi-ta-structure-metric">
                    <span>Confirmed Pivots</span>
                    <strong>{marketStructure.counts?.swings ?? "--"}</strong>
                  </div>
                </div>

                <div className="qmi-ta-structure-reason">
                  <strong>{pretty(structureTrend.bias)} bias.</strong>{" "}
                  {structureTrend.reason || "Structural state available."}{" "}
                  Confirmation requires{" "}
                  {marketStructure.confirmation_bars ?? "--"} bars to the
                  right of each pivot.
                </div>

                <div className="qmi-ta-validation">
                  <div className="qmi-ta-validation__score">
                    <span>Structure Quality</span>
                    <strong>
                      {structureValidation?.score === undefined
                        ? "--"
                        : `${formatNumber(
                            structureValidation.score,
                            1
                          )}/100`}
                    </strong>
                    <small>
                      {pretty(structureValidation?.label)} ·{" "}
                      {structureValidation?.is_decision_ready
                        ? "Decision-ready"
                        : "Validation required"}
                    </small>
                  </div>

                  <div>
                    <span>Clarity</span>
                    <strong>
                      {validationComponents?.clarity === undefined
                        ? "--"
                        : `${formatNumber(
                            validationComponents.clarity,
                            0
                          )}%`}
                    </strong>
                  </div>

                  <div>
                    <span>Swing Recency</span>
                    <strong>
                      {validationComponents?.swing_recency === undefined
                        ? "--"
                        : `${formatNumber(
                            validationComponents.swing_recency,
                            0
                          )}%`}
                    </strong>
                  </div>

                  <div>
                    <span>Protected Level</span>
                    <strong>
                      {validationComponents?.protected_level_quality === undefined
                        ? "--"
                        : `${formatNumber(
                            validationComponents.protected_level_quality,
                            0
                          )}%`}
                    </strong>
                  </div>

                  <div>
                    <span>Event Consistency</span>
                    <strong>
                      {validationComponents?.event_consistency === undefined
                        ? "--"
                        : `${formatNumber(
                            validationComponents.event_consistency,
                            0
                          )}%`}
                    </strong>
                  </div>
                </div>

                <div className="qmi-ta-validation-diagnostics">
                  <span>
                    Latest swing:{" "}
                    <strong>
                      {validationDiagnostics?.bars_since_latest_swing ?? "--"} bars
                    </strong>
                  </span>
                  <span>
                    Protected age:{" "}
                    <strong>
                      {validationDiagnostics?.protected_level_age_bars ?? "--"} bars
                    </strong>
                  </span>
                  <span>
                    Protected distance:{" "}
                    <strong>
                      {validationDiagnostics?.protected_level_distance_pct === null ||
                      validationDiagnostics?.protected_level_distance_pct === undefined
                        ? "--"
                        : `${formatNumber(
                            validationDiagnostics.protected_level_distance_pct,
                            2
                          )}%`}
                    </strong>
                  </span>
                </div>

                {validationWarnings.length > 0 && (
                  <div className="qmi-ta-validation-warning">
                    {validationWarnings.join(" · ")}
                  </div>
                )}

                <div className="qmi-ta-state-machine">
                  <div className="qmi-ta-state-machine__primary">
                    <span>Structural State</span>
                    <strong>{pretty(structuralState)}</strong>
                    <small>
                      Persistent state machine · close-confirmed events
                    </small>
                  </div>

                  <div>
                    <span>Protected High</span>
                    <strong>
                      {protectedHigh?.price === undefined
                        ? "--"
                        : `$${formatNumber(protectedHigh.price, 2)}`}
                    </strong>
                    <small>
                      {protectedHigh?.date
                        ? String(protectedHigh.date)
                        : "Not active"}
                    </small>
                  </div>

                  <div>
                    <span>Protected Low</span>
                    <strong>
                      {protectedLow?.price === undefined
                        ? "--"
                        : `$${formatNumber(protectedLow.price, 2)}`}
                    </strong>
                    <small>
                      {protectedLow?.date
                        ? String(protectedLow.date)
                        : "Not active"}
                    </small>
                  </div>

                  <div>
                    <span>Last BOS</span>
                    <strong>
                      {lastBos?.type ? pretty(lastBos.type) : "--"}
                    </strong>
                    <small>
                      {lastBos?.date
                        ? `${lastBos.date} · $${formatNumber(
                            lastBos.broken_level,
                            2
                          )}`
                        : "No BOS confirmed"}
                    </small>
                  </div>

                  <div>
                    <span>Last CHoCH</span>
                    <strong>
                      {lastChoch?.type ? pretty(lastChoch.type) : "--"}
                    </strong>
                    <small>
                      {lastChoch?.date
                        ? `${lastChoch.date} · $${formatNumber(
                            lastChoch.broken_level,
                            2
                          )}`
                        : "No CHoCH confirmed"}
                    </small>
                  </div>
                </div>

                <div className="qmi-ta-event-grid">
                  <div
                    className={`qmi-ta-event-card ${
                      latestStructureEvent?.direction === "BULLISH"
                        ? "is-bullish"
                        : latestStructureEvent?.direction === "BEARISH"
                          ? "is-bearish"
                          : ""
                    }`}
                  >
                    <span>Latest Structural Event</span>
                    <strong>
                      {latestStructureEvent?.type
                        ? pretty(latestStructureEvent.type)
                        : "No confirmed break"}
                    </strong>
                  </div>

                  <div className="qmi-ta-event-card">
                    <span>Broken Level</span>
                    <strong>
                      {latestStructureEvent?.broken_level === undefined
                        ? "--"
                        : `$${formatNumber(
                            latestStructureEvent.broken_level,
                            2
                          )}`}
                    </strong>
                  </div>

                  <div className="qmi-ta-event-card">
                    <span>Confirmation</span>
                    <strong>
                      {latestStructureEvent?.confirmation_price === undefined
                        ? "--"
                        : `$${formatNumber(
                            latestStructureEvent.confirmation_price,
                            2
                          )}`}
                    </strong>
                  </div>

                  <div className="qmi-ta-event-card">
                    <span>Break Distance</span>
                    <strong>
                      {latestStructureEvent?.break_distance_pct === undefined
                        ? "--"
                        : `${formatNumber(
                            latestStructureEvent.break_distance_pct,
                            2
                          )}%`}
                    </strong>
                  </div>

                  <div className="qmi-ta-event-card">
                    <span>Event Confidence</span>
                    <strong>
                      {latestStructureEvent?.confidence === undefined
                        ? "--"
                        : `${formatNumber(
                            latestStructureEvent.confidence,
                            1
                          )}%`}
                    </strong>
                  </div>
                </div>

                {structureEvents.length > 0 && (
                  <div className="qmi-ta-event-history">
                    {structureEvents.slice(-6).map((event, index) => (
                      <div
                        className="qmi-ta-event-chip"
                        key={`${event.date}-${event.type}-${index}`}
                        title={`Broken ${event.broken_level} · close ${event.confirmation_price}`}
                      >
                        {pretty(event.type)} · {String(event.date || "").slice(5)}
                      </div>
                    ))}
                  </div>
                )}

                {structureSwings.length > 0 && (
                  <div className="qmi-ta-swing-strip">
                    {structureSwings.slice(-10).map((swing, index) => (
                      <div
                        className={`qmi-ta-swing-chip ${
                          swing.kind === "SWING_HIGH"
                            ? "is-high"
                            : "is-low"
                        }`}
                        key={`${swing.date}-${swing.kind}-${index}`}
                        title={`${swing.date} · ${swing.kind}`}
                      >
                        <strong>{swing.label || "PIVOT"}</strong>
                        <span>
                          ${formatNumber(swing.price, 2)} ·{" "}
                          {String(swing.date || "").slice(5)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </section>

          <section className="qmi-ta-zones-panel">
            <div className="qmi-ta-zones-head">
              <div className="qmi-ta-zones-title">
                <div className="qmi-ta-icon-box">
                  <Layers3 size={19} strokeWidth={1.8} />
                </div>

                <div>
                  <span className="qmi-ta-kicker">
                    DE-TA-006.1 · SUPPORT & RESISTANCE
                  </span>
                  <h2>Structural Price Zones</h2>
                </div>
              </div>

              <div className="qmi-ta-structure-badge">
                {supportResistance
                  ? `${structuralZones.length} zones`
                  : "--"}
              </div>
            </div>

            {zonesLoading && !supportResistance ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building structural price zones...
              </div>
            ) : zonesError ? (
              <div className="qmi-ta-alert">{zonesError}</div>
            ) : supportResistance ? (
              <>
                <div className="qmi-ta-zone-summary">
                  <div>
                    <span>Nearest Support</span>
                    <strong>
                      {nearestSupport
                        ? `$${formatNumber(
                            nearestSupport.lower,
                            2
                          )} – $${formatNumber(
                            nearestSupport.upper,
                            2
                          )}`
                        : "--"}
                    </strong>
                  </div>

                  <div>
                    <span>Nearest Resistance</span>
                    <strong>
                      {nearestResistance
                        ? `$${formatNumber(
                            nearestResistance.lower,
                            2
                          )} – $${formatNumber(
                            nearestResistance.upper,
                            2
                          )}`
                        : "--"}
                    </strong>
                  </div>

                  <div>
                    <span>Active Zone</span>
                    <strong>
                      {activeZone
                        ? pretty(activeZone.type)
                        : "None"}
                    </strong>
                  </div>

                  <div>
                    <span>ATR 14</span>
                    <strong>
                      ${formatNumber(supportResistance.atr14, 3)}
                    </strong>
                  </div>
                </div>

                {structuralZones.length > 0 && (
                  <div className="qmi-ta-zones-strip">
                    {structuralZones.map((zone, index) => (
                      <div
                        className={`qmi-ta-zone-card ${
                          zone.type === "SUPPORT"
                            ? "is-support"
                            : "is-resistance"
                        }`}
                        key={`${zone.type}-${zone.center}-${index}`}
                      >
                        <span>
                          {pretty(zone.type)} · {pretty(zone.quality)}
                        </span>
                        <strong>
                          ${formatNumber(zone.lower, 2)} – $
                          {formatNumber(zone.upper, 2)}
                        </strong>
                        <small>
                          {zone.touches} touches ·{" "}
                          {formatNumber(zone.distance_pct, 2)}% away ·{" "}
                          last {zone.age_bars} bars ago
                        </small>
                        <small>
                          Avg reaction{" "}
                          {formatNumber(
                            zone.average_reaction_pct,
                            2
                          )}% · strength{" "}
                          {formatNumber(zone.strength, 1)}/100
                        </small>

                        <div className="qmi-ta-zone-strength">
                          <div
                            style={{
                              width: `${clamp(
                                zone.strength,
                                0,
                                100
                              )}%`
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            ) : null}
          </section>

          <div className="qmi-ta-engine-grid">
            <EngineCard
              title="Trend"
              icon={ArrowUpRight}
              score={trend.score}
              state={trend.direction}
              directional
            >
              <div className="qmi-ta-metrics">
                <Metric
                  label="Agreement"
                  value={formatPercent(regime.trend_agreement)}
                />
                <Metric
                  label="Structure quality"
                  value={formatPercent(regime.structure_quality)}
                />
                <Metric
                  label="Temporal stability"
                  value={formatPercent(regime.temporal_stability)}
                />
              </div>
            </EngineCard>

            <EngineCard
              title="Strength"
              icon={Gauge}
              score={strength.score}
              state={strength.strength}
            >
              <div className="qmi-ta-metrics">
                <Metric label="DMI" value={pretty(strength.dmi_direction)} />
                <Metric
                  label="Regime conflict"
                  value={strength.regime_conflict ? "YES" : "NO"}
                />
                <Metric
                  label="Data quality"
                  value={formatPercent(strength.data_quality)}
                />
              </div>
            </EngineCard>

            <EngineCard
              title="Momentum"
              icon={
                Number(momentum.score) >= 0
                  ? ArrowUpRight
                  : ArrowDownRight
              }
              score={momentum.score}
              state={momentum.state}
              confidence={momentum.confidence}
              directional
            >
              <div className="qmi-ta-metrics">
                <Metric
                  label="Acceleration"
                  value={pretty(momentum.acceleration)}
                />
                <Metric
                  label="Δ 5 sessions"
                  value={formatScore(momentum.momentum_delta_5)}
                />
                <Metric
                  label="Δ 10 sessions"
                  value={formatScore(momentum.momentum_delta_10)}
                />
                <Metric
                  label="Divergence"
                  value={pretty(momentum.divergence_type)}
                />
              </div>
            </EngineCard>

            <EngineCard
              title="Volatility"
              icon={Waves}
              score={volatility.score}
              state={volatility.state}
              confidence={volatility.confidence}
            >
              <div className="qmi-ta-metrics">
                <Metric
                  label="Direction"
                  value={pretty(volatility.direction)}
                />
                <Metric
                  label="Risk environment"
                  value={pretty(volatility.risk_environment)}
                />
                <Metric
                  label="Compression"
                  value={volatility.compression ? "YES" : "NO"}
                />
                <Metric
                  label="Expansion"
                  value={volatility.expansion ? "YES" : "NO"}
                />
              </div>
            </EngineCard>

            <EngineCard
              title="Volume"
              icon={BarChart3}
              score={volume.score}
              state={volume.state}
              confidence={volume.confidence}
              directional
            >
              <div className="qmi-ta-metrics">
                <Metric
                  label="Direction"
                  value={pretty(volume.direction)}
                />
                <Metric
                  label="Participation"
                  value={formatPercent(volume.participation_score)}
                />
                <Metric
                  label="RVOL"
                  value={formatNumber(volume.relative_volume, 2)}
                />
                <Metric
                  label="Breakout"
                  value={pretty(volume.breakout_confirmation)}
                />
              </div>
            </EngineCard>
          </div>

          <div className="qmi-ta-detail-grid">
            <section className="qmi-ta-detail-panel">
              <h3>Momentum Components</h3>
              <div className="qmi-ta-detail-list">
                {Object.entries(momentum.components || {}).map(
                  ([key, component]) => (
                    <Metric
                      key={key}
                      label={`${pretty(key)} · ${Math.round(
                        Number(component.weight || 0) * 100
                      )}%`}
                      value={`${formatScore(component.score)} · ${pretty(
                        component.state
                      )}`}
                    />
                  )
                )}
              </div>
            </section>

            <section className="qmi-ta-detail-panel">
              <h3>Volatility Diagnostics</h3>
              <div className="qmi-ta-detail-list">
                <Metric
                  label="ATR normalized"
                  value={formatPercent(volatility.atr_normalized, 2)}
                />
                <Metric
                  label="ATR percentile"
                  value={formatPercent(volatility.atr_percentile, 2)}
                />
                <Metric
                  label="HV 20"
                  value={formatPercent(
                    Number(volatility.historical_volatility_20) * 100,
                    2
                  )}
                />
                <Metric
                  label="HV 60"
                  value={formatPercent(
                    Number(volatility.historical_volatility_60) * 100,
                    2
                  )}
                />
                <Metric
                  label="HV ratio"
                  value={formatNumber(volatility.hv_ratio, 3)}
                />
                <Metric
                  label="Bandwidth percentile"
                  value={formatPercent(
                    volatility.bandwidth_percentile,
                    2
                  )}
                />
              </div>
            </section>

            <section className="qmi-ta-detail-panel">
              <h3>Volume Diagnostics</h3>
              <div className="qmi-ta-detail-list">
                <Metric
                  label="Participation"
                  value={formatPercent(volume.participation_score)}
                />
                <Metric
                  label="Relative volume"
                  value={formatNumber(volume.relative_volume, 2)}
                />
                <Metric
                  label="Volume Z-score"
                  value={formatNumber(volume.volume_zscore, 2)}
                />
                <Metric
                  label="Up / Down ratio"
                  value={formatNumber(volume.up_down_ratio, 2)}
                />
                <Metric
                  label="Volume trend"
                  value={formatPercent(volume.volume_trend, 2)}
                />
                <Metric
                  label="Divergence"
                  value={pretty(volume.divergence_type)}
                />
                <Metric
                  label="Climax"
                  value={pretty(volume.climax)}
                />
                <Metric
                  label="Dry-up"
                  value={volume.dry_up ? "YES" : "NO"}
                />
                <Metric
                  label="False breakout risk"
                  value={volume.false_breakout_risk ? "YES" : "NO"}
                />
              </div>
            </section>
          </div>

          {regime.regime_conflict && (
            <div className="qmi-ta-alert">
              <ShieldAlert size={18} /> QMI has detected a directional
              conflict between Trend and DMI. Regime confidence has been
              penalized.
            </div>
          )}
        </>
      )}
    </div>
  );
}

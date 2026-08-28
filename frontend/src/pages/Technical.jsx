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
  getTechnicalDecision,
  getTechnicalActionFramework,
  getTechnicalRiskExposure,
  getTechnicalPositionSizing,
  getTechnicalUiSnapshot
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
  const magnitude = Math.min(100, Math.abs(score));
  const tone =
    score > 0.01
      ? "is-positive"
      : score < -0.01
        ? "is-negative"
        : "is-neutral";

  const engineName = String(item?.engine || "").trim().toUpperCase();

  const engineIcon =
    engineName === "STRUCTURE"
      ? GitBranch
      : engineName === "TREND"
        ? ArrowDownRight
        : engineName === "LIQUIDITY"
          ? Waves
          : engineName === "STRENGTH"
            ? ShieldCheck
            : Activity;

  const EngineIcon = engineIcon;

  return (
    <div className={`qmi-confluence__engine qmi-confluence__engine--large ${tone}`}>
      <div className="qmi-confluence__engine-main">
        <div className="qmi-confluence__engine-identity">
          <div className="qmi-confluence__engine-icon">
            <EngineIcon size={19} strokeWidth={1.9} />
          </div>

          <div>
            <span>{pretty(item?.engine)}</span>
            <small>
              {pretty(item?.vote)} · effective weight{" "}
              {formatPercent(item?.effective_weight_pct)}
            </small>
          </div>
        </div>

        <div className="qmi-confluence__engine-values">
          <strong>{formatScore(score, 2)}</strong>
          <b>{formatPercent(item?.confidence)}</b>
        </div>
      </div>

      <div className="qmi-confluence__engine-scale">
        <div className="qmi-confluence__engine-track">
          <div className="qmi-confluence__engine-center" />
          <div className="qmi-confluence__engine-quarter is-left" />
          <div className="qmi-confluence__engine-quarter is-right" />
          <div
            className="qmi-confluence__engine-fill"
            style={{
              width: `${magnitude / 2}%`,
              left: score >= 0 ? "50%" : `${50 - magnitude / 2}%`
            }}
          />
        </div>

        <div className="qmi-confluence__axis-labels">
          <span>-100</span>
          <span>-50</span>
          <span>0</span>
          <span>+50</span>
          <span>+100</span>
        </div>
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
  const [actionFramework, setActionFramework] = useState(null);
  const [riskExposure, setRiskExposure] = useState(null);
  const [positionSizing, setPositionSizing] = useState(null);
  const [executionPlan, setExecutionPlan] = useState(null);
  const [stateTransition, setStateTransition] = useState(null);
  const [statePersistence, setStatePersistence] = useState(null);
  const [regimeMaturity, setRegimeMaturity] = useState(null);
  const [transitionConfirmation, setTransitionConfirmation] = useState(null);
  const [decisionSynthesis, setDecisionSynthesis] = useState(null);
  const [technicalSetup, setTechnicalSetup] = useState(null);
  const [technicalPricePlan, setTechnicalPricePlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [structureLoading, setStructureLoading] = useState(true);
  const [zonesLoading, setZonesLoading] = useState(true);
  const [chartLoading, setChartLoading] = useState(true);
  const [liquidityLoading, setLiquidityLoading] = useState(true);
  const [confluenceLoading, setConfluenceLoading] = useState(true);
  const [decisionLoading, setDecisionLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(true);
  const [riskExposureLoading, setRiskExposureLoading] = useState(true);
  const [positionSizingLoading, setPositionSizingLoading] = useState(true);
  const [executionPlanLoading, setExecutionPlanLoading] = useState(true);
  const [stateMonitorLoading, setStateMonitorLoading] = useState(true);
  const [decisionSynthesisLoading, setDecisionSynthesisLoading] = useState(true);
  const [error, setError] = useState("");
  const [structureError, setStructureError] = useState("");
  const [zonesError, setZonesError] = useState("");
  const [chartError, setChartError] = useState("");
  const [liquidityError, setLiquidityError] = useState("");
  const [confluenceError, setConfluenceError] = useState("");
  const [decisionError, setDecisionError] = useState("");
  const [actionError, setActionError] = useState("");
  const [riskExposureError, setRiskExposureError] = useState("");
  const [positionSizingError, setPositionSizingError] = useState("");
  const [executionPlanError, setExecutionPlanError] = useState("");
  const [stateMonitorError, setStateMonitorError] = useState("");
  const [decisionSynthesisError, setDecisionSynthesisError] = useState("");

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

  useEffect(() => {
    const controller = new AbortController();

    async function loadActionFramework() {
      setActionLoading(true);
      setActionError("");

      try {
        const result = await getTechnicalActionFramework(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          token,
          signal: controller.signal
        });
        setActionFramework(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load technical action framework:", requestError);
          setActionFramework(null);
          setActionError(requestError?.message || "Unable to load QMI Technical Action Framework");
        }
      } finally {
        if (!controller.signal.aborted) setActionLoading(false);
      }
    }

    loadActionFramework();
    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadRiskExposure() {
      setRiskExposureLoading(true);
      setRiskExposureError("");

      try {
        const result = await getTechnicalRiskExposure(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          token,
          signal: controller.signal
        });
        setRiskExposure(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load technical risk exposure:", requestError);
          setRiskExposure(null);
          setRiskExposureError(
            requestError?.message || "Unable to load QMI Technical Risk & Exposure Gate"
          );
        }
      } finally {
        if (!controller.signal.aborted) setRiskExposureLoading(false);
      }
    }

    loadRiskExposure();
    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);


  useEffect(() => {
    const controller = new AbortController();

    async function loadPositionSizing() {
      setPositionSizingLoading(true);
      setPositionSizingError("");

      try {
        const result = await getTechnicalPositionSizing(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          token,
          signal: controller.signal
        });

        setPositionSizing(result);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load technical position sizing:", requestError);
          setPositionSizing(null);
          setPositionSizingError(
            requestError?.message ||
              "Unable to load QMI Technical Position Sizing & Capital Allocation"
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setPositionSizingLoading(false);
        }
      }
    }

    loadPositionSizing();

    return () => controller.abort();
  }, [submittedSymbol, period, interval, token]);


  useEffect(() => {
    const controller = new AbortController();

    async function loadUpperTechnicalSnapshot() {
      setExecutionPlanLoading(true);
      setStateMonitorLoading(true);
      setDecisionSynthesisLoading(true);
      setZonesLoading(true);

      setExecutionPlanError("");
      setStateMonitorError("");
      setDecisionSynthesisError("");
      setZonesError("");

      try {
        const snapshot = await getTechnicalUiSnapshot(submittedSymbol, {
          period,
          interval,
          pivotWindow: 3,
          historyLimit: 500,
          token,
          signal: controller.signal
        });

        setExecutionPlan(snapshot?.execution_plan || null);
        setStateTransition(snapshot?.state_transition || null);
        setStatePersistence(snapshot?.state_persistence || null);
        setRegimeMaturity(snapshot?.regime_maturity || null);
        setTransitionConfirmation(snapshot?.transition_confirmation || null);
        setDecisionSynthesis(snapshot?.decision_synthesis || null);
        setTechnicalSetup(snapshot?.technical_setup || null);
        setTechnicalPricePlan(snapshot?.technical_price_plan || null);
        setSupportResistance(snapshot?.support_resistance || null);
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error(
            "Unable to load shared technical UI snapshot:",
            requestError
          );

          setExecutionPlan(null);
          setStateTransition(null);
          setStatePersistence(null);
          setRegimeMaturity(null);
          setTransitionConfirmation(null);
          setDecisionSynthesis(null);
          setTechnicalSetup(null);
          setTechnicalPricePlan(null);
          setSupportResistance(null);

          const message =
            requestError?.message ||
            "Unable to load QMI shared technical UI snapshot";

          setExecutionPlanError(message);
          setStateMonitorError(message);
          setDecisionSynthesisError(message);
          setZonesError(message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setExecutionPlanLoading(false);
          setStateMonitorLoading(false);
          setDecisionSynthesisLoading(false);
          setZonesLoading(false);
        }
      }
    }

    loadUpperTechnicalSnapshot();
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


  const keyConfluenceContributions = confluenceContributions
    .filter((item) => {
      const engineName = String(item?.engine || "").trim().toUpperCase();

      // The backend's engine_contributions payload is the source of truth
      // for directional voting. Keep every available directional engine
      // and explicitly exclude volatility if it is ever added there later.
      return item?.available !== false && engineName !== "VOLATILITY";
    });

  const volatilityModifierValue =
    confluenceDiagnostics?.confidence?.volatility_modifier;

  const volatilityContext =
    technicalConfluence?.volatility_context || {};

  const volatilityConfidenceContribution =
    confluenceDiagnostics?.confidence?.volatility_component;


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

  const scenarioMatrix = useMemo(() => {
    const score = clamp(decisionScore, -100, 100);
    const confidence = clamp(
      decisionCore?.confidence ?? technicalDecision?.confidence ?? 0,
      0,
      100
    );
    const readiness = clamp(
      decisionReadiness?.score ??
        decisionReadiness?.readiness_score ??
        decisionCore?.readiness_score ??
        0,
      0,
      100
    );

    const bearish = clamp(50 + Math.max(0, -score) * 0.5, 0, 100);
    const bullish = clamp(50 + Math.max(0, score) * 0.5 - Math.max(0, -score) * 0.34, 0, 100);
    const stabilization = clamp(
      58 - Math.abs(score) * 0.11 + (100 - confidence) * 0.05,
      0,
      100
    );

    const scenarios = [
      {
        key: "bearish",
        label: "Bearish Continuation",
        score: bearish,
        tone: "negative",
        thesis: "Downside structure remains dominant while bearish confluence persists.",
        trigger: decisionBlockers.length
          ? "Bearish blockers remain active"
          : "Failure to reclaim nearby resistance",
        invalidation: reversalRequirements.length
          ? "Reversal requirements begin to validate"
          : "Sustained structural recovery"
      },
      {
        key: "stabilization",
        label: "Stabilization",
        score: stabilization,
        tone: "neutral",
        thesis: "Price compresses and directional pressure weakens without a confirmed reversal.",
        trigger: "Momentum and structure stop deteriorating",
        invalidation: "Fresh directional break with expanding conviction"
      },
      {
        key: "bullish",
        label: "Bullish Reversal",
        score: bullish,
        tone: "positive",
        thesis: "A reversal becomes credible only after structural and confluence confirmation.",
        trigger: reversalRequirements.length
          ? "Complete active reversal requirements"
          : "Bullish structure + positive confluence",
        invalidation: "Loss of reclaimed structure / renewed bearish expansion"
      }
    ].sort((a, b) => b.score - a.score);

    return {
      scenarios,
      primary: scenarios[0],
      confidence,
      readiness
    };
  }, [
    decisionScore,
    decisionCore,
    technicalDecision,
    decisionReadiness,
    decisionBlockers,
    reversalRequirements
  ]);

  const actionCore = actionFramework?.technical_action || actionFramework?.action_framework || {};
  const actionPosture = actionCore?.action_posture || actionCore?.posture || {};
  const actionPermission = actionCore?.technical_permission || actionCore?.permissions || {};
  const actionReadiness = actionCore?.action_readiness || actionCore?.readiness || {};
  const actionGates = Array.isArray(actionCore?.confirmation_gates) ? actionCore.confirmation_gates : [];
  const entryConstraints = Array.isArray(actionCore?.entry_constraints) ? actionCore.entry_constraints : [];
  const invalidationGates = Array.isArray(actionCore?.invalidation_gates) ? actionCore.invalidation_gates : [];
  const escalationConditions = Array.isArray(actionCore?.escalation_conditions)
    ? actionCore.escalation_conditions
    : Array.isArray(actionCore?.upgrade_conditions) ? actionCore.upgrade_conditions : [];
  const downgradeConditions = Array.isArray(actionCore?.downgrade_conditions) ? actionCore.downgrade_conditions : [];

  const actionState = actionPosture?.state || actionCore?.state || "--";
  const actionDirection = actionPosture?.direction || actionCore?.direction || "--";
  const actionSeverity = actionPosture?.severity ?? actionCore?.severity;
  const actionReadinessScore = actionReadiness?.score ?? actionReadiness?.readiness_score ?? actionCore?.readiness_score;
  const actionQuality = actionPermission?.quality_gate || actionReadiness?.quality_gate || actionCore?.quality_gate || actionReadiness?.state || "--";

  const actionText = (value) => {
    if (value === null || value === undefined || value === "") return "--";
    return String(value).replaceAll("_", " ");
  };

  const actionScore = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return null;
    return formatScore(value);
  };

  const riskCore = riskExposure?.technical_risk_exposure || riskExposure?.risk_exposure || {};
  const riskRegime = riskCore?.risk_regime || riskCore?.regime || {};
  const exposureGate = riskCore?.exposure_gate || riskCore?.exposure || {};
  const technicalBudget = riskCore?.technical_budget || riskCore?.risk_budget || {};
  const protectiveControls = Array.isArray(riskCore?.protective_controls)
    ? riskCore.protective_controls
    : Array.isArray(riskCore?.controls) ? riskCore.controls : [];
  const releaseConditions = Array.isArray(riskCore?.release_conditions)
    ? riskCore.release_conditions
    : Array.isArray(riskCore?.release_gates) ? riskCore.release_gates : [];
  const riskEscalationConditions = Array.isArray(riskCore?.escalation_conditions)
    ? riskCore.escalation_conditions
    : [];

  const riskState = riskRegime?.state || riskCore?.state || "--";
  const riskScore = riskRegime?.score ?? riskCore?.score;
  const riskDirection = riskRegime?.directional_state || riskRegime?.direction || riskCore?.directional_state || "--";
  const exposureState =
    exposureGate?.new_long_permission ||
    exposureGate?.state ||
    exposureGate?.exposure_state ||
    exposureGate?.new_long_exposure ||
    "--";
  const exposureBand = exposureGate?.new_long_technical_band || "--";

  const budgetState =
    technicalBudget?.technical_gross_exposure_band ||
    technicalBudget?.state ||
    technicalBudget?.budget_state ||
    technicalBudget?.level ||
    "--";
  const budgetPriority = technicalBudget?.capital_preservation_priority || "--";

  const riskItemText = (item, fallback = "--") => {
    if (typeof item === "string") return actionText(item);
    return actionText(item?.condition || item?.control || item?.label || item?.name || item?.requirement || fallback);
  };

  const sizingCore =
    positionSizing?.technical_position_sizing ||
    positionSizing?.position_sizing ||
    {};

  const allocationRegime = sizingCore?.allocation_regime || {};
  const maximumExposure = sizingCore?.maximum_technical_exposure || {};
  const newEntryAllocation = sizingCore?.new_entry_allocation || {};
  const addOnCapacity = sizingCore?.add_on_capacity || {};
  const reductionPolicy = sizingCore?.risk_reduction || {};
  const cashPreference = sizingCore?.cash_preference || {};
  const sizingConfidence = sizingCore?.sizing_confidence || {};
  const sizingContext = sizingCore?.source_context || {};

  const allocationState = allocationRegime?.state || "--";
  const allocationPriority = allocationRegime?.priority || "--";
  const maxExposureBand = maximumExposure?.band || "--";
  const maxExposurePriority =
    maximumExposure?.capital_preservation_priority || "--";
  const newEntryState = newEntryAllocation?.state || "--";
  const newEntryBand = newEntryAllocation?.technical_band || "--";
  const addOnState = addOnCapacity?.state || "--";
  const addOnBand = addOnCapacity?.technical_band || "--";
  const reductionPermission = reductionPolicy?.permission || "--";
  const reductionPreference = reductionPolicy?.preference || "--";
  const cashState = cashPreference?.state || "--";
  const leverageState = sizingCore?.leverage || "--";
  const sizingConfidenceScore = sizingConfidence?.score;
  const sizingConfidenceState = sizingConfidence?.state || "--";

  const executionCore =
    executionPlan?.technical_execution_plan ||
    executionPlan?.execution_plan ||
    {};

  const executionState = executionCore?.execution_state || {};
  const actionMatrix = executionCore?.action_matrix || {};
  const allocationContext = executionCore?.allocation_context || {};
  const activationConditions = Array.isArray(executionCore?.activation_conditions)
    ? executionCore.activation_conditions
    : [];
  const executionInvalidations = Array.isArray(executionCore?.invalidation_conditions)
    ? executionCore.invalidation_conditions
    : [];
  const executionEscalation = Array.isArray(executionCore?.escalation_path)
    ? executionCore.escalation_path
    : [];
  const executionDeescalation = Array.isArray(executionCore?.deescalation_path)
    ? executionCore.deescalation_path
    : [];
  const executionConfidence = executionCore?.execution_confidence || {};
  const executionContext = executionCore?.source_context || {};

  const executionStateName = executionState?.state || "--";
  const executionBias = executionState?.bias || "--";
  const executionRiskState = executionState?.risk_state || "--";

  const waitAction = actionMatrix?.WAIT || {};
  const enterAction = actionMatrix?.ENTER || {};
  const addAction = actionMatrix?.ADD || {};
  const reduceAction = actionMatrix?.REDUCE || {};
  const exitAction = actionMatrix?.EXIT || {};

  const transitionCore = stateTransition?.technical_state_transition || {};
  const persistenceCore = statePersistence?.state_persistence || {};
  const maturityCore = regimeMaturity?.regime_maturity || {};
  const confirmationCore = transitionConfirmation?.transition_confirmation || {};
  const currentTransitionState = transitionCore?.current_state || {};
  const nextTransitionState = transitionCore?.next_state_candidate || {};
  const transitionReadiness014 = transitionCore?.transition_readiness || {};
  const persistenceCurrent = persistenceCore?.current_state || {};
  const persistenceStrength014 = persistenceCore?.persistence_strength || {};
  const regimeStability014 = persistenceCore?.regime_stability || {};
  const maturityCurrent014 = maturityCore?.current_regime || {};
  const maturityAssessment014 = maturityCore?.transition_assessment || {};
  const confirmationDecision014 = confirmationCore?.decision || "--";
  const confirmationScore014 = confirmationCore?.confirmation_score;
  const confirmationBlockers014 = Array.isArray(confirmationCore?.blockers) ? confirmationCore.blockers : [];
  const stateCurrentName014 = currentTransitionState?.state || maturityCurrent014?.state || "--";
  const stateNextName014 = maturityAssessment014?.target_state || nextTransitionState?.state || "--";
  const transitionProbability014 = maturityAssessment014?.transition_probability ?? nextTransitionState?.probability;
  const maturityPhase014 = maturityCurrent014?.maturity_phase || persistenceStrength014?.maturity || "--";
  const persistenceScore014 = maturityCurrent014?.persistence_score ?? persistenceStrength014?.score;
  const readinessScore014 = maturityAssessment014?.transition_readiness ?? transitionReadiness014?.score;
  const consecutive014 = maturityCurrent014?.consecutive_snapshots ?? persistenceCurrent?.consecutive_snapshots ?? 0;

  const synthesisCore =
    decisionSynthesis?.technical_decision_synthesis ||
    decisionSynthesis?.decision_synthesis ||
    {};

  const synthesisTransition = synthesisCore?.transition || {};
  const synthesisMarketContext = synthesisCore?.market_context || {};
  const synthesisTrace = synthesisCore?.decision_trace || {};
  const synthesisPermissions =
    synthesisTrace?.action_permissions ||
    synthesisCore?.action_permissions ||
    {};
  const synthesisBlockers = Array.isArray(synthesisCore?.blockers)
    ? synthesisCore.blockers
    : [];

  const synthesisPosture =
    synthesisCore?.final_posture ||
    synthesisTrace?.final_posture ||
    "--";
  const synthesisConviction =
    synthesisCore?.conviction ??
    synthesisCore?.conviction_score;
  const synthesisTiming = synthesisCore?.timing || "--";
  const synthesisRisk =
    synthesisCore?.risk_state ||
    synthesisCore?.risk ||
    "--";
  const synthesisExecutionState =
    synthesisCore?.execution_state ||
    synthesisTransition?.execution_state ||
    "--";
  const synthesisCurrentState =
    synthesisTransition?.current_state ||
    synthesisCore?.current_state ||
    "--";
  const synthesisTargetState =
    synthesisTransition?.target_state ||
    synthesisTransition?.next_state ||
    synthesisCore?.target_state ||
    "--";
  const synthesisScenario =
    synthesisMarketContext?.primary_scenario ||
    synthesisCore?.primary_scenario ||
    "--";
  const synthesisDirection =
    synthesisMarketContext?.direction_score ??
    synthesisCore?.direction_score;
  const synthesisExecutionConfidence =
    synthesisMarketContext?.execution_confidence ??
    synthesisCore?.execution_confidence;
  const synthesisRationale = synthesisCore?.rationale || "";
  const synthesisBlockerCount =
    synthesisTrace?.blocker_count ??
    synthesisCore?.blocker_count ??
    synthesisBlockers.length;

  const synthesisPermission = (key) => {
    const value =
      synthesisPermissions?.[key] ??
      synthesisPermissions?.[String(key).toUpperCase()] ??
      "--";
    return typeof value === "object"
      ? value?.state || value?.permission || value?.status || "--"
      : value;
  };

  const synthesisToneClass = (value) => {
    const normalized = String(value || "").toUpperCase();
    if (["PERMITTED", "PRIMARY", "BUY", "ENTER", "REDUCE"].includes(normalized)) return "is-positive";
    if (["BLOCKED", "PROHIBITED", "HIGH", "HARD_BLOCK"].includes(normalized)) return "is-negative";
    if (["WATCH", "CONDITIONAL", "EARLY", "WAIT"].includes(normalized)) return "is-watch";
    return "";
  };


  const setup016 =
    technicalSetup?.technical_setup ||
    {};
  const setupQualification016 = setup016?.qualification || {};
  const setupContext016 = setup016?.context || {};
  const setupGates016 = setup016?.gates || {};

  const pricePlan016 =
    technicalPricePlan?.technical_price_plan ||
    {};
  const priceTrigger016 = pricePlan016?.trigger || {};
  const priceEntryZone016 = pricePlan016?.entry_zone || {};
  const priceRR016 = pricePlan016?.risk_reward || {};

  const setupStatus016 = setup016?.setup_status || "--";
  const setupQuality016 = setup016?.setup_quality;
  const setupType016 = setup016?.setup_type || "--";
  const setupDirection016 = setup016?.direction || "--";
  const setupTiming016 = setup016?.timing || "--";
  const setupScenario016 = setupContext016?.primary_scenario || "--";

  const priceAuthorization016 = pricePlan016?.authorization || "--";
  const priceCurrent016 = pricePlan016?.current_price;
  const priceInvalidation016 = pricePlan016?.invalidation;
  const priceTarget1016 = pricePlan016?.primary_target;
  const priceTarget2016 = pricePlan016?.secondary_target;

  const formatPrice016 = (value) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
    return `$${Number(value).toFixed(4)}`;
  };

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


        /* =========================================================
           QMI TECHNICAL — TOP COMPACT COMMAND HEADER
           Applies only while Technical.jsx is mounted.
           ========================================================= */
        .page-shell > .page-intro {
          min-height: 58px !important;
          padding: 9px 14px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          gap: 16px !important;
          border: 1px solid rgba(148, 163, 184, 0.16) !important;
          border-radius: 12px !important;
          background: rgba(10, 16, 27, 0.88) !important;
          box-shadow: 0 10px 28px rgba(2, 6, 23, 0.08) !important;
        }

        .page-shell > .page-intro > div:first-child::before {
          content: "QUANTUM MARKET INTELLIGENCE";
          display: block;
          margin-bottom: 2px;
          color: #5b8cff;
          font-size: 10px;
          line-height: 1;
          font-weight: 950;
          letter-spacing: .08em;
        }

        .page-shell > .page-intro h2 {
          margin: 0 !important;
          font-size: 0 !important;
          line-height: 1 !important;
        }

        .page-shell > .page-intro h2::after {
          content: "Technical Command Center";
          color: #f4f7fb;
          font-size: 18px;
          line-height: 1.1;
          font-weight: 950;
          letter-spacing: -.02em;
        }

        .page-shell > .page-intro p {
          display: none !important;
        }

        /* =========================================================
           MARKET REGIME + TECHNICAL DECISION — 50 / 50
           ========================================================= */
        .qmi-ta-primary-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
        }

        .qmi-ta-primary-grid > section {
          min-width: 0;
          height: 100%;
        }

        .qmi-ta-primary-grid .qmi-ta-regime-panel {
          padding: 18px;
          display: flex;
          flex-direction: column;
          gap: 14px;
        }

        .qmi-ta-primary-grid .qmi-ta-regime-panel > div:first-child {
          min-height: 104px;
          display: flex;
          flex-direction: column;
          justify-content: center;
        }

        .qmi-ta-primary-grid .qmi-ta-regime-name {
          font-size: clamp(38px, 4vw, 54px);
          margin: 5px 0;
        }

        .qmi-ta-primary-grid .qmi-ta-context-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
          margin-top: auto;
        }

        .qmi-ta-primary-grid .qmi-ta-context {
          padding: 11px 12px;
        }

        .qmi-ta-primary-grid .qmi-ta-context span {
          font-size: 11px;
          margin-bottom: 5px;
        }

        .qmi-ta-primary-grid .qmi-ta-context strong {
          font-size: 18px;
        }

        .qmi-ta-primary-grid .qmi-synthesis {
          padding: 18px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__header {
          margin-bottom: 11px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__title h2 {
          font-size: 20px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__badge {
          min-width: 108px;
          padding: 7px 10px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__hero {
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 7px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__card {
          padding: 10px 11px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__card span {
          margin-bottom: 5px;
          font-size: 10px !important;
        }

        .qmi-ta-primary-grid .qmi-synthesis__card strong {
          font-size: 14px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__card.is-posture strong {
          font-size: 17px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__card small {
          margin-top: 4px;
          font-size: 10px !important;
        }

        .qmi-ta-primary-grid .qmi-synthesis__permissions {
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 6px;
          margin-top: 7px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__permission {
          padding: 8px 9px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__permission span {
          margin-bottom: 3px;
          font-size: 9px !important;
        }

        .qmi-ta-primary-grid .qmi-synthesis__permission strong {
          font-size: 11px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__footer {
          grid-template-columns: 1fr;
          gap: 6px;
          margin-top: 7px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__strip {
          padding: 8px 10px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__rationale {
          margin-top: 5px;
          font-size: 10px !important;
          line-height: 1.35;
        }

        .qmi-ta-primary-grid .qmi-synthesis__blockers {
          margin-top: 5px;
        }

        .qmi-ta-primary-grid .qmi-synthesis__blocker {
          padding: 4px 6px;
          font-size: 9px;
        }

        @media (max-width: 1180px) {
          .qmi-ta-primary-grid {
            grid-template-columns: 1fr;
          }
        }

        /* DE-UI readability pass — compact layout, higher legibility */
        .qmi-confluence__engine small,
        .qmi-confluence__engine-foot,
        .qmi-synthesis__card span,
        .qmi-synthesis__card small,
        .qmi-synthesis__permission span,
        .qmi-synthesis__rationale,
        .qmi-opportunity__card span,
        .qmi-opportunity__card small,
        .qmi-opportunity__meta,
        .qmi-opportunity__note {
          font-size: 12px !important;
          line-height: 1.45;
          opacity: 0.82 !important;
        }

        .qmi-confluence__engine-foot {
          color: #9eabbc;
        }

        .qmi-confluence__engine small {
          color: #9aa7b9;
        }

        .qmi-ta-detail-panel,
        .qmi-synthesis,
        .qmi-opportunity {
          font-size: 14px;
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
          font-size: 13px;
          letter-spacing: 0.14em;
          font-weight: 900;
          opacity: 0.78;
        }

        .qmi-ta-regime-sub {
          opacity: 0.82;
          font-size: 14px;
          line-height: 1.45;
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
          font-size: 13px;
          opacity: 0.80;
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
          font-size: 11px;
          opacity: 0.68;
          margin-bottom: 6px;
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
          color: #9aa7b9;
          font-size: 11px;
          font-weight: 900;
          letter-spacing: 0.10em;
        }

        .qmi-ichart__header > div:first-child strong {
          display: block;
          margin-top: 3px;
          font-size: 13px;
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
          color: #b1bdcc;
          font-family: var(--font-family-mono, monospace);
          font-size: 11px;
          font-weight: 800;
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
          min-height: 27px;
          padding: 4px 9px;
          color: #8f9caf;
          background: rgba(148, 163, 184, 0.04);
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 6px;
          font-size: 10px;
          font-weight: 850;
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
          fill: #8995a6;
          font-family: var(--font-family-mono, monospace);
          font-size: 11px;
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


        /* DE-UI-009.0 — Technical Scenario Matrix */
        .qmi-scenario {
          padding: 22px;
          background: var(--panel-bg, rgba(15, 23, 42, 0.78));
          border: 1px solid var(--border, rgba(148, 163, 184, 0.16));
          border-radius: 16px;
          box-shadow: 0 16px 38px rgba(2, 6, 23, 0.10);
        }
        .qmi-scenario__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:16px; }
        .qmi-scenario__title { display:flex; align-items:center; gap:12px; }
        .qmi-scenario__title h2 { margin:3px 0 0; font-size:24px; font-weight:950; letter-spacing:-.03em; }
        .qmi-scenario__primary { min-width:150px; padding:10px 13px; border-radius:10px; border:1px solid rgba(78,161,255,.24); background:rgba(78,161,255,.07); text-align:center; }
        .qmi-scenario__primary span { display:block; color:#7f8da3; font-size:9px; font-weight:900; letter-spacing:.08em; text-transform:uppercase; }
        .qmi-scenario__primary strong { display:block; margin-top:4px; font-size:13px; font-weight:950; }
        .qmi-scenario__grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
        .qmi-scenario__card { min-width:0; padding:16px; border:1px solid rgba(148,163,184,.13); border-radius:12px; background:rgba(148,163,184,.035); }
        .qmi-scenario__card.is-primary { border-color:rgba(78,161,255,.30); box-shadow:inset 0 0 0 1px rgba(78,161,255,.08); }
        .qmi-scenario__card-head { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
        .qmi-scenario__card-head span { color:#7f8da3; font-size:10px; font-weight:900; letter-spacing:.05em; text-transform:uppercase; }
        .qmi-scenario__card-head strong { font-size:26px; font-weight:1000; letter-spacing:-.04em; }
        .qmi-scenario__card.is-negative .qmi-scenario__card-head strong { color:#ff6178; }
        .qmi-scenario__card.is-neutral .qmi-scenario__card-head strong { color:#f4c542; }
        .qmi-scenario__card.is-positive .qmi-scenario__card-head strong { color:#31d890; }
        .qmi-scenario__bar { height:5px; margin:12px 0; overflow:hidden; border-radius:999px; background:rgba(148,163,184,.13); }
        .qmi-scenario__bar > div { height:100%; border-radius:inherit; background:currentColor; }
        .qmi-scenario__card.is-negative { color:#ff6178; }
        .qmi-scenario__card.is-neutral { color:#f4c542; }
        .qmi-scenario__card.is-positive { color:#31d890; }
        .qmi-scenario__thesis { min-height:42px; color:var(--text,#f8fafc); font-size:11px; line-height:1.55; opacity:.72; }
        .qmi-scenario__facts { display:grid; gap:8px; margin-top:12px; padding-top:11px; border-top:1px solid rgba(148,163,184,.10); }
        .qmi-scenario__fact span { display:block; margin-bottom:3px; color:#7f8da3; font-size:9px; font-weight:850; letter-spacing:.05em; text-transform:uppercase; }
        .qmi-scenario__fact strong { display:block; color:var(--text,#f8fafc); font-size:10px; line-height:1.45; font-weight:800; }
        .qmi-scenario__footer { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-scenario__footer > div { padding:11px 13px; border:1px solid rgba(148,163,184,.10); border-radius:10px; background:rgba(2,6,23,.12); }
        .qmi-scenario__footer span { display:block; color:#7f8da3; font-size:9px; font-weight:850; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-scenario__footer strong { display:block; margin-top:4px; font-size:12px; font-weight:900; }
        @media (max-width: 900px) { .qmi-scenario__grid, .qmi-scenario__footer { grid-template-columns:1fr; } }
        @media (max-width: 760px) { .qmi-scenario__header { flex-direction:column; } }

        /* DE-UI-010.0 — Technical Action Framework */
        .qmi-action { padding:22px; background:var(--panel-bg,rgba(15,23,42,.78)); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 16px 38px rgba(2,6,23,.10); }
        .qmi-action__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:16px; }
        .qmi-action__title { display:flex; align-items:center; gap:12px; }
        .qmi-action__title h2 { margin:3px 0 0; font-size:24px; font-weight:950; letter-spacing:-.03em; }
        .qmi-action__badge { min-width:170px; padding:10px 14px; border:1px solid rgba(255,97,120,.30); border-radius:10px; background:rgba(255,97,120,.07); color:#ff6178; text-align:center; font-size:13px; font-weight:950; }
        .qmi-action__hero { display:grid; grid-template-columns:1.25fr repeat(2,minmax(0,1fr)); gap:10px; }
        .qmi-action__card { min-width:0; padding:16px; border:1px solid rgba(148,163,184,.13); border-radius:12px; background:rgba(148,163,184,.035); }
        .qmi-action__card span, .qmi-action__list span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:11px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-action__card strong { display:block; font-size:22px; font-weight:950; overflow-wrap:anywhere; }
        .qmi-action__card.is-posture strong { color:#ff6178; font-size:29px; letter-spacing:-.035em; }
        .qmi-action__card small { display:block; margin-top:7px; color:#a7b3c4; font-size:12px; line-height:1.5; font-weight:700; }
        .qmi-action__permissions { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-action__permission { padding:14px; border:1px solid rgba(148,163,184,.12); border-radius:11px; background:rgba(2,6,23,.13); }
        .qmi-action__permission span { display:block; color:#8b9ab0; font-size:10px; font-weight:900; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-action__permission strong { display:block; margin-top:6px; font-size:14px; font-weight:950; }
        .qmi-action__permission.is-blocked strong { color:#ff6178; } .qmi-action__permission.is-permitted strong { color:#31d890; } .qmi-action__permission.is-preferred strong { color:#f4c542; }
        .qmi-action__lists { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-action__list { padding:14px; border:1px solid rgba(148,163,184,.10); border-radius:11px; background:rgba(148,163,184,.025); min-width:0; }
        .qmi-action__items { display:grid; gap:8px; }
        .qmi-action__item { padding:9px 10px; border:1px solid rgba(148,163,184,.09); border-radius:8px; background:rgba(2,6,23,.16); }
        .qmi-action__item-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
        .qmi-action__item-head strong { color:var(--text,#f8fafc); font-size:13px; line-height:1.35; font-weight:900; overflow-wrap:anywhere; }
        .qmi-action__item-head em { flex-shrink:0; color:#91a0b6; font-style:normal; font-size:11px; font-weight:850; }
        .qmi-action__item small { display:block; margin-top:5px; color:#9eabbc; font-size:12px; line-height:1.5; font-weight:650; overflow-wrap:anywhere; }
        .qmi-action__item-meta { display:flex; flex-wrap:wrap; gap:7px; margin-top:6px; }
        .qmi-action__item-meta b { padding:3px 6px; border-radius:6px; background:rgba(148,163,184,.06); color:#91a0b6; font-size:10px; font-weight:850; }
        .qmi-action__transition-group + .qmi-action__transition-group { margin-top:10px; padding-top:10px; border-top:1px solid rgba(148,163,184,.09); }
        .qmi-action__transition-title { display:block; margin-bottom:7px; color:#91a0b6; font-size:10px; font-weight:900; letter-spacing:.05em; text-transform:uppercase; }
        @media (min-width:1400px) {
          .qmi-action__item-head strong { font-size:14px; }
          .qmi-action__item small { font-size:13px; }
          .qmi-action__item-meta b { font-size:11px; }
        }
        @media (max-width:1100px) { .qmi-action__hero,.qmi-action__permissions,.qmi-action__lists { grid-template-columns:repeat(2,minmax(0,1fr)); } }
        @media (max-width:760px) { .qmi-action__header { flex-direction:column; } .qmi-action__hero,.qmi-action__permissions,.qmi-action__lists { grid-template-columns:1fr; } }

        /* DE-UI-011.0 — Technical Risk & Exposure Gate */
        .qmi-state-monitor { padding:20px; background:var(--panel-bg,rgba(15,23,42,.78)); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 16px 38px rgba(2,6,23,.10); }
        .qmi-state-monitor__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:14px; }
        .qmi-state-monitor__title { display:flex; align-items:center; gap:12px; }
        .qmi-state-monitor__title h2 { margin:3px 0 0; font-size:23px; font-weight:950; letter-spacing:-.03em; }
        .qmi-state-monitor__badge { min-width:150px; padding:9px 13px; border:1px solid rgba(96,165,250,.30); border-radius:10px; background:rgba(96,165,250,.07); color:#60a5fa; text-align:center; font-size:12px; font-weight:950; }
        .qmi-state-monitor__flow { display:grid; grid-template-columns:1.2fr auto 1.2fr repeat(4,minmax(0,1fr)); gap:9px; align-items:stretch; }
        .qmi-state-monitor__arrow { display:flex; align-items:center; justify-content:center; color:#708198; font-size:20px; font-weight:900; }
        .qmi-state-monitor__card { min-width:0; padding:14px; border:1px solid rgba(148,163,184,.12); border-radius:11px; background:rgba(148,163,184,.03); }
        .qmi-state-monitor__card span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:10px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-state-monitor__card strong { display:block; color:var(--text,#f8fafc); font-size:18px; line-height:1.25; font-weight:950; overflow-wrap:anywhere; }
        .qmi-state-monitor__card small { display:block; margin-top:6px; color:#9eabbc; font-size:11px; line-height:1.45; font-weight:700; }
        .qmi-state-monitor__card.is-current strong { color:#ff6178; }
        .qmi-state-monitor__card.is-next strong { color:#60a5fa; }
        .qmi-state-monitor__card.is-confirm strong { color:#f4c542; }
        .qmi-state-monitor__footer { display:grid; grid-template-columns:1.2fr 2fr; gap:9px; margin-top:9px; }
        .qmi-state-monitor__strip { padding:11px 13px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.14); }
        .qmi-state-monitor__strip span { color:#8b9ab0; font-size:10px; font-weight:900; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-state-monitor__strip strong { margin-left:8px; color:var(--text,#f8fafc); font-size:12px; font-weight:900; }
        .qmi-state-monitor__blockers { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
        .qmi-state-monitor__blocker { padding:5px 7px; border-radius:7px; background:rgba(255,97,120,.06); border:1px solid rgba(255,97,120,.12); color:#ff8798; font-size:10px; font-weight:800; }
        @media (max-width:1200px) { .qmi-state-monitor__flow { grid-template-columns:repeat(3,minmax(0,1fr)); } .qmi-state-monitor__arrow { display:none; } }
        @media (max-width:760px) { .qmi-state-monitor__header { flex-direction:column; } .qmi-state-monitor__flow,.qmi-state-monitor__footer { grid-template-columns:1fr; } }


        /* DE-UI-015.0 — Technical Decision Synthesis */
        .qmi-synthesis { padding:20px; background:linear-gradient(135deg,rgba(37,99,235,.055),rgba(15,23,42,.78) 42%); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 16px 38px rgba(2,6,23,.10); }
        .qmi-synthesis__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:14px; }
        .qmi-synthesis__title { display:flex; align-items:center; gap:12px; }
        .qmi-synthesis__title h2 { margin:3px 0 0; font-size:23px; font-weight:950; letter-spacing:-.03em; }
        .qmi-synthesis__badge { min-width:150px; padding:9px 13px; border:1px solid rgba(244,197,66,.30); border-radius:10px; background:rgba(244,197,66,.07); color:#f4c542; text-align:center; font-size:12px; font-weight:950; }
        .qmi-synthesis__hero { display:grid; grid-template-columns:1.25fr 1.25fr repeat(4,minmax(0,1fr)); gap:9px; }
        .qmi-synthesis__card { min-width:0; padding:14px; border:1px solid rgba(148,163,184,.12); border-radius:11px; background:rgba(148,163,184,.03); }
        .qmi-synthesis__card span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:10px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-synthesis__card strong { display:block; color:var(--text,#f8fafc); font-size:17px; line-height:1.25; font-weight:950; overflow-wrap:anywhere; }
        .qmi-synthesis__card small { display:block; margin-top:6px; color:#9eabbc; font-size:11px; line-height:1.4; font-weight:700; }
        .qmi-synthesis__card.is-posture strong { color:#f4c542; font-size:20px; }
        .qmi-synthesis__transition { color:#60a5fa !important; }
        .qmi-synthesis__permissions { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:9px; margin-top:9px; }
        .qmi-synthesis__permission { padding:11px 13px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.14); }
        .qmi-synthesis__permission span { display:block; margin-bottom:5px; color:#8b9ab0; font-size:10px; font-weight:900; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-synthesis__permission strong { font-size:12px; font-weight:950; }
        .qmi-synthesis__permission.is-positive strong { color:#5ee35a; }
        .qmi-synthesis__permission.is-negative strong { color:#ff6178; }
        .qmi-synthesis__permission.is-watch strong { color:#f4c542; }
        .qmi-synthesis__footer { display:grid; grid-template-columns:1.2fr 2fr; gap:9px; margin-top:9px; }
        .qmi-synthesis__strip { padding:11px 13px; border:1px solid rgba(148,163,184,.10); border-radius:9px; background:rgba(2,6,23,.14); min-width:0; }
        .qmi-synthesis__strip > span { color:#8b9ab0; font-size:10px; font-weight:900; text-transform:uppercase; letter-spacing:.05em; }
        .qmi-synthesis__strip > strong { margin-left:8px; color:var(--text,#f8fafc); font-size:12px; font-weight:900; }
        .qmi-synthesis__rationale { margin-top:7px; color:#aab6c7; font-size:11px; line-height:1.5; font-weight:700; }
        .qmi-synthesis__blockers { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
        .qmi-synthesis__blocker { padding:5px 7px; border-radius:7px; background:rgba(255,97,120,.06); border:1px solid rgba(255,97,120,.12); color:#ff8798; font-size:10px; font-weight:800; }
        @media (max-width:1200px) { .qmi-synthesis__hero { grid-template-columns:repeat(3,minmax(0,1fr)); } .qmi-synthesis__permissions { grid-template-columns:repeat(3,minmax(0,1fr)); } }
        @media (max-width:760px) { .qmi-synthesis__header { flex-direction:column; } .qmi-synthesis__hero,.qmi-synthesis__permissions,.qmi-synthesis__footer { grid-template-columns:1fr; } }

        .qmi-execution { padding:22px; background:var(--panel-bg,rgba(15,23,42,.78)); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 18px 42px rgba(2,6,23,.11); }
        .qmi-execution__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:16px; }
        .qmi-execution__title { display:flex; align-items:center; gap:12px; }
        .qmi-execution__title h2 { margin:3px 0 0; font-size:24px; font-weight:950; letter-spacing:-.03em; }
        .qmi-execution__badge { min-width:180px; padding:10px 14px; border:1px solid rgba(255,97,120,.30); border-radius:10px; background:rgba(255,97,120,.07); color:#ff6178; text-align:center; font-size:13px; font-weight:950; }
        .qmi-execution__hero { display:grid; grid-template-columns:1.3fr repeat(5,minmax(0,1fr)); gap:10px; }
        .qmi-execution__card { min-width:0; padding:15px; border:1px solid rgba(148,163,184,.13); border-radius:12px; background:rgba(148,163,184,.035); }
        .qmi-execution__card span,.qmi-execution__panel > span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:11px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-execution__card strong { display:block; font-size:19px; font-weight:950; overflow-wrap:anywhere; }
        .qmi-execution__card small { display:block; margin-top:7px; color:#a7b3c4; font-size:12px; line-height:1.5; font-weight:700; }
        .qmi-execution__card.is-state strong { color:#ff6178; font-size:24px; }
        .qmi-execution__card.is-wait strong { color:#f4c542; }
        .qmi-execution__card.is-enter strong,.qmi-execution__card.is-add strong { color:#ff6178; }
        .qmi-execution__card.is-reduce strong { color:#31d890; }
        .qmi-execution__grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-execution__panel { min-width:0; padding:14px; border:1px solid rgba(148,163,184,.10); border-radius:11px; background:rgba(148,163,184,.025); }
        .qmi-execution__items { display:grid; gap:8px; }
        .qmi-execution__item { padding:10px; border:1px solid rgba(148,163,184,.09); border-radius:8px; background:rgba(2,6,23,.16); }
        .qmi-execution__item strong { display:block; color:var(--text,#f8fafc); font-size:13px; line-height:1.45; font-weight:900; overflow-wrap:anywhere; }
        .qmi-execution__item small { display:block; margin-top:5px; color:#9eabbc; font-size:12px; line-height:1.5; font-weight:650; overflow-wrap:anywhere; }
        .qmi-execution__meta { display:flex; flex-wrap:wrap; gap:7px; margin-top:7px; }
        .qmi-execution__meta b { padding:3px 6px; border-radius:6px; background:rgba(148,163,184,.06); color:#91a0b6; font-size:10px; font-weight:850; }
        @media (min-width:1400px) { .qmi-execution__item strong { font-size:14px; } .qmi-execution__item small { font-size:13px; } }
        @media (max-width:1200px) { .qmi-execution__hero { grid-template-columns:repeat(3,minmax(0,1fr)); } .qmi-execution__grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
        @media (max-width:760px) { .qmi-execution__header { flex-direction:column; } .qmi-execution__hero,.qmi-execution__grid { grid-template-columns:1fr; } }

        .qmi-sizing { padding:22px; background:var(--panel-bg,rgba(15,23,42,.78)); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 16px 38px rgba(2,6,23,.10); }
        .qmi-sizing__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:16px; }
        .qmi-sizing__title { display:flex; align-items:center; gap:12px; }
        .qmi-sizing__title h2 { margin:3px 0 0; font-size:24px; font-weight:950; letter-spacing:-.03em; }
        .qmi-sizing__badge { min-width:180px; padding:10px 14px; border:1px solid rgba(244,197,66,.30); border-radius:10px; background:rgba(244,197,66,.07); color:#f4c542; text-align:center; font-size:13px; font-weight:950; }
        .qmi-sizing__hero { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px; }
        .qmi-sizing__card { min-width:0; padding:16px; border:1px solid rgba(148,163,184,.13); border-radius:12px; background:rgba(148,163,184,.035); }
        .qmi-sizing__card span,.qmi-sizing__panel > span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:11px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-sizing__card strong { display:block; font-size:22px; font-weight:950; overflow-wrap:anywhere; }
        .qmi-sizing__card small { display:block; margin-top:7px; color:#a7b3c4; font-size:12px; line-height:1.5; font-weight:700; }
        .qmi-sizing__card.is-allocation strong { color:#f4c542; font-size:24px; }
        .qmi-sizing__grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-sizing__panel { min-width:0; padding:14px; border:1px solid rgba(148,163,184,.10); border-radius:11px; background:rgba(148,163,184,.025); }
        .qmi-sizing__items { display:grid; gap:8px; }
        .qmi-sizing__item { padding:10px; border:1px solid rgba(148,163,184,.09); border-radius:8px; background:rgba(2,6,23,.16); }
        .qmi-sizing__item strong { display:block; color:var(--text,#f8fafc); font-size:13px; line-height:1.4; font-weight:900; overflow-wrap:anywhere; }
        .qmi-sizing__item small { display:block; margin-top:5px; color:#9eabbc; font-size:12px; line-height:1.5; font-weight:650; overflow-wrap:anywhere; }
        .qmi-sizing__meta { display:flex; flex-wrap:wrap; gap:7px; margin-top:7px; }
        .qmi-sizing__meta b { padding:3px 6px; border-radius:6px; background:rgba(148,163,184,.06); color:#91a0b6; font-size:10px; font-weight:850; }
        @media (min-width:1400px) { .qmi-sizing__item strong { font-size:14px; } .qmi-sizing__item small { font-size:13px; } }
        @media (max-width:1100px) { .qmi-sizing__hero { grid-template-columns:repeat(2,minmax(0,1fr)); } .qmi-sizing__grid { grid-template-columns:1fr; } }
        @media (max-width:760px) { .qmi-sizing__header { flex-direction:column; } .qmi-sizing__hero { grid-template-columns:1fr; } }

        .qmi-risk { padding:22px; background:var(--panel-bg,rgba(15,23,42,.78)); border:1px solid var(--border,rgba(148,163,184,.16)); border-radius:16px; box-shadow:0 16px 38px rgba(2,6,23,.10); }
        .qmi-risk__header { display:flex; align-items:flex-start; justify-content:space-between; gap:18px; margin-bottom:16px; }
        .qmi-risk__title { display:flex; align-items:center; gap:12px; }
        .qmi-risk__title h2 { margin:3px 0 0; font-size:24px; font-weight:950; letter-spacing:-.03em; }
        .qmi-risk__badge { min-width:150px; padding:10px 14px; border:1px solid rgba(255,97,120,.30); border-radius:10px; background:rgba(255,97,120,.07); color:#ff6178; text-align:center; font-size:13px; font-weight:950; }
        .qmi-risk__hero { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; }
        .qmi-risk__card { min-width:0; padding:16px; border:1px solid rgba(148,163,184,.13); border-radius:12px; background:rgba(148,163,184,.035); }
        .qmi-risk__card span,.qmi-risk__panel > span { display:block; margin-bottom:7px; color:#8b9ab0; font-size:11px; font-weight:900; letter-spacing:.055em; text-transform:uppercase; }
        .qmi-risk__card strong { display:block; font-size:22px; font-weight:950; overflow-wrap:anywhere; }
        .qmi-risk__card.is-risk strong { color:#ff6178; font-size:29px; letter-spacing:-.035em; }
        .qmi-risk__card small { display:block; margin-top:7px; color:#a7b3c4; font-size:12px; line-height:1.5; font-weight:700; }
        .qmi-risk__grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:10px; }
        .qmi-risk__panel { min-width:0; padding:14px; border:1px solid rgba(148,163,184,.10); border-radius:11px; background:rgba(148,163,184,.025); }
        .qmi-risk__items { display:grid; gap:8px; }
        .qmi-risk__item { padding:10px; border:1px solid rgba(148,163,184,.09); border-radius:8px; background:rgba(2,6,23,.16); }
        .qmi-risk__item strong { display:block; color:var(--text,#f8fafc); font-size:13px; line-height:1.4; font-weight:900; overflow-wrap:anywhere; }
        .qmi-risk__item small { display:block; margin-top:5px; color:#9eabbc; font-size:12px; line-height:1.5; font-weight:650; overflow-wrap:anywhere; }
        .qmi-risk__meta { display:flex; flex-wrap:wrap; gap:7px; margin-top:7px; }
        .qmi-risk__meta b { padding:3px 6px; border-radius:6px; background:rgba(148,163,184,.06); color:#91a0b6; font-size:10px; font-weight:850; }
        @media (min-width:1400px) { .qmi-risk__item strong { font-size:14px; } .qmi-risk__item small { font-size:13px; } }
        @media (max-width:1000px) { .qmi-risk__hero,.qmi-risk__grid { grid-template-columns:1fr; } }
        @media (max-width:760px) { .qmi-risk__header { flex-direction:column; } }

        /* DE-UI-008.1 — Technical Confluence Panel */

        /* DE-UI-016.x — FULL OPPORTUNITY CARD STYLES */
        .qmi-opportunity {
          padding: 18px !important;
          border: 1px solid var(--border, rgba(148,163,184,.16)) !important;
          border-radius: 16px !important;
          background: linear-gradient(135deg, rgba(37,99,235,.055), rgba(15,23,42,.82)) !important;
          box-shadow: 0 14px 34px rgba(2,6,23,.10) !important;
          overflow: hidden;
        }

        .qmi-opportunity__head {
          display: flex !important;
          align-items: center !important;
          justify-content: space-between !important;
          gap: 14px !important;
          margin-bottom: 12px !important;
        }

        .qmi-opportunity__title {
          display: flex !important;
          align-items: center !important;
          gap: 11px !important;
        }

        .qmi-opportunity__title h2 {
          margin: 3px 0 0 !important;
          font-size: 21px !important;
          line-height: 1.2 !important;
          font-weight: 950 !important;
          letter-spacing: -.025em !important;
        }

        .qmi-opportunity__status {
          min-width: 112px;
          padding: 8px 12px !important;
          border-radius: 9px !important;
          border: 1px solid rgba(244,197,66,.30) !important;
          background: rgba(244,197,66,.07) !important;
          color: #f4c542 !important;
          text-align: center;
          font-size: 12px !important;
          font-weight: 950 !important;
        }

        .qmi-opportunity__grid {
          display: grid !important;
          grid-template-columns: 1.15fr 1fr 1fr 1fr 1.15fr !important;
          gap: 8px !important;
        }

        .qmi-opportunity__cell {
          display: block !important;
          min-width: 0 !important;
          padding: 12px 13px !important;
          border-radius: 10px !important;
          border: 1px solid rgba(148,163,184,.11) !important;
          background: rgba(148,163,184,.035) !important;
        }

        .qmi-opportunity__cell span {
          display: block !important;
          margin-bottom: 6px !important;
          color: #9aa7b9 !important;
          font-size: 11px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: .045em !important;
          text-transform: uppercase !important;
          opacity: 1 !important;
        }

        .qmi-opportunity__cell strong {
          display: block !important;
          color: #f0f5fb !important;
          font-size: 15px !important;
          line-height: 1.3 !important;
          font-weight: 950 !important;
          overflow-wrap: anywhere !important;
        }

        .qmi-opportunity__cell small {
          display: block !important;
          margin-top: 5px !important;
          color: #a8b3c1 !important;
          font-size: 12px !important;
          line-height: 1.35 !important;
          font-weight: 750 !important;
          opacity: 1 !important;
        }

        .qmi-opportunity__cell.is-main strong {
          color: #f4c542 !important;
          font-size: 18px !important;
        }

        .qmi-opportunity__cell.is-critical strong {
          color: #ff8798 !important;
        }

        .qmi-opportunity__foot {
          display: grid !important;
          grid-template-columns: 1.3fr 1fr !important;
          gap: 8px !important;
          margin-top: 8px !important;
        }

        .qmi-opportunity__bar {
          display: block !important;
          padding: 11px 13px !important;
          border-radius: 9px !important;
          border: 1px solid rgba(148,163,184,.11) !important;
          background: rgba(2,6,23,.16) !important;
          color: #aeb9c8 !important;
          font-size: 12px !important;
          line-height: 1.5 !important;
          font-weight: 750 !important;
        }

        .qmi-opportunity__bar strong {
          color: #e5edf8 !important;
          font-weight: 950 !important;
        }

        @media (max-width: 1150px) {
          .qmi-opportunity__grid {
            grid-template-columns: repeat(3, minmax(0,1fr)) !important;
          }
        }

        @media (max-width: 760px) {
          .qmi-opportunity__head {
            align-items: flex-start !important;
            flex-direction: column !important;
          }

          .qmi-opportunity__grid,
          .qmi-opportunity__foot {
            grid-template-columns: 1fr !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL TOP V2.2 — SAFE LAYOUT
           ========================================================= */
        .qmi-ta-regime-panel--compact {
          padding: 14px 18px !important;
        }

        .qmi-ta-regime-summary {
          display: grid;
          grid-template-columns: minmax(230px, .72fr) minmax(0, 2.28fr);
          gap: 18px;
          align-items: center;
        }

        .qmi-ta-regime-panel--compact .qmi-ta-regime-name {
          margin: 4px 0 3px !important;
          font-size: 28px !important;
          line-height: 1 !important;
          font-weight: 950 !important;
          letter-spacing: -.03em !important;
        }

        .qmi-ta-regime-name--bear {
          color: #ff4f67 !important;
        }

        .qmi-ta-regime-name--bull {
          color: #31d890 !important;
        }

        .qmi-ta-regime-name--neutral {
          color: #f4c542 !important;
        }

        .qmi-ta-regime-panel--compact .qmi-ta-regime-sub {
          font-size: 12px !important;
        }

        .qmi-ta-regime-panel--compact .qmi-ta-context-grid {
          grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
          gap: 8px !important;
          margin: 0 !important;
        }

        .qmi-ta-regime-panel--compact .qmi-ta-context {
          min-height: 60px !important;
          padding: 10px 12px !important;
        }

        .qmi-ta-regime-panel--compact .qmi-ta-context strong {
          font-size: 17px !important;
        }

        .qmi-ta-decision-opportunity-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
        }

        .qmi-ta-decision-opportunity-grid > section {
          min-width: 0;
          height: 100%;
        }

        .qmi-ta-decision-opportunity-grid .qmi-synthesis,
        .qmi-ta-decision-opportunity-grid .qmi-opportunity {
          padding: 18px !important;
        }

        .qmi-ta-decision-opportunity-grid .qmi-synthesis__hero {
          grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
          gap: 7px !important;
        }

        .qmi-ta-decision-opportunity-grid .qmi-synthesis__footer,
        .qmi-ta-decision-opportunity-grid .qmi-opportunity__foot {
          grid-template-columns: 1fr !important;
        }

        .qmi-ta-decision-opportunity-grid .qmi-opportunity__grid {
          grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
          gap: 7px !important;
        }

        /* Technical typeface becomes the QMI shell default while this page is mounted. */
        .app-shell,
        .main-content,
        .page-shell,
        .topbar,
        .sidebar,
        .qmi-ta-page,
        button,
        input,
        select {
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
            "Segoe UI", sans-serif !important;
        }

        @media (max-width: 1180px) {
          .qmi-ta-regime-summary,
          .qmi-ta-decision-opportunity-grid {
            grid-template-columns: 1fr !important;
          }

          .qmi-ta-regime-panel--compact .qmi-ta-context-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }
        }


        /* Opportunity V2.3 — price levels only; decision semantics live in Decision */
        .qmi-opportunity__score {
          display: flex;
          align-items: baseline;
          gap: 10px;
          padding: 7px 10px;
          border: 1px solid rgba(245, 158, 11, .30);
          border-radius: 9px;
          background: rgba(245, 158, 11, .06);
          white-space: nowrap;
        }

        .qmi-opportunity__score strong {
          color: #f5c542;
          font-size: 16px;
          font-weight: 950;
        }

        .qmi-opportunity__score span {
          color: #f5c542;
          font-size: 14px;
          font-weight: 900;
        }

        .qmi-opportunity__grid--levels {
          grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
        }

        .qmi-opportunity__targets {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          margin-top: 9px;
          overflow: hidden;
          border: 1px solid rgba(148, 163, 184, .14);
          border-radius: 9px;
          background: rgba(8, 15, 28, .26);
        }

        .qmi-opportunity__targets > div {
          min-width: 0;
          padding: 11px 12px;
          border-right: 1px solid rgba(148, 163, 184, .12);
        }

        .qmi-opportunity__targets > div:last-child {
          border-right: 0;
        }

        .qmi-opportunity__targets span {
          display: block;
          margin-bottom: 5px;
          color: #8291aa;
          font-size: 10px !important;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-opportunity__targets strong {
          color: #f4f7fb;
          font-size: 14px;
          font-weight: 950;
        }

        @media (max-width: 760px) {
          .qmi-opportunity__grid--levels,
          .qmi-opportunity__targets {
            grid-template-columns: 1fr !important;
          }

          .qmi-opportunity__targets > div {
            border-right: 0;
            border-bottom: 1px solid rgba(148, 163, 184, .12);
          }

          .qmi-opportunity__targets > div:last-child {
            border-bottom: 0;
          }
        }

        /* =========================================================
           DECISION LAYER V2.5.1 — INTEGRATED / VISIBLE
           ========================================================= */
        .qmi-synthesis__decision-layer {
          display: grid !important;
          grid-template-columns: 150px minmax(0, 1fr) !important;
          gap: 10px !important;
          align-items: stretch !important;
          width: 100% !important;
          margin-top: 8px !important;
          padding-top: 9px !important;
          border-top: 1px solid rgba(148, 163, 184, .12) !important;
          visibility: visible !important;
          opacity: 1 !important;
        }

        .qmi-synthesis__decision-layer-title {
          display: flex !important;
          flex-direction: column !important;
          justify-content: center !important;
          min-width: 0 !important;
        }

        .qmi-synthesis__decision-layer-title span {
          display: block !important;
          color: #8fa0b7 !important;
          font-size: 10px !important;
          line-height: 1.2 !important;
          font-weight: 950 !important;
          letter-spacing: .06em !important;
          text-transform: uppercase !important;
        }

        .qmi-synthesis__decision-layer-title small {
          display: block !important;
          margin-top: 4px !important;
          color: #718096 !important;
          font-size: 9px !important;
          line-height: 1.25 !important;
          font-weight: 750 !important;
        }

        .qmi-synthesis__decision-layer-grid {
          display: grid !important;
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          gap: 7px !important;
          min-width: 0 !important;
        }

        .qmi-synthesis__decision-layer-state {
          display: block !important;
          min-width: 0 !important;
          padding: 9px 10px !important;
          border: 1px solid rgba(148, 163, 184, .12) !important;
          border-radius: 8px !important;
          background: rgba(8, 15, 28, .24) !important;
        }

        .qmi-synthesis__decision-layer-state span {
          display: block !important;
          margin-bottom: 4px !important;
          color: #8190a6 !important;
          font-size: 9px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: .05em !important;
          text-transform: uppercase !important;
        }

        .qmi-synthesis__decision-layer-state strong {
          display: block !important;
          font-size: 14px !important;
          line-height: 1.15 !important;
          font-weight: 950 !important;
        }

        .qmi-synthesis__decision-layer-state.is-defensive strong {
          color: #f4c542 !important;
        }

        .qmi-synthesis__decision-layer-state.is-unfavourable strong {
          color: #ff6178 !important;
        }

        @media (max-width: 760px) {
          .qmi-synthesis__decision-layer {
            grid-template-columns: 1fr !important;
          }

          .qmi-synthesis__decision-layer-grid {
            grid-template-columns: 1fr !important;
          }
        }

        /* =========================================================
           DECISION LAYER V2.6 — BELOW TECHNICAL OPPORTUNITY
           ========================================================= */
        .qmi-ta-right-stack {
          display: grid;
          grid-template-rows: auto auto;
          gap: 10px;
          min-width: 0;
          align-content: start;
        }

        .qmi-ta-right-stack > section {
          min-width: 0;
        }

        .qmi-decision--under-opportunity {
          padding: 14px 16px !important;
          border-radius: 12px !important;
        }

        .qmi-decision--under-opportunity .qmi-decision__header {
          margin-bottom: 9px !important;
        }

        .qmi-decision--under-opportunity .qmi-decision__title h2 {
          font-size: 18px !important;
        }

        .qmi-decision-minimal__grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }

        .qmi-decision-minimal__state {
          min-width: 0;
          padding: 12px 14px;
          border: 1px solid rgba(148, 163, 184, .13);
          border-radius: 9px;
          background: rgba(8, 15, 28, .28);
        }

        .qmi-decision-minimal__state span {
          display: block;
          margin-bottom: 5px;
          color: #8c9ab0;
          font-size: 10px !important;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-decision-minimal__state strong {
          display: block;
          font-size: 18px;
          line-height: 1.15;
          font-weight: 950;
          letter-spacing: -.02em;
        }

        .qmi-decision-minimal__state.is-defensive strong {
          color: #f4c542;
        }

        .qmi-decision-minimal__state.is-unfavourable strong {
          color: #ff6178;
        }

        @media (max-width: 1180px) {
          .qmi-ta-right-stack {
            grid-template-rows: auto auto;
          }
        }

        @media (max-width: 760px) {
          .qmi-decision-minimal__grid {
            grid-template-columns: 1fr;
          }
        }

        /* =========================================================
           QMI TECHNICAL TOP V2.7 — LEFT STACK / RIGHT DECISION
           Left: Regime + Opportunity + Decision Layer
           Right: Technical Decision
           ========================================================= */
        .qmi-ta-top-composition {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: start;
        }

        .qmi-ta-left-command-stack {
          display: grid;
          grid-template-rows: auto auto auto;
          gap: 10px;
          min-width: 0;
          align-content: start;
        }

        .qmi-ta-left-command-stack > section,
        .qmi-ta-top-composition > .qmi-synthesis {
          min-width: 0;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact {
          padding: 13px 16px !important;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-summary {
          grid-template-columns: minmax(150px, .72fr) minmax(0, 1.28fr) !important;
          gap: 12px !important;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact .qmi-ta-regime-name {
          font-size: 26px !important;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact .qmi-ta-context-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          gap: 7px !important;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact .qmi-ta-context {
          min-height: 54px !important;
          padding: 9px 10px !important;
        }

        .qmi-ta-left-command-stack .qmi-opportunity,
        .qmi-ta-left-command-stack .qmi-decision--under-opportunity {
          margin: 0 !important;
        }

        .qmi-ta-top-composition > .qmi-synthesis {
          height: 100%;
          min-height: 100%;
          align-self: stretch;
        }

        .qmi-ta-top-composition > .qmi-synthesis .qmi-synthesis__hero {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        .qmi-ta-top-composition > .qmi-synthesis .qmi-synthesis__permissions {
          grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
        }

        .qmi-ta-top-composition > .qmi-synthesis .qmi-synthesis__footer {
          grid-template-columns: 1fr !important;
        }

        @media (max-width: 1180px) {
          .qmi-ta-top-composition {
            grid-template-columns: 1fr !important;
          }

          .qmi-ta-left-command-stack .qmi-ta-regime-summary {
            grid-template-columns: 1fr !important;
          }

          .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact .qmi-ta-context-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL TOP V2.8 — REGIME HORIZONTAL
           BEAR + 4 context cards on one line
           ========================================================= */
        .qmi-ta-left-command-stack .qmi-ta-regime-summary {
          grid-template-columns: minmax(145px, .58fr) minmax(0, 2.42fr) !important;
          gap: 12px !important;
          align-items: center !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-regime-name {
          font-size: 34px !important;
          line-height: 1 !important;
          margin: 5px 0 4px !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context-grid {
          grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
          gap: 6px !important;
          margin: 0 !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context {
          min-height: 58px !important;
          padding: 8px 8px !important;
          text-align: center !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context span {
          margin-bottom: 5px !important;
          font-size: 9px !important;
          line-height: 1.15 !important;
          white-space: nowrap !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context strong {
          font-size: 15px !important;
          line-height: 1.1 !important;
          white-space: nowrap !important;
        }

        @media (max-width: 1450px) {
          .qmi-ta-left-command-stack .qmi-ta-regime-summary {
            grid-template-columns: minmax(130px, .52fr) minmax(0, 2.48fr) !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-regime-name {
            font-size: 31px !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-context span {
            font-size: 8px !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-context strong {
            font-size: 13px !important;
          }
        }

        @media (max-width: 1180px) {
          .qmi-ta-left-command-stack .qmi-ta-regime-summary {
            grid-template-columns: 1fr !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-context-grid {
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
          }
        }

        @media (max-width: 760px) {
          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-context-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL TOP V2.9 — REGIME SCALE / WIDER METRICS
           ========================================================= */
        .qmi-ta-left-command-stack .qmi-ta-regime-summary {
          grid-template-columns: 118px minmax(0, 1fr) !important;
          gap: 10px !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-regime-name {
          font-size: 44px !important;
          line-height: .95 !important;
          margin: 5px 0 4px !important;
          letter-spacing: -.045em !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context-grid {
          grid-template-columns: repeat(4, minmax(100px, 1fr)) !important;
          gap: 5px !important;
          width: 100% !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context {
          min-width: 0 !important;
          min-height: 64px !important;
          padding: 9px 7px !important;
          overflow: visible !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context span {
          font-size: 8.5px !important;
          line-height: 1.1 !important;
          letter-spacing: .025em !important;
          white-space: nowrap !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context strong {
          font-size: 15px !important;
          line-height: 1.05 !important;
          white-space: nowrap !important;
        }

        @media (max-width: 1450px) {
          .qmi-ta-left-command-stack .qmi-ta-regime-summary {
            grid-template-columns: 108px minmax(0, 1fr) !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-regime-name {
            font-size: 40px !important;
          }

          .qmi-ta-left-command-stack
            .qmi-ta-regime-panel--compact
            .qmi-ta-context-grid {
            grid-template-columns: repeat(4, minmax(92px, 1fr)) !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL V3.0 — TYPOGRAPHY STANDARD
           Consistent hierarchy across the full Technical dashboard.
           ========================================================= */

        /* 1. Section/module titles */
        .qmi-ta-page h2,
        .qmi-synthesis__title h2,
        .qmi-opportunity__title h2,
        .qmi-decision__title h2,
        .qmi-confluence__title h2,
        .qmi-scenario__title h2,
        .qmi-action__title h2,
        .qmi-risk__title h2,
        .qmi-sizing__title h2,
        .qmi-execution__title h2,
        .qmi-state-monitor__title h2 {
          font-size: 18px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: -.015em !important;
        }

        /* 2. Technical kicker / engine code */
        .qmi-ta-page .qmi-ta-kicker {
          font-size: 10px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: .055em !important;
        }

        /* 3. Metric labels */
        .qmi-ta-page .qmi-ta-context span,
        .qmi-ta-page .qmi-synthesis__card span,
        .qmi-ta-page .qmi-synthesis__permission span,
        .qmi-ta-page .qmi-synthesis__strip > span,
        .qmi-ta-page .qmi-opportunity__cell span,
        .qmi-ta-page .qmi-opportunity__targets span,
        .qmi-ta-page .qmi-decision-minimal__state span,
        .qmi-ta-page .qmi-confluence__score span,
        .qmi-ta-page .qmi-confluence__metric span,
        .qmi-ta-page .qmi-confluence__row span,
        .qmi-ta-page .qmi-scenario span,
        .qmi-ta-page .qmi-action span,
        .qmi-ta-page .qmi-risk span,
        .qmi-ta-page .qmi-sizing span,
        .qmi-ta-page .qmi-execution span,
        .qmi-ta-page .qmi-state-monitor span {
          font-size: 10px !important;
          line-height: 1.2 !important;
          font-weight: 850 !important;
          letter-spacing: .035em !important;
        }

        /* 4. Standard metric values */
        .qmi-ta-page .qmi-ta-context strong,
        .qmi-ta-page .qmi-synthesis__card strong,
        .qmi-ta-page .qmi-opportunity__cell strong,
        .qmi-ta-page .qmi-opportunity__targets strong,
        .qmi-ta-page .qmi-decision-minimal__state strong,
        .qmi-ta-page .qmi-confluence__metric strong {
          font-size: 15px !important;
          line-height: 1.15 !important;
          font-weight: 900 !important;
        }

        /* 5. Secondary/explanatory copy */
        .qmi-ta-page small,
        .qmi-ta-page .qmi-ta-regime-sub,
        .qmi-ta-page .qmi-synthesis__rationale,
        .qmi-ta-page .qmi-confluence__metric small,
        .qmi-ta-page .qmi-confluence__score small {
          font-size: 10px !important;
          line-height: 1.35 !important;
        }

        /* 6. Main states — intentionally one hierarchy above normal values */
        .qmi-ta-page .qmi-synthesis__card.is-posture strong,
        .qmi-ta-page .qmi-opportunity__score strong,
        .qmi-ta-page .qmi-decision-minimal__state strong {
          font-size: 17px !important;
          line-height: 1.1 !important;
          font-weight: 950 !important;
        }

        /* 7. Main regime and confluence score are the only XL values */
        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-regime-name {
          font-size: 42px !important;
          line-height: .95 !important;
          font-weight: 950 !important;
        }

        .qmi-ta-page .qmi-confluence__score strong {
          font-size: 42px !important;
          line-height: .95 !important;
          font-weight: 950 !important;
        }

        /* 8. Permission/action values */
        .qmi-ta-page .qmi-synthesis__permission strong {
          font-size: 11px !important;
          line-height: 1.15 !important;
          font-weight: 900 !important;
        }

        /* 9. Opportunity status/quality */
        .qmi-ta-page .qmi-opportunity__score span {
          font-size: 13px !important;
          line-height: 1.1 !important;
          font-weight: 900 !important;
        }

        /* 10. Keep controls readable and aligned with Technical typography */
        .qmi-ta-page button,
        .qmi-ta-page input,
        .qmi-ta-page select {
          font-size: 13px !important;
          line-height: 1.2 !important;
        }

        /* =========================================================
           QMI TECHNICAL V3.1 — UNIFIED QMI MODULE TITLES
           Every visible "QMI ..." module title uses exactly the same scale.
           ========================================================= */

        .qmi-ta-page .qmi-synthesis__title h2,
        .qmi-ta-page .qmi-opportunity__title h2,
        .qmi-ta-page .qmi-decision__title h2,
        .qmi-ta-page .qmi-confluence__title h2,
        .qmi-ta-page .qmi-scenario__title h2,
        .qmi-ta-page .qmi-action__title h2,
        .qmi-ta-page .qmi-risk__title h2,
        .qmi-ta-page .qmi-sizing__title h2,
        .qmi-ta-page .qmi-execution__title h2,
        .qmi-ta-page .qmi-state-monitor__title h2,
        .qmi-ta-page section h2 {
          font-size: 18px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: -0.015em !important;
          margin-top: 2px !important;
          margin-bottom: 0 !important;
        }

        /* Remove local exceptions in the compact top composition */
        .qmi-ta-top-composition .qmi-synthesis__title h2,
        .qmi-ta-left-command-stack .qmi-opportunity__title h2,
        .qmi-ta-left-command-stack .qmi-decision__title h2,
        .qmi-decision--under-opportunity .qmi-decision__title h2 {
          font-size: 18px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
        }

        /* All engine/module kickers aligned too */
        .qmi-ta-page .qmi-ta-kicker,
        .qmi-ta-page [class*="__title"] .qmi-ta-kicker {
          font-size: 10px !important;
          line-height: 1.2 !important;
          font-weight: 900 !important;
          letter-spacing: .055em !important;
        }

        /* =========================================================
           QMI TECHNICAL V3.2 — ALIGN LEFT / RIGHT TOP WINDOWS
           Grow Market Regime so the left stack matches Technical Decision.
           ========================================================= */
        .qmi-ta-left-command-stack .qmi-ta-regime-panel--compact {
          min-height: 154px !important;
          padding: 18px 18px !important;
          display: flex !important;
          align-items: center !important;
        }

        .qmi-ta-left-command-stack .qmi-ta-regime-summary {
          width: 100% !important;
          grid-template-columns: 118px minmax(0, 1fr) !important;
          gap: 10px !important;
          align-items: center !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-context {
          min-height: 76px !important;
          padding: 12px 8px !important;
          display: flex !important;
          flex-direction: column !important;
          justify-content: center !important;
        }

        .qmi-ta-left-command-stack
          .qmi-ta-regime-panel--compact
          .qmi-ta-regime-name {
          font-size: 42px !important;
        }

        /* =========================================================
           QMI TECHNICAL V3.3 — CONFLUENCE WEIGHT AUDIT
           7 directional engines + volatility separated as modifier.
           ========================================================= */
        .qmi-confluence__allocation-note {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-top: 10px;
          padding: 9px 11px;
          border: 1px solid rgba(91, 140, 255, .16);
          border-radius: 9px;
          background: rgba(91, 140, 255, .055);
        }

        .qmi-confluence__allocation-note span {
          flex: 0 0 auto;
          color: #8fa0b7;
          font-size: 10px !important;
          font-weight: 900;
          letter-spacing: .045em;
          text-transform: uppercase;
        }

        .qmi-confluence__allocation-note strong {
          color: #c8d2e1;
          font-size: 10px !important;
          line-height: 1.3;
          font-weight: 750;
          text-align: right;
        }

        /* =========================================================
           QMI TECHNICAL V3.4 — BACKEND-DRIVEN CONFLUENCE
           ========================================================= */
        .qmi-confluence__weight-audit {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-top: 8px;
          padding: 8px 11px;
          border: 1px solid rgba(49, 216, 144, .16);
          border-radius: 9px;
          background: rgba(49, 216, 144, .045);
        }

        .qmi-confluence__weight-audit span {
          color: #8fa0b7;
          font-size: 10px !important;
          font-weight: 900;
          letter-spacing: .045em;
          text-transform: uppercase;
        }

        .qmi-confluence__weight-audit strong {
          color: #31d890;
          font-size: 14px !important;
          font-weight: 950;
        }

        /* =========================================================
           QMI TECHNICAL V3.5 — VOLATILITY / RISK CONTEXT
           Volatility explains reliability, not direction.
           ========================================================= */
        .qmi-volatility-context {
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .qmi-volatility-context__head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 14px;
          margin-bottom: 12px;
        }

        .qmi-volatility-context__head > div:first-child > span,
        .qmi-volatility-context__risk span {
          display: block;
          color: #56d997;
          font-size: 10px !important;
          font-weight: 950;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-volatility-context__head > div:first-child > strong {
          display: block;
          margin-top: 5px;
          font-size: 20px !important;
          line-height: 1.1;
          font-weight: 950;
        }

        .qmi-volatility-context__risk {
          min-width: 132px;
          padding: 9px 11px;
          border: 1px solid rgba(86, 217, 151, .18);
          border-radius: 9px;
          background: rgba(86, 217, 151, .045);
          text-align: right;
        }

        .qmi-volatility-context__risk span {
          color: #8291a6;
          font-size: 9px !important;
        }

        .qmi-volatility-context__risk strong {
          display: block;
          margin-top: 4px;
          color: #56d997;
          font-size: 14px !important;
          font-weight: 950;
        }

        .qmi-volatility-context__primary {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 8px;
        }

        .qmi-volatility-context__metric {
          min-width: 0;
          padding: 13px;
          border: 1px solid rgba(148, 163, 184, .11);
          border-radius: 10px;
          background: rgba(2, 6, 23, .18);
        }

        .qmi-volatility-context__metric span,
        .qmi-volatility-context__status-grid span {
          display: block;
          margin-bottom: 6px;
          color: #8f9db1;
          font-size: 10px !important;
          line-height: 1.2;
          font-weight: 900;
          letter-spacing: .04em;
          text-transform: uppercase;
        }

        .qmi-volatility-context__metric strong {
          display: block;
          color: #56d997;
          font-size: 22px !important;
          line-height: 1;
          font-weight: 950;
        }

        .qmi-volatility-context__metric small {
          display: block;
          margin-top: 7px;
          color: #9da9b9;
          font-size: 10px !important;
          line-height: 1.4;
        }

        .qmi-volatility-context__status-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 7px;
          margin-top: 8px;
        }

        .qmi-volatility-context__status-grid > div {
          min-width: 0;
          padding: 10px;
          border: 1px solid rgba(148, 163, 184, .10);
          border-radius: 8px;
          background: rgba(148, 163, 184, .025);
        }

        .qmi-volatility-context__status-grid strong {
          display: block;
          font-size: 13px !important;
          line-height: 1.15;
          font-weight: 950;
        }

        .qmi-volatility-context__explanation {
          display: grid;
          grid-template-columns: 34px minmax(0, 1fr);
          gap: 10px;
          align-items: start;
          margin-top: 9px;
          padding: 11px 12px;
          border: 1px solid rgba(86, 217, 151, .12);
          border-radius: 9px;
          background: rgba(86, 217, 151, .03);
        }

        .qmi-volatility-context__explanation-icon {
          width: 32px;
          height: 32px;
          display: grid;
          place-items: center;
          border-radius: 8px;
          background: rgba(86, 217, 151, .08);
          color: #56d997;
        }

        .qmi-volatility-context__explanation strong {
          display: block;
          color: #dce7f4;
          font-size: 11px !important;
          font-weight: 950;
          text-transform: uppercase;
        }

        .qmi-volatility-context__explanation span {
          display: block;
          margin-top: 4px;
          color: #a7b2c1;
          font-size: 10px !important;
          line-height: 1.45;
        }

        .qmi-confluence__audit {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        @media (max-width: 760px) {
          .qmi-volatility-context__primary,
          .qmi-volatility-context__status-grid {
            grid-template-columns: 1fr 1fr;
          }

          .qmi-volatility-context__head {
            align-items: flex-start;
            flex-direction: column;
          }

          .qmi-volatility-context__risk {
            width: 100%;
            text-align: left;
          }
        }

        /* =========================================================
           QMI TECHNICAL V3.6 — VOLATILITY + SCENARIO MATRIX ROW
           Left: Volatility / Risk Context
           Right: Scenario Matrix with 3 vertical scenarios
           ========================================================= */

        /* Directional engines now use the full Confluence width */
        .qmi-confluence__engine-layout {
          grid-template-columns: 1fr !important;
        }

        .qmi-volatility-scenario-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
        }

        .qmi-volatility-scenario-row__left,
        .qmi-volatility-scenario-row__right {
          min-width: 0;
          display: flex;
        }

        .qmi-volatility-scenario-row__left > .qmi-volatility-context,
        .qmi-volatility-scenario-row__right > .qmi-scenario {
          width: 100%;
          height: 100%;
          margin: 0 !important;
        }

        .qmi-volatility-scenario-row__left .qmi-volatility-context {
          padding: 16px !important;
          border: 1px solid rgba(148, 163, 184, 0.14);
          border-radius: 14px;
          background: rgba(15, 23, 42, 0.72);
        }

        /* Three scenarios one under another */
        .qmi-volatility-scenario-row .qmi-scenario__grid {
          grid-template-columns: 1fr !important;
          gap: 8px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__card {
          padding: 11px 12px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__card-head {
          margin-bottom: 7px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__thesis {
          margin-top: 7px !important;
          font-size: 10px !important;
          line-height: 1.35 !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__facts {
          grid-template-columns: 1fr 1fr !important;
          gap: 7px !important;
          margin-top: 7px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__fact {
          padding: 8px 9px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__footer {
          grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
          gap: 7px !important;
          margin-top: 8px !important;
        }

        .qmi-volatility-scenario-row .qmi-scenario__footer > div {
          padding: 9px 10px !important;
        }

        /* Keep volatility compact enough to align visually with Scenario Matrix */
        .qmi-volatility-scenario-row .qmi-volatility-context__primary {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        .qmi-volatility-scenario-row .qmi-volatility-context__status-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        @media (max-width: 1180px) {
          .qmi-volatility-scenario-row {
            grid-template-columns: 1fr !important;
          }
        }

        @media (max-width: 760px) {
          .qmi-volatility-scenario-row .qmi-scenario__facts,
          .qmi-volatility-scenario-row .qmi-scenario__footer,
          .qmi-volatility-scenario-row .qmi-volatility-context__primary,
          .qmi-volatility-scenario-row .qmi-volatility-context__status-grid {
            grid-template-columns: 1fr !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL V3.7 — CONFLUENCE LEFT / SCENARIOS RIGHT
           ========================================================= */
        .qmi-confluence-scenario-pair {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 14px;
          align-items: stretch;
        }

        .qmi-confluence-scenario-pair__left,
        .qmi-confluence-scenario-pair__right {
          min-width: 0;
          display: flex;
        }

        .qmi-confluence-scenario-pair__left > .qmi-confluence,
        .qmi-confluence-scenario-pair__right > .qmi-scenario {
          width: 100%;
          height: 100%;
          margin: 0 !important;
        }

        /* Confluence is compact inside its left half */
        .qmi-confluence-scenario-pair .qmi-confluence__engine-layout {
          grid-template-columns: 1fr !important;
        }

        .qmi-confluence-scenario-pair .qmi-volatility-context {
          margin-top: 10px;
          padding: 13px !important;
          border: 1px solid rgba(148, 163, 184, .12);
          border-radius: 10px;
          background: rgba(8, 15, 28, .22);
        }

        .qmi-confluence-scenario-pair .qmi-volatility-context__primary,
        .qmi-confluence-scenario-pair .qmi-volatility-context__status-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        /* Scenario Matrix uses the right half; scenarios stacked vertically */
        .qmi-confluence-scenario-pair .qmi-scenario__grid {
          grid-template-columns: 1fr !important;
          gap: 8px !important;
        }

        .qmi-confluence-scenario-pair .qmi-scenario__card {
          padding: 11px 12px !important;
        }

        .qmi-confluence-scenario-pair .qmi-scenario__facts {
          grid-template-columns: 1fr 1fr !important;
          gap: 7px !important;
        }

        .qmi-confluence-scenario-pair .qmi-scenario__footer {
          grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
          gap: 7px !important;
        }

        @media (max-width: 1180px) {
          .qmi-confluence-scenario-pair {
            grid-template-columns: 1fr !important;
          }
        }

        @media (max-width: 760px) {
          .qmi-confluence-scenario-pair .qmi-volatility-context__primary,
          .qmi-confluence-scenario-pair .qmi-volatility-context__status-grid,
          .qmi-confluence-scenario-pair .qmi-scenario__facts,
          .qmi-confluence-scenario-pair .qmi-scenario__footer {
            grid-template-columns: 1fr !important;
          }
        }

        /* =========================================================
           QMI TECHNICAL V3.8 — VOLATILITY TOP RIGHT
           Confluence left; Volatility above Scenario Matrix on right.
           ========================================================= */
        .qmi-confluence-scenario-pair__right {
          display: flex !important;
          flex-direction: column !important;
          gap: 10px !important;
        }

        .qmi-confluence-scenario-pair__right > .qmi-volatility-context {
          width: 100%;
          margin: 0 !important;
          padding: 13px !important;
          flex: 0 0 auto;
          border: 1px solid rgba(148, 163, 184, .12);
          border-radius: 10px;
          background: rgba(8, 15, 28, .22);
        }

        .qmi-confluence-scenario-pair__right > .qmi-scenario {
          width: 100%;
          margin: 0 !important;
          flex: 1 1 auto;
        }

        .qmi-confluence-scenario-pair__right .qmi-volatility-context__primary,
        .qmi-confluence-scenario-pair__right .qmi-volatility-context__status-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        /* Left and right cards stretch to the same total row height */
        .qmi-confluence-scenario-pair {
          align-items: stretch !important;
        }

        .qmi-confluence-scenario-pair__left > .qmi-confluence {
          height: 100% !important;
        }

        .qmi-detail-divider {
          display: flex;
          align-items: end;
          justify-content: space-between;
          gap: 16px;
          margin: 4px 2px -2px;
          padding: 8px 4px 0;
        }

        .qmi-detail-divider span {
          display: block;
          color: #6f9fff;
          font-size: 11px;
          font-weight: 950;
          letter-spacing: .09em;
        }

        .qmi-detail-divider strong {
          display: block;
          margin-top: 4px;
          color: #e8eef8;
          font-size: 16px;
          font-weight: 950;
        }

        .qmi-detail-divider small {
          color: #7f8da2;
          font-size: 11px;
          font-weight: 800;
        }

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

        .qmi-confluence__engine-layout {
          display: grid;
          grid-template-columns: minmax(0, 1.05fr) minmax(0, 0.95fr);
          gap: 14px;
          margin-top: 16px;
          align-items: stretch;
        }

        .qmi-confluence__key-panel,
        .qmi-confluence__modifier-panel {
          min-width: 0;
          padding: 16px;
          border: 1px solid rgba(148, 163, 184, 0.14);
          border-radius: 14px;
          background: rgba(2, 6, 23, 0.13);
        }

        .qmi-confluence__panel-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          margin-bottom: 12px;
        }

        .qmi-confluence__panel-head > div:first-child span {
          display: block;
          color: #74a7ff;
          font-size: 12px;
          font-weight: 950;
          letter-spacing: 0.055em;
        }

        .qmi-confluence__modifier-panel
        .qmi-confluence__panel-head > div:first-child span {
          color: #56d997;
        }

        .qmi-confluence__panel-head > div:first-child strong {
          display: block;
          margin-top: 4px;
          font-size: 22px;
          line-height: 1.2;
          font-weight: 950;
        }

        .qmi-confluence__panel-columns {
          display: grid;
          grid-template-columns: 112px 96px;
          gap: 12px;
          color: #a2aec0;
          font-size: 11px;
          font-weight: 900;
          text-align: right;
          text-transform: uppercase;
        }

        .qmi-confluence__key-list {
          display: grid;
          gap: 7px;
        }

        .qmi-confluence__engine--large {
          padding: 13px 14px 11px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-confluence__engine-main {
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          align-items: center;
          gap: 14px;
        }

        .qmi-confluence__engine-identity {
          display: flex;
          align-items: center;
          gap: 11px;
          min-width: 0;
        }

        .qmi-confluence__engine-icon {
          width: 40px;
          height: 40px;
          flex: 0 0 40px;
          display: grid;
          place-items: center;
          border-radius: 10px;
          border: 1px solid rgba(255, 97, 120, 0.18);
          background: rgba(255, 97, 120, 0.045);
          color: #ff6178;
        }

        .qmi-confluence__engine.is-positive .qmi-confluence__engine-icon {
          border-color: rgba(49, 216, 144, 0.18);
          background: rgba(49, 216, 144, 0.045);
          color: #31d890;
        }

        .qmi-confluence__engine-identity span {
          display: block;
          font-size: 15px;
          line-height: 1.2;
          font-weight: 950;
          color: #eef4fb;
        }

        .qmi-confluence__engine-identity small {
          display: block;
          margin-top: 4px;
          color: #a4b0c1;
          font-size: 12px !important;
          line-height: 1.35;
          opacity: 1 !important;
        }

        .qmi-confluence__engine-values {
          display: grid;
          grid-template-columns: 112px 96px;
          align-items: center;
          gap: 12px;
          text-align: right;
        }

        .qmi-confluence__engine-values strong {
          font-size: 20px;
          line-height: 1;
          font-weight: 1000;
        }

        .qmi-confluence__engine-values b {
          color: #edf3fb;
          font-size: 15px;
          font-weight: 950;
        }

        .qmi-confluence__engine.is-positive .qmi-confluence__engine-values strong {
          color: #31d890;
        }

        .qmi-confluence__engine.is-negative .qmi-confluence__engine-values strong {
          color: #ff6178;
        }

        .qmi-confluence__engine.is-neutral .qmi-confluence__engine-values strong {
          color: #f4c542;
        }

        .qmi-confluence__engine-scale {
          margin-top: 9px;
          padding-left: 51px;
          padding-right: 1px;
        }

        .qmi-confluence__engine-track {
          position: relative;
          height: 6px;
          overflow: visible;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.13);
        }

        .qmi-confluence__engine-center,
        .qmi-confluence__engine-quarter {
          position: absolute;
          top: -3px;
          bottom: -3px;
          width: 1px;
          z-index: 2;
          background: rgba(226, 232, 240, 0.25);
        }

        .qmi-confluence__engine-center {
          left: 50%;
          background: rgba(226, 232, 240, 0.42);
        }

        .qmi-confluence__engine-quarter.is-left {
          left: 25%;
        }

        .qmi-confluence__engine-quarter.is-right {
          left: 75%;
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

        .qmi-confluence__axis-labels {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          margin-top: 5px;
          color: #9eabba;
          font-size: 11px;
          font-weight: 800;
        }

        .qmi-confluence__axis-labels span:nth-child(1) { text-align: left; }
        .qmi-confluence__axis-labels span:nth-child(2),
        .qmi-confluence__axis-labels span:nth-child(3),
        .qmi-confluence__axis-labels span:nth-child(4) { text-align: center; }
        .qmi-confluence__axis-labels span:nth-child(5) { text-align: right; }

        .qmi-confluence__legend {
          display: flex;
          flex-wrap: wrap;
          gap: 20px;
          margin-top: 11px;
          padding: 10px 12px 2px;
          color: #b3becc;
          font-size: 12px;
          font-weight: 800;
        }

        .qmi-confluence__legend span {
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        .qmi-confluence__legend i {
          width: 9px;
          height: 9px;
          display: inline-block;
          border-radius: 50%;
        }

        .qmi-confluence__legend i.is-bearish { background: #ff6178; }
        .qmi-confluence__legend i.is-neutral { background: #718096; }
        .qmi-confluence__legend i.is-bullish { background: #31d890; }

        .qmi-confluence__modifier-badge {
          padding: 8px 11px;
          border: 1px solid rgba(86, 217, 151, 0.22);
          border-radius: 9px;
          background: rgba(86, 217, 151, 0.07);
          color: #56d997;
          font-size: 15px;
          font-weight: 950;
        }

        .qmi-confluence__modifier-card {
          padding: 15px;
          border: 1px solid rgba(148, 163, 184, 0.11);
          border-radius: 11px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-confluence__modifier-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-confluence__modifier-grid > div {
          min-width: 0;
          padding: 12px;
          border-radius: 9px;
          background: rgba(2, 6, 23, 0.18);
        }

        .qmi-confluence__modifier-grid span,
        .qmi-confluence__modifier-track span,
        .qmi-confluence__secondary-evidence span {
          display: block;
          margin-bottom: 6px;
          color: #9ca9ba;
          font-size: 12px;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: .04em;
        }

        .qmi-confluence__modifier-grid strong {
          font-size: 18px;
          font-weight: 950;
        }

        .qmi-confluence__modifier-track {
          margin-top: 11px;
          padding: 12px;
          border-radius: 9px;
          background: rgba(2, 6, 23, 0.18);
        }

        .qmi-confluence__modifier-track > div:first-child {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          margin-bottom: 9px;
        }

        .qmi-confluence__modifier-track > div:first-child span {
          margin: 0;
        }

        .qmi-confluence__modifier-track > div:first-child strong {
          color: #56d997;
          font-size: 16px;
        }

        .qmi-confluence__modifier-note {
          margin-top: 10px;
          padding: 14px;
          border: 1px solid rgba(86, 217, 151, 0.13);
          border-radius: 10px;
          background: rgba(86, 217, 151, 0.035);
        }

        .qmi-confluence__modifier-note strong {
          display: block;
          margin-bottom: 7px;
          color: #56d997;
          font-size: 13px;
          font-weight: 950;
          text-transform: uppercase;
        }

        .qmi-confluence__modifier-note span {
          color: #aeb8c6;
          font-size: 13px;
          line-height: 1.5;
        }

        .qmi-confluence__secondary-evidence {
          margin-top: 10px;
          padding: 13px;
          border: 1px solid rgba(148, 163, 184, 0.11);
          border-radius: 9px;
          background: rgba(148, 163, 184, 0.025);
        }

        .qmi-confluence__secondary-evidence span {
          margin-bottom: 5px;
        }

        .qmi-confluence__secondary-evidence strong {
          font-size: 13px;
          font-weight: 900;
        }

        @media (max-width: 1100px) {
          .qmi-confluence__engine-layout {
            grid-template-columns: 1fr;
          }
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
          <div className="qmi-ta-top-composition">
            <div className="qmi-ta-left-command-stack">
              <section className="qmi-ta-regime-panel qmi-ta-regime-panel--compact">
            <div className="qmi-ta-regime-summary">
              <div>
                <span className="qmi-ta-kicker">
                  QMI MARKET REGIME · {submittedSymbol}
                </span>

                <div
                  className={`qmi-ta-regime-name qmi-ta-regime-name--${
                    String(regime.primary_regime || "").toUpperCase().includes("BULL")
                      ? "bull"
                      : String(regime.primary_regime || "").toUpperCase().includes("BEAR")
                        ? "bear"
                        : "neutral"
                  }`}
                >
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
            </div>
          </section>

              <section className="qmi-opportunity qmi-opportunity--levels-only">
            <div className="qmi-opportunity__head">
              <div className="qmi-opportunity__title">
                <div className="qmi-ta-icon-box">
                  <Gauge size={18} strokeWidth={1.8} />
                </div>
                <div>
                  <span className="qmi-ta-kicker">DE-UI-016.x · OPPORTUNITY & PRICE PLAN</span>
                  <h2>QMI Technical Opportunity</h2>
                </div>
              </div>

              <div className="qmi-opportunity__score">
                <strong>{pretty(setupStatus016)}</strong>
                <span>
                  {setupQuality016 !== undefined && setupQuality016 !== null
                    ? `${formatNumber(setupQuality016, 1)} / 100`
                    : "-- / 100"}
                </span>
              </div>
            </div>

            {decisionSynthesisLoading && !technicalSetup ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building opportunity and price plan...
              </div>
            ) : (
              <>
                <div className="qmi-opportunity__grid qmi-opportunity__grid--levels">
                  <div className="qmi-opportunity__cell">
                    <span>Current Price</span>
                    <strong>{formatPrice016(priceCurrent016)}</strong>
                  </div>

                  <div className="qmi-opportunity__cell is-critical">
                    <span>Critical Level</span>
                    <strong>{formatPrice016(priceTrigger016?.price)}</strong>
                  </div>

                  <div className="qmi-opportunity__cell">
                    <span>Structural Zone</span>
                    <strong>
                      {priceEntryZone016?.lower !== undefined && priceEntryZone016?.upper !== undefined
                        ? `${formatPrice016(priceEntryZone016.lower)} – ${formatPrice016(priceEntryZone016.upper)}`
                        : "--"}
                    </strong>
                  </div>
                </div>

                <div className="qmi-opportunity__targets">
                  <div>
                    <span>Invalidation</span>
                    <strong>{formatPrice016(priceInvalidation016)}</strong>
                  </div>
                  <div>
                    <span>Target 1</span>
                    <strong>{formatPrice016(priceTarget1016)}</strong>
                  </div>
                  <div>
                    <span>Target 2</span>
                    <strong>{formatPrice016(priceTarget2016)}</strong>
                  </div>
                  <div>
                    <span>R:R</span>
                    <strong>{priceRR016?.available ? priceRR016?.ratio : "--"}</strong>
                  </div>
                </div>
              </>
            )}
          </section>

              <section className="qmi-decision qmi-decision--minimal qmi-decision--under-opportunity">
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
            </div>

            {decisionLoading && !technicalDecision ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Converting technical evidence into decision posture...
              </div>
            ) : decisionError ? (
              <div className="qmi-ta-alert">{decisionError}</div>
            ) : technicalDecision ? (
              <div className="qmi-decision-minimal__grid">
                <div className="qmi-decision-minimal__state is-defensive">
                  <span>Decision Posture</span>
                  <strong>
                    {pretty(
                      decisionPosture?.state ||
                      decisionCore?.state ||
                      technicalDecision?.state
                    )}
                  </strong>
                </div>

                <div className="qmi-decision-minimal__state is-unfavourable">
                  <span>Market Condition</span>
                  <strong>
                    {pretty(
                      decisionPosture?.directional_state ||
                      decisionCore?.directional_state ||
                      "Unfavourable"
                    )}
                  </strong>
                </div>
              </div>
            ) : null}
          </section>
            </div>

            <section className="qmi-synthesis">
            <div className="qmi-synthesis__header">
              <div className="qmi-synthesis__title">
                <div className="qmi-ta-icon-box"><ShieldCheck size={19} strokeWidth={1.8} /></div>
                <div>
                  <span className="qmi-ta-kicker">DE-UI-015.0 · DECISION SYNTHESIS</span>
                  <h2>QMI Technical Decision</h2>
                </div>
              </div>
              <div className="qmi-synthesis__badge">{pretty(synthesisPosture)}</div>
            </div>

            {decisionSynthesisLoading && !decisionSynthesis ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building final technical decision...
              </div>
            ) : decisionSynthesisError ? (
              <div className="qmi-ta-alert">
                Decision synthesis unavailable: {decisionSynthesisError}
              </div>
            ) : (
              <>
                <div className="qmi-synthesis__hero">
                  <div className="qmi-synthesis__card is-posture">
                    <span>Final Posture</span>
                    <strong>{pretty(synthesisPosture)}</strong>
                    <small>
                      Conviction {synthesisConviction !== undefined && synthesisConviction !== null
                        ? formatNumber(synthesisConviction, 1)
                        : "--"}
                    </small>
                  </div>

                  <div className="qmi-synthesis__card">
                    <span>State Transition</span>
                    <strong className="qmi-synthesis__transition">
                      {pretty(synthesisCurrentState)} → {pretty(synthesisTargetState)}
                    </strong>
                    <small>{pretty(synthesisExecutionState)}</small>
                  </div>

                  <div className="qmi-synthesis__card">
                    <span>Timing</span>
                    <strong>{pretty(synthesisTiming)}</strong>
                    <small>Execution timing</small>
                  </div>

                  <div className="qmi-synthesis__card">
                    <span>Risk</span>
                    <strong>{pretty(synthesisRisk)}</strong>
                    <small>Technical risk state</small>
                  </div>

                  <div className="qmi-synthesis__card">
                    <span>Primary Scenario</span>
                    <strong>{actionText(synthesisScenario)}</strong>
                    <small>
                      Direction {synthesisDirection !== undefined && synthesisDirection !== null
                        ? formatScore(synthesisDirection)
                        : "--"}
                    </small>
                  </div>

                  <div className="qmi-synthesis__card">
                    <span>Execution Confidence</span>
                    <strong>
                      {synthesisExecutionConfidence !== undefined && synthesisExecutionConfidence !== null
                        ? formatPercent(synthesisExecutionConfidence)
                        : "--"}
                    </strong>
                    <small>Final pipeline confidence</small>
                  </div>
                </div>

                <div className="qmi-synthesis__permissions">
                  {["WAIT", "ENTER", "ADD", "REDUCE", "EXIT"].map((key) => {
                    const value = synthesisPermission(key);
                    return (
                      <div
                        className={`qmi-synthesis__permission ${synthesisToneClass(value)}`}
                        key={`synthesis-permission-${key}`}
                      >
                        <span>{key}</span>
                        <strong>{pretty(value)}</strong>
                      </div>
                    );
                  })}
                </div>

                <div className="qmi-synthesis__footer">
                  <div className="qmi-synthesis__strip">
                    <span>Active Blockers</span>
                    <strong>{synthesisBlockerCount}</strong>
                    {synthesisBlockers.length ? (
                      <div className="qmi-synthesis__blockers">
                        {synthesisBlockers.slice(0, 5).map((item, index) => (
                          <div className="qmi-synthesis__blocker" key={`synthesis-blocker-${index}`}>
                            {pretty(item?.severity)} · {actionText(item?.reason || item?.type)}
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>

                  <div className="qmi-synthesis__strip">
                    <span>QMI Rationale</span>
                    <div className="qmi-synthesis__rationale">
                      {synthesisRationale || "Final deterministic synthesis of the technical decision pipeline."}
                    </div>
                  </div>
                </div>
              </>
            )}
          </section>
          </div>

          <div className="qmi-detail-divider">
            <div>
              <span>DETAILED TECHNICAL ANALYSIS</span>
              <strong>Decision Evidence & Execution Context</strong>
            </div>
            <small>Supporting engines and operational detail</small>
          </div>

          <div className="qmi-confluence-scenario-pair">
            <div className="qmi-confluence-scenario-pair__left">
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

                {(keyConfluenceContributions.length > 0 || volatility) && (
                  <div className="qmi-confluence__engine-layout">
                    <div className="qmi-confluence__key-panel">
                      <div className="qmi-confluence__panel-head">
                        <div>
                          <span>DE-UI-008.1 · TECHNICAL CONFLUENCE</span>
                          <strong>Directional Confluence Engines ({keyConfluenceContributions.length})</strong>
                        </div>
                        <div className="qmi-confluence__panel-columns">
                          <span>Contribution</span>
                          <span>Confidence</span>
                        </div>
                      </div>

                      <div className="qmi-confluence__key-list">
                        {keyConfluenceContributions.map((item) => (
                          <ConfluenceContribution
                            key={item.engine}
                            item={item}
                          />
                        ))}
                      </div>

                      <div className="qmi-confluence__allocation-note">
                        <span>Directional allocation</span>
                        <strong>
                          All available directional engines returned by the backend are shown here. Effective weights are normalized and should sum to 100%.
                        </strong>
                      </div>

                      <div className="qmi-confluence__weight-audit">
                        <span>Total effective weight</span>
                        <strong>
                          {formatPercent(
                            keyConfluenceContributions.reduce(
                              (sum, item) => sum + Number(item?.effective_weight_pct || 0),
                              0
                            )
                          )}
                        </strong>
                      </div>

                      <div className="qmi-confluence__legend">
                        <span><i className="is-bearish" /> Bearish Contribution</span>
                        <span><i className="is-neutral" /> Neutral</span>
                        <span><i className="is-bullish" /> Bullish Contribution</span>
                      </div>
                    </div>

                    
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
            </div>

            <div className="qmi-confluence-scenario-pair__right">
              <div className="qmi-confluence__modifier-panel qmi-volatility-context">
                      <div className="qmi-volatility-context__head">
                        <div>
                          <span>VOLATILITY / RISK CONTEXT</span>
                          <strong>{pretty(volatilityContext?.state || volatility?.state || "Unknown")}</strong>
                        </div>

                        <div className="qmi-volatility-context__risk">
                          <span>Risk context</span>
                          <strong>
                            {pretty(
                              volatilityContext?.risk_modifier ||
                              volatility?.risk_environment ||
                              "Normal"
                            )}
                          </strong>
                        </div>
                      </div>

                      <div className="qmi-volatility-context__primary">
                        <div className="qmi-volatility-context__metric">
                          <span>Confidence Modifier</span>
                          <strong>{formatPercent(volatilityModifierValue)}</strong>
                          <small>
                            Quality of the directional signal under the current volatility regime
                          </small>
                        </div>

                        <div className="qmi-volatility-context__metric">
                          <span>Final Confidence Contribution</span>
                          <strong>
                            {volatilityConfidenceContribution !== undefined &&
                            volatilityConfidenceContribution !== null
                              ? `+${formatNumber(volatilityConfidenceContribution, 1)} pts`
                              : "--"}
                          </strong>
                          <small>
                            Volatility contributes 5% of total Confluence confidence
                          </small>
                        </div>
                      </div>

                      <div className="qmi-volatility-context__status-grid">
                        <div>
                          <span>Expansion</span>
                          <strong>
                            {volatilityContext?.expansion ? "ACTIVE" : "NO"}
                          </strong>
                        </div>
                        <div>
                          <span>Compression</span>
                          <strong>
                            {volatilityContext?.compression ? "ACTIVE" : "NO"}
                          </strong>
                        </div>
                        <div>
                          <span>Volatility Confidence</span>
                          <strong>
                            {formatPercent(
                              volatilityContext?.confidence ??
                              volatility?.confidence
                            )}
                          </strong>
                        </div>
                        <div>
                          <span>Direction Impact</span>
                          <strong>NONE</strong>
                        </div>
                      </div>

                      <div className="qmi-volatility-context__explanation">
                        <div className="qmi-volatility-context__explanation-icon">
                          <ShieldAlert size={17} strokeWidth={1.8} />
                        </div>
                        <div>
                          <strong>How to read this</strong>
                          <span>
                            Volatility does not make the signal bullish or bearish.
                            It tells QMI how reliable and operationally stable the
                            current directional reading is. Direction remains driven
                            by the seven Confluence engines on the left.
                          </span>
                        </div>
                      </div>
                    </div>

              <section className="qmi-scenario">
            <div className="qmi-scenario__header">
              <div className="qmi-scenario__title">
                <div className="qmi-ta-icon-box">
                  <GitBranch size={19} strokeWidth={1.8} />
                </div>
                <div>
                  <span className="qmi-ta-kicker">DE-UI-009.0 · SCENARIO MATRIX</span>
                  <h2>QMI Technical Scenario Matrix</h2>
                </div>
              </div>
              <div className="qmi-scenario__primary">
                <span>Clear Primary</span>
                <strong>{scenarioMatrix.primary?.label || "--"}</strong>
              </div>
            </div>

            {decisionLoading && !technicalDecision ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building technical scenarios...
              </div>
            ) : decisionError ? (
              <div className="qmi-ta-alert">Scenario matrix unavailable: {decisionError}</div>
            ) : technicalDecision ? (
              <>
                <div className="qmi-scenario__grid">
                  {scenarioMatrix.scenarios.map((scenario) => (
                    <div
                      key={scenario.key}
                      className={`qmi-scenario__card is-${scenario.tone} ${
                        scenario.key === scenarioMatrix.primary?.key ? "is-primary" : ""
                      }`}
                    >
                      <div className="qmi-scenario__card-head">
                        <span>{scenario.label}</span>
                        <strong>{formatNumber(scenario.score, 1)}</strong>
                      </div>
                      <div className="qmi-scenario__bar">
                        <div style={{ width: `${clamp(scenario.score, 0, 100)}%` }} />
                      </div>
                      <div className="qmi-scenario__thesis">{scenario.thesis}</div>
                      <div className="qmi-scenario__facts">
                        <div className="qmi-scenario__fact">
                          <span>Trigger</span>
                          <strong>{scenario.trigger}</strong>
                        </div>
                        <div className="qmi-scenario__fact">
                          <span>Invalidation</span>
                          <strong>{scenario.invalidation}</strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="qmi-scenario__footer">
                  <div><span>Decision Confidence</span><strong>{formatPercent(scenarioMatrix.confidence)}</strong></div>
                  <div><span>Decision Readiness</span><strong>{formatPercent(scenarioMatrix.readiness)}</strong></div>
                  <div><span>Reversal Requirements</span><strong>{reversalRequirements.length || 0} active</strong></div>
                </div>
              </>
            ) : null}
          </section>
            </div>
          </div>

          <section className="qmi-action">
            <div className="qmi-action__header">
              <div className="qmi-action__title">
                <div className="qmi-ta-icon-box"><ShieldCheck size={19} strokeWidth={1.8} /></div>
                <div><span className="qmi-ta-kicker">DE-UI-010.0 · ACTION FRAMEWORK</span><h2>QMI Technical Action Framework</h2></div>
              </div>
              <div className="qmi-action__badge">{pretty(actionState)}</div>
            </div>

            {actionLoading && !actionFramework ? (
              <div className="qmi-ta-structure-status"><RefreshCw className="qmi-ta-spin" size={15} /> Building technical action framework...</div>
            ) : actionError ? (
              <div className="qmi-ta-alert">Action framework unavailable: {actionError}</div>
            ) : actionFramework ? (<>
              <div className="qmi-action__hero">
                <div className="qmi-action__card is-posture"><span>Action Posture</span><strong>{pretty(actionState)}</strong><small>{pretty(actionDirection)}{actionSeverity !== undefined ? ` · Severity ${formatNumber(actionSeverity,1)}` : ""}</small></div>
                <div className="qmi-action__card"><span>Action Readiness</span><strong>{formatPercent(actionReadinessScore)}</strong><small>{pretty(actionReadiness?.state || "Decision ready")}</small></div>
                <div className="qmi-action__card"><span>Quality Gate</span><strong>{pretty(actionQuality)}</strong><small>Execution-quality filter</small></div>
              </div>
              <div className="qmi-action__permissions">
                {[
                  ["New Long Exposure", actionPermission?.new_long_exposure, "blocked"],
                  ["Add Existing Long", actionPermission?.add_to_existing_long, "blocked"],
                  ["Risk Reduction", actionPermission?.risk_reduction, "permitted"],
                  ["Wait / Confirmation", actionPermission?.wait_for_confirmation || actionPermission?.wait, "preferred"]
                ].map(([label,value,tone]) => <div className={`qmi-action__permission is-${tone}`} key={label}><span>{label}</span><strong>{pretty(value)}</strong></div>)}
              </div>
              <div className="qmi-action__lists">
                <div className="qmi-action__list">
                  <span>Confirmation Gates</span>
                  <div className="qmi-action__items">
                    {actionGates.length ? actionGates.map((item, index) => (
                      <div className="qmi-action__item" key={`gate-${index}`}>
                        <div className="qmi-action__item-head">
                          <strong>{actionText(item?.gate || item?.requirement || `Gate ${index + 1}`)}</strong>
                          <em>{item?.priority ? `P${item.priority}` : actionText(item?.status)}</em>
                        </div>
                        {item?.target && <small>{actionText(item.target)}</small>}
                        <div className="qmi-action__item-meta">
                          {item?.engine && <b>{pretty(item.engine)}</b>}
                          {actionScore(item?.current_score) !== null && <b>Score {actionScore(item.current_score)}</b>}
                          {item?.status && <b>{pretty(item.status)}</b>}
                        </div>
                      </div>
                    )) : (
                      <div className="qmi-action__item"><small>No active confirmation gates</small></div>
                    )}
                  </div>
                </div>

                <div className="qmi-action__list">
                  <span>Entry Constraints</span>
                  <div className="qmi-action__items">
                    {entryConstraints.length ? entryConstraints.map((item, index) => (
                      <div className="qmi-action__item" key={`constraint-${index}`}>
                        <div className="qmi-action__item-head">
                          <strong>{pretty(item?.engine || item?.type || `Constraint ${index + 1}`)}</strong>
                          <em>{pretty(item?.severity)}</em>
                        </div>
                        {item?.constraint && <small>{actionText(item.constraint)}</small>}
                        <div className="qmi-action__item-meta">
                          {item?.type && <b>{pretty(item.type)}</b>}
                          {actionScore(item?.current_score) !== null && <b>Score {actionScore(item.current_score)}</b>}
                        </div>
                      </div>
                    )) : (
                      <div className="qmi-action__item"><small>No additional entry constraints</small></div>
                    )}
                  </div>
                </div>

                <div className="qmi-action__list">
                  <span>Invalidation Gates</span>
                  <div className="qmi-action__items">
                    {invalidationGates.length ? invalidationGates.map((item, index) => (
                      <div className="qmi-action__item" key={`invalid-${index}`}>
                        <div className="qmi-action__item-head">
                          <strong>{actionText(item?.condition || item?.gate || `Invalidation ${index + 1}`)}</strong>
                          <em>{item?.priority ? `P${item.priority}` : ""}</em>
                        </div>
                        {item?.status && (
                          <div className="qmi-action__item-meta">
                            <b>{pretty(item.status)}</b>
                          </div>
                        )}
                      </div>
                    )) : (
                      <div className="qmi-action__item"><small>No active invalidation gates</small></div>
                    )}
                  </div>
                </div>

                <div className="qmi-action__list">
                  <span>Escalation / Downgrade</span>

                  <div className="qmi-action__transition-group">
                    <b className="qmi-action__transition-title">Escalation</b>
                    <div className="qmi-action__items">
                      {escalationConditions.length ? escalationConditions.map((item, index) => (
                        <div className="qmi-action__item" key={`escalation-${index}`}>
                          <small>{actionText(typeof item === "string" ? item : item?.condition || item?.label || item?.name)}</small>
                        </div>
                      )) : <div className="qmi-action__item"><small>No escalation conditions</small></div>}
                    </div>
                  </div>

                  <div className="qmi-action__transition-group">
                    <b className="qmi-action__transition-title">Downgrade</b>
                    <div className="qmi-action__items">
                      {downgradeConditions.length ? downgradeConditions.map((item, index) => (
                        <div className="qmi-action__item" key={`downgrade-${index}`}>
                          <small>{actionText(typeof item === "string" ? item : item?.condition || item?.label || item?.name)}</small>
                        </div>
                      )) : <div className="qmi-action__item"><small>No downgrade conditions</small></div>}
                    </div>
                  </div>
                </div>
              </div>
            </>) : null}
          </section>

          <section className="qmi-risk">
            <div className="qmi-risk__header">
              <div className="qmi-risk__title">
                <div className="qmi-ta-icon-box"><ShieldAlert size={19} strokeWidth={1.8} /></div>
                <div><span className="qmi-ta-kicker">DE-UI-011.0 · RISK & EXPOSURE</span><h2>QMI Technical Risk & Exposure Gate</h2></div>
              </div>
              <div className="qmi-risk__badge">{pretty(riskState)}</div>
            </div>

            {riskExposureLoading && !riskExposure ? (
              <div className="qmi-ta-structure-status"><RefreshCw className="qmi-ta-spin" size={15} /> Building technical risk & exposure gate...</div>
            ) : riskExposureError ? (
              <div className="qmi-ta-alert">Risk & exposure gate unavailable: {riskExposureError}</div>
            ) : riskExposure ? (<>
              <div className="qmi-risk__hero">
                <div className="qmi-risk__card is-risk"><span>Risk Regime</span><strong>{pretty(riskState)}</strong><small>{pretty(riskDirection)}{riskScore !== undefined && riskScore !== null ? ` · Score ${formatNumber(riskScore,1)}` : ""}</small></div>
                <div className="qmi-risk__card">
                  <span>Exposure Gate</span>
                  <strong>{pretty(exposureState)}</strong>
                  <small>New Long · {exposureBand} technical band</small>
                </div>
                <div className="qmi-risk__card">
                  <span>Technical Budget</span>
                  <strong>{budgetState}</strong>
                  <small>{pretty(budgetPriority)} capital preservation</small>
                </div>
              </div>

              <div className="qmi-risk__grid">
                <div className="qmi-risk__panel">
                  <span>Protective Controls</span>
                  <div className="qmi-risk__items">
                    {protectiveControls.length ? protectiveControls.map((item,index) => (
                      <div className="qmi-risk__item" key={`risk-control-${index}`}>
                        <strong>{riskItemText(item, `Control ${index + 1}`)}</strong>
                        {typeof item !== "string" && item?.description && <small>{actionText(item.description)}</small>}
                        {typeof item !== "string" && <div className="qmi-risk__meta">{item?.status && <b>{pretty(item.status)}</b>}{item?.severity && <b>{pretty(item.severity)}</b>}{item?.priority && <b>P{item.priority}</b>}</div>}
                      </div>
                    )) : <div className="qmi-risk__item"><small>No active protective controls</small></div>}
                  </div>
                </div>

                <div className="qmi-risk__panel">
                  <span>Release Conditions</span>
                  <div className="qmi-risk__items">
                    {releaseConditions.length ? releaseConditions.map((item,index) => (
                      <div className="qmi-risk__item" key={`risk-release-${index}`}>
                        <strong>{riskItemText(item, `Release ${index + 1}`)}</strong>
                        {typeof item !== "string" && item?.description && <small>{actionText(item.description)}</small>}
                        {typeof item !== "string" && <div className="qmi-risk__meta">{item?.status && <b>{pretty(item.status)}</b>}{item?.priority && <b>P{item.priority}</b>}</div>}
                      </div>
                    )) : <div className="qmi-risk__item"><small>No release conditions reported</small></div>}
                  </div>
                </div>

                <div className="qmi-risk__panel">
                  <span>Escalation Conditions</span>
                  <div className="qmi-risk__items">
                    {riskEscalationConditions.length ? riskEscalationConditions.map((item,index) => (
                      <div className="qmi-risk__item" key={`risk-escalation-${index}`}>
                        <strong>{riskItemText(item, `Escalation ${index + 1}`)}</strong>
                        {typeof item !== "string" && item?.description && <small>{actionText(item.description)}</small>}
                        {typeof item !== "string" && <div className="qmi-risk__meta">{item?.status && <b>{pretty(item.status)}</b>}{item?.severity && <b>{pretty(item.severity)}</b>}</div>}
                      </div>
                    )) : <div className="qmi-risk__item"><small>No escalation conditions reported</small></div>}
                  </div>
                </div>
              </div>
            </>) : null}
          </section>


          <section className="qmi-sizing">
            <div className="qmi-sizing__header">
              <div className="qmi-sizing__title">
                <div className="qmi-ta-icon-box">
                  <Gauge size={19} strokeWidth={1.8} />
                </div>
                <div>
                  <span className="qmi-ta-kicker">
                    DE-UI-012.0 · POSITION SIZING
                  </span>
                  <h2>QMI Technical Position Sizing & Capital Allocation</h2>
                </div>
              </div>

              <div className="qmi-sizing__badge">
                {pretty(allocationState)}
              </div>
            </div>

            {positionSizingLoading && !positionSizing ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building technical position sizing...
              </div>
            ) : positionSizingError ? (
              <div className="qmi-ta-alert">
                Position sizing unavailable: {positionSizingError}
              </div>
            ) : positionSizing ? (
              <>
                <div className="qmi-sizing__hero">
                  <div className="qmi-sizing__card is-allocation">
                    <span>Allocation Regime</span>
                    <strong>{pretty(allocationState)}</strong>
                    <small>{pretty(allocationPriority)} priority</small>
                  </div>

                  <div className="qmi-sizing__card">
                    <span>Maximum Technical Exposure</span>
                    <strong>{maxExposureBand}</strong>
                    <small>{pretty(maxExposurePriority)} capital preservation</small>
                  </div>

                  <div className="qmi-sizing__card">
                    <span>New Entry</span>
                    <strong>{newEntryBand}</strong>
                    <small>{pretty(newEntryState)}</small>
                  </div>

                  <div className="qmi-sizing__card">
                    <span>Add-On Capacity</span>
                    <strong>{addOnBand}</strong>
                    <small>{pretty(addOnState)}</small>
                  </div>
                </div>

                <div className="qmi-sizing__grid">
                  <div className="qmi-sizing__panel">
                    <span>Capital Controls</span>
                    <div className="qmi-sizing__items">
                      <div className="qmi-sizing__item">
                        <strong>Risk Reduction · {pretty(reductionPermission)}</strong>
                        <small>{pretty(reductionPreference)} preference</small>
                      </div>

                      <div className="qmi-sizing__item">
                        <strong>Cash Preference · {pretty(cashState)}</strong>
                        <small>{pretty(cashPreference?.rationale)}</small>
                      </div>

                      <div className="qmi-sizing__item">
                        <strong>Leverage · {pretty(leverageState)}</strong>
                        <small>Technical leverage policy</small>
                      </div>
                    </div>
                  </div>

                  <div className="qmi-sizing__panel">
                    <span>Sizing Confidence</span>
                    <div className="qmi-sizing__items">
                      <div className="qmi-sizing__item">
                        <strong>
                          {sizingConfidenceScore !== undefined &&
                          sizingConfidenceScore !== null
                            ? `${formatNumber(sizingConfidenceScore, 1)}%`
                            : "--"}
                        </strong>
                        <small>{pretty(sizingConfidenceState)}</small>
                      </div>

                      <div className="qmi-sizing__item">
                        <strong>
                          Primary Scenario · {actionText(sizingContext?.primary_scenario)}
                        </strong>
                        <small>
                          {pretty(sizingContext?.primary_direction)} · Score{" "}
                          {sizingContext?.primary_score !== undefined
                            ? formatNumber(sizingContext.primary_score, 1)
                            : "--"}
                        </small>
                      </div>
                    </div>
                  </div>

                  <div className="qmi-sizing__panel">
                    <span>Source Context</span>
                    <div className="qmi-sizing__items">
                      <div className="qmi-sizing__item">
                        <strong>Risk · {pretty(sizingContext?.risk_state)}</strong>
                        <small>
                          Score{" "}
                          {sizingContext?.risk_score !== undefined
                            ? formatNumber(sizingContext.risk_score, 1)
                            : "--"}
                        </small>
                      </div>

                      <div className="qmi-sizing__item">
                        <strong>
                          Direction ·{" "}
                          {sizingContext?.direction_score !== undefined
                            ? formatScore(sizingContext.direction_score)
                            : "--"}
                        </strong>
                        <small>
                          Action Readiness{" "}
                          {sizingContext?.action_readiness !== undefined
                            ? formatPercent(sizingContext.action_readiness)
                            : "--"}
                        </small>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </section>


          <section className="qmi-execution">
            <div className="qmi-execution__header">
              <div className="qmi-execution__title">
                <div className="qmi-ta-icon-box">
                  <ShieldCheck size={19} strokeWidth={1.8} />
                </div>
                <div>
                  <span className="qmi-ta-kicker">
                    DE-UI-013.0 · EXECUTION PLAN
                  </span>
                  <h2>QMI Technical Execution Plan</h2>
                </div>
              </div>

              <div className="qmi-execution__badge">
                {pretty(executionStateName)}
              </div>
            </div>

            {executionPlanLoading && !executionPlan ? (
              <div className="qmi-ta-structure-status">
                <RefreshCw className="qmi-ta-spin" size={15} />
                Building technical execution plan...
              </div>
            ) : executionPlanError ? (
              <div className="qmi-ta-alert">
                Execution plan unavailable: {executionPlanError}
              </div>
            ) : executionPlan ? (
              <>
                <div className="qmi-execution__hero">
                  <div className="qmi-execution__card is-state">
                    <span>Execution State</span>
                    <strong>{pretty(executionStateName)}</strong>
                    <small>{pretty(executionBias)} · Risk {pretty(executionRiskState)}</small>
                  </div>

                  <div className="qmi-execution__card is-wait">
                    <span>Wait</span>
                    <strong>{pretty(waitAction?.state)}</strong>
                    <small>{pretty(waitAction?.priority)} priority</small>
                  </div>

                  <div className="qmi-execution__card is-enter">
                    <span>Enter</span>
                    <strong>{pretty(enterAction?.state)}</strong>
                    <small>{enterAction?.technical_band || "--"} technical band</small>
                  </div>

                  <div className="qmi-execution__card is-add">
                    <span>Add</span>
                    <strong>{pretty(addAction?.state)}</strong>
                    <small>{addAction?.technical_band || "--"} technical band</small>
                  </div>

                  <div className="qmi-execution__card is-reduce">
                    <span>Reduce</span>
                    <strong>{pretty(reduceAction?.state)}</strong>
                    <small>{pretty(reduceAction?.preference)} preference</small>
                  </div>

                  <div className="qmi-execution__card">
                    <span>Exit</span>
                    <strong>{pretty(exitAction?.state)}</strong>
                    <small>{actionText(exitAction?.trigger)}</small>
                  </div>
                </div>

                <div className="qmi-execution__grid">
                  <div className="qmi-execution__panel">
                    <span>Activation Conditions</span>
                    <div className="qmi-execution__items">
                      {activationConditions.length ? activationConditions.map((item,index) => (
                        <div className="qmi-execution__item" key={`exec-activation-${index}`}>
                          <strong>{actionText(item?.condition || `Condition ${index + 1}`)}</strong>
                          <small>{actionText(item?.target)}</small>
                          <div className="qmi-execution__meta">
                            {item?.priority && <b>P{item.priority}</b>}
                            {item?.engine && <b>{pretty(item.engine)}</b>}
                            {item?.status && <b>{pretty(item.status)}</b>}
                          </div>
                        </div>
                      )) : <div className="qmi-execution__item"><small>No activation conditions</small></div>}
                    </div>
                  </div>

                  <div className="qmi-execution__panel">
                    <span>Invalidation Conditions</span>
                    <div className="qmi-execution__items">
                      {executionInvalidations.length ? executionInvalidations.map((item,index) => (
                        <div className="qmi-execution__item" key={`exec-invalid-${index}`}>
                          <strong>{actionText(item?.condition)}</strong>
                          <div className="qmi-execution__meta">
                            {item?.priority && <b>P{item.priority}</b>}
                            {item?.status && <b>{pretty(item.status)}</b>}
                          </div>
                        </div>
                      )) : <div className="qmi-execution__item"><small>No invalidation conditions</small></div>}
                    </div>
                  </div>

                  <div className="qmi-execution__panel">
                    <span>Escalation / De-escalation</span>
                    <div className="qmi-execution__items">
                      {executionEscalation.slice(0,4).map((item,index) => (
                        <div className="qmi-execution__item" key={`exec-esc-${index}`}>
                          <strong>Escalation</strong>
                          <small>{actionText(item)}</small>
                        </div>
                      ))}
                      {executionDeescalation.slice(0,4).map((item,index) => (
                        <div className="qmi-execution__item" key={`exec-deesc-${index}`}>
                          <strong>De-escalation</strong>
                          <small>{actionText(item)}</small>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="qmi-execution__panel">
                    <span>Execution Confidence</span>
                    <div className="qmi-execution__items">
                      <div className="qmi-execution__item">
                        <strong>
                          {executionConfidence?.score !== undefined
                            ? `${formatNumber(executionConfidence.score,1)}%`
                            : "--"}
                        </strong>
                        <small>{pretty(executionConfidence?.state)}</small>
                      </div>

                      <div className="qmi-execution__item">
                        <strong>{pretty(allocationContext?.allocation_regime)}</strong>
                        <small>
                          Max exposure {allocationContext?.maximum_technical_exposure || "--"} ·
                          Cash {pretty(allocationContext?.cash_preference)} ·
                          Leverage {pretty(allocationContext?.leverage)}
                        </small>
                      </div>

                      <div className="qmi-execution__item">
                        <strong>{actionText(executionContext?.primary_scenario)}</strong>
                        <small>
                          Direction {executionContext?.direction_score !== undefined
                            ? formatScore(executionContext.direction_score)
                            : "--"} ·
                          Risk {pretty(executionContext?.risk_state)}
                        </small>
                      </div>
                    </div>
                  </div>
                </div>
              </>
            ) : null}
          </section>

          <section className="qmi-state-monitor">
            <div className="qmi-state-monitor__header">
              <div className="qmi-state-monitor__title">
                <div className="qmi-ta-icon-box"><Activity size={19} strokeWidth={1.8} /></div>
                <div><span className="qmi-ta-kicker">DE-UI-014.x · TECHNICAL STATE MONITOR</span><h2>QMI Technical State Monitor</h2></div>
              </div>
              <div className="qmi-state-monitor__badge">{pretty(confirmationDecision014)}</div>
            </div>
            {stateMonitorLoading && !stateTransition ? (
              <div className="qmi-ta-structure-status"><RefreshCw className="qmi-ta-spin" size={15} />Building technical state monitor...</div>
            ) : stateMonitorError ? (
              <div className="qmi-ta-alert">State monitor unavailable: {stateMonitorError}</div>
            ) : (<>
              <div className="qmi-state-monitor__flow">
                <div className="qmi-state-monitor__card is-current"><span>Current State</span><strong>{pretty(stateCurrentName014)}</strong><small>{consecutive014} consecutive snapshots</small></div>
                <div className="qmi-state-monitor__arrow">→</div>
                <div className="qmi-state-monitor__card is-next"><span>Next State Candidate</span><strong>{pretty(stateNextName014)}</strong><small>Transition target</small></div>
                <div className="qmi-state-monitor__card"><span>Transition Probability</span><strong>{transitionProbability014 !== undefined && transitionProbability014 !== null ? `${formatNumber(transitionProbability014,1)}%` : "--"}</strong><small>{pretty(maturityAssessment014?.status)}</small></div>
                <div className="qmi-state-monitor__card"><span>Maturity</span><strong>{pretty(maturityPhase014)}</strong><small>Score {maturityCurrent014?.maturity_score !== undefined ? formatNumber(maturityCurrent014.maturity_score,1) : "--"}</small></div>
                <div className="qmi-state-monitor__card"><span>Persistence</span><strong>{persistenceScore014 !== undefined && persistenceScore014 !== null ? formatNumber(persistenceScore014,1) : "--"}</strong><small>{pretty(persistenceStrength014?.state)}</small></div>
                <div className="qmi-state-monitor__card is-confirm"><span>Confirmation</span><strong>{pretty(confirmationDecision014)}</strong><small>Score {confirmationScore014 !== undefined && confirmationScore014 !== null ? formatNumber(confirmationScore014,1) : "--"}</small></div>
              </div>
              <div className="qmi-state-monitor__footer">
                <div className="qmi-state-monitor__strip"><span>Transition Readiness</span><strong>{readinessScore014 !== undefined && readinessScore014 !== null ? `${formatNumber(readinessScore014,1)}%` : "--"}</strong><strong>· Stability {regimeStability014?.score !== undefined ? `${formatNumber(regimeStability014.score,1)}%` : "--"}</strong></div>
                <div className="qmi-state-monitor__strip"><span>Blockers</span>{confirmationBlockers014.length ? <div className="qmi-state-monitor__blockers">{confirmationBlockers014.slice(0,5).map((item,index)=><div className="qmi-state-monitor__blocker" key={`state-blocker-${index}`}>{pretty(item?.severity)} · {actionText(item?.reason)}</div>)}</div> : <strong>No active transition blockers</strong>}</div>
              </div>
            </>)}
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

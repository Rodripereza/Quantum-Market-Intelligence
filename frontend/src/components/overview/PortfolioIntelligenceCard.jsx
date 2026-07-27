import SectionHeader from "../ui/SectionHeader";

import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  CircleAlert,
  Gauge,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

function clamp(value, minimum = 0, maximum = 100) {
  const number = Number(value);

  if (Number.isNaN(number)) {
    return minimum;
  }

  return Math.min(maximum, Math.max(minimum, number));
}

function normalizeText(value, fallback) {
  if (
    value === null ||
    value === undefined ||
    String(value).trim() === ""
  ) {
    return fallback;
  }

  return String(value).trim();
}

function resolveTone(value) {
  const normalized = String(value).toLowerCase();

  if (
    normalized.includes("bull") ||
    normalized.includes("positive") ||
    normalized.includes("strong") ||
    normalized.includes("buy") ||
    normalized.includes("low") ||
    normalized.includes("holding") ||
    normalized.includes("confirmed")
  ) {
    return "positive";
  }

  if (
    normalized.includes("bear") ||
    normalized.includes("negative") ||
    normalized.includes("sell") ||
    normalized.includes("high") ||
    normalized.includes("weak") ||
    normalized.includes("broken")
  ) {
    return "negative";
  }

  if (
    normalized.includes("warning") ||
    normalized.includes("moderate") ||
    normalized.includes("watch") ||
    normalized.includes("mixed") ||
    normalized.includes("neutral")
  ) {
    return "warning";
  }

  return "neutral";
}

function InsightRow({
  icon: Icon,
  label,
  value,
  tone = "neutral",
}) {
  return (
    <div className="ai-insight-row">
      <div className={`ai-insight-row-icon ${tone}`}>
        <Icon size={15} strokeWidth={1.9} />
      </div>

      <div className="ai-insight-row-copy">
        <span>{label}</span>
        <strong className={tone}>{value}</strong>
      </div>
    </div>
  );
}

function PortfolioIntelligenceCard({
  portfolio,
  ai,
}) {
  const safePortfolio = portfolio ?? {};
  const safeAi = ai ?? {};

  const aiConfidence = clamp(
    safeAi.confidence ??
      safeAi.confidence_score ??
      safePortfolio.ai_confidence ??
      84
  );

  const aiOutlook = normalizeText(
    safeAi.outlook ??
      safeAi.market_outlook ??
      safeAi.signal ??
      safePortfolio.ai_outlook,
    "Bullish"
  );

  const momentum = normalizeText(
    safeAi.momentum ??
      safeAi.momentum_state ??
      safePortfolio.momentum_state,
    "Positive"
  );

  const trend = normalizeText(
    safeAi.trend ??
      safeAi.trend_state ??
      safePortfolio.trend_state,
    "Confirmed"
  );

  const riskLevel = normalizeText(
    safeAi.risk_level ??
      safePortfolio.risk_level ??
      (
        Number(safePortfolio.risk_score ?? 42) >= 70
          ? "High"
          : Number(safePortfolio.risk_score ?? 42) >= 45
            ? "Moderate"
            : "Low"
      ),
    "Low"
  );

  const support = normalizeText(
    safeAi.support ??
      safeAi.support_state ??
      safePortfolio.support_state,
    "Holding"
  );

  const earnings = normalizeText(
    safeAi.earnings ??
      safeAi.earnings_state ??
      safePortfolio.earnings_state,
    "Watch"
  );

  const summary = normalizeText(
    safeAi.summary ??
      safePortfolio.ai_summary,
    "Momentum remains constructive while portfolio risk stays inside the current operating range."
  );

  const outlookTone = resolveTone(aiOutlook);
  const momentumTone = resolveTone(momentum);
  const trendTone = resolveTone(trend);
  const riskTone = resolveTone(riskLevel);
  const supportTone = resolveTone(support);
  const earningsTone = resolveTone(earnings);

  return (
    <aside className="institutional-intelligence-panel ai-insights-panel">
      <SectionHeader
        size="compact"
        eyebrow="QMI Intelligence"
        title="AI Insights"
        actions={
          <div className="ai-insights-live">
            <span />
            Live
          </div>
        }
      />

      <section className="ai-insights-outlook">
        <div className={`ai-insights-orb ${outlookTone}`}>
          <BrainCircuit size={23} strokeWidth={1.75} />
        </div>

        <div className="ai-insights-outlook-copy">
          <span>Portfolio outlook</span>

          <strong className={outlookTone}>
            {aiOutlook}
          </strong>
        </div>

        <span className={`ai-insights-badge ${outlookTone}`}>
          {aiConfidence.toFixed(0)}%
        </span>
      </section>

      <section className="ai-insights-list">
        <InsightRow
          icon={TrendingUp}
          label="Momentum"
          value={momentum}
          tone={momentumTone}
        />

        <InsightRow
          icon={Activity}
          label="Trend"
          value={trend}
          tone={trendTone}
        />

        <InsightRow
          icon={Gauge}
          label="Risk level"
          value={riskLevel}
          tone={riskTone}
        />

        <InsightRow
          icon={CheckCircle2}
          label="Support"
          value={support}
          tone={supportTone}
        />

        <InsightRow
          icon={CircleAlert}
          label="Earnings"
          value={earnings}
          tone={earningsTone}
        />
      </section>

      <section className="ai-insights-summary">
        <div className="ai-insights-summary-heading">
          <Sparkles size={14} />
          <span>AI interpretation</span>
        </div>

        <p>{summary}</p>
      </section>

      <section className="ai-insights-confidence">
        <div className="ai-insights-confidence-heading">
          <span>Confidence</span>
          <strong>{aiConfidence.toFixed(0)}%</strong>
        </div>

        <div className="ai-insights-confidence-track">
          <span
            style={{
              width: `${aiConfidence}%`,
            }}
          />
        </div>
      </section>

      <footer className="ai-insights-footer">
        <ShieldCheck size={14} />
        Intelligence layer operational
      </footer>
    </aside>
  );
}

export default PortfolioIntelligenceCard;
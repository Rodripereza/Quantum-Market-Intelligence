import {
  Activity,
  BrainCircuit,
  BriefcaseBusiness,
  Gauge,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

function formatNumber(value, decimals = 2) {
  const number = Number(value);

  if (Number.isNaN(number)) {
    return "--";
  }

  return number.toFixed(decimals);
}

function IntelligenceMetric({
  icon: Icon,
  label,
  value,
  tone = "neutral",
}) {
  return (
    <div className="terminal-metric">
      <div className={`terminal-metric-icon ${tone}`}>
        <Icon size={16} />
      </div>

      <div>
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

  const riskScore = Math.min(
    100,
    Math.max(
      0,
      Number(safePortfolio.risk_score ?? 73)
    )
  );

  const sharpeRatio = Number(
    safePortfolio.sharpe_ratio ?? 1.81
  );

  const beta = Number(
    safePortfolio.beta ?? 0.92
  );

  const volatility = Number(
    safePortfolio.volatility ?? 17.4
  );

  const activePositions = Number(
    safePortfolio.position_count ?? 0
  );

  const aiConfidence = Math.min(
    100,
    Math.max(
      0,
      Number(
        safeAi.confidence ??
          safePortfolio.ai_confidence ??
          84
      )
    )
  );

  const aiOutlook =
    safeAi.outlook ??
    safePortfolio.ai_outlook ??
    "Bullish";

  const summary =
    safeAi.summary ??
    safePortfolio.ai_summary ??
    "Portfolio conditions remain constructive. Momentum, diversification and risk remain inside the current operating range.";

  const riskTone =
    riskScore >= 80
      ? "negative"
      : riskScore >= 60
        ? "warning"
        : "positive";

  const volatilityTone =
    volatility >= 30
      ? "negative"
      : volatility >= 20
        ? "warning"
        : "positive";

  const outlookTone =
    aiOutlook.toLowerCase().includes("bull")
      ? "positive"
      : aiOutlook.toLowerCase().includes("bear")
        ? "negative"
        : "warning";

  return (
    <aside className="institutional-intelligence-panel">
      <header className="institutional-panel-header">
        <div>
          <span className="institutional-panel-kicker">
            PORTFOLIO CONTROL
          </span>

          <h2>Risk & Intelligence</h2>
        </div>

        <div className="institutional-live-status">
          <span />
          Live
        </div>
      </header>

      <section className="institutional-risk-summary">
        <div
          className={`institutional-risk-score ${riskTone}`}
        >
          <span>Risk score</span>

          <strong>{riskScore}</strong>

          <small>/ 100</small>
        </div>

        <div className="institutional-risk-copy">
          <span>Current classification</span>

          <strong className={riskTone}>
            {riskScore >= 80
              ? "Elevated"
              : riskScore >= 60
                ? "Moderate"
                : "Controlled"}
          </strong>

          <small>
            Exposure, concentration and volatility
          </small>
        </div>
      </section>

      <section className="terminal-metrics-grid">
        <IntelligenceMetric
          icon={TrendingUp}
          label="Sharpe ratio"
          value={formatNumber(sharpeRatio)}
          tone={
            sharpeRatio >= 1
              ? "positive"
              : "warning"
          }
        />

        <IntelligenceMetric
          icon={Gauge}
          label="Portfolio beta"
          value={formatNumber(beta)}
        />

        <IntelligenceMetric
          icon={Activity}
          label="Volatility"
          value={`${formatNumber(volatility, 1)}%`}
          tone={volatilityTone}
        />

        <IntelligenceMetric
          icon={BriefcaseBusiness}
          label="Positions"
          value={activePositions}
        />
      </section>

      <section className="institutional-ai-summary">
        <div className="institutional-ai-heading">
          <div className="institutional-ai-icon">
            <BrainCircuit size={17} />
          </div>

          <div>
            <span>AI portfolio outlook</span>

            <strong className={outlookTone}>
              {aiOutlook}
            </strong>
          </div>

          <span
            className={`institutional-outlook-badge ${outlookTone}`}
          >
            {aiConfidence}%
          </span>
        </div>

        <p>{summary}</p>

        <div className="institutional-confidence">
          <div>
            <span>Confidence</span>
            <strong>{aiConfidence}%</strong>
          </div>

          <div className="institutional-confidence-track">
            <span
              style={{
                width: `${aiConfidence}%`,
              }}
            />
          </div>
        </div>
      </section>

      <footer className="institutional-panel-footer">
        <ShieldCheck size={14} />

        <span>Risk governance operational</span>
      </footer>
    </aside>
  );
}

export default PortfolioIntelligenceCard;
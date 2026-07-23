import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  CircleMinus,
  Gauge,
} from "lucide-react";

const FALLBACK_BREADTH = {
  advancing: 312,
  declining: 168,
  unchanged: 42,
  aboveSma50: 67,
  aboveSma200: 58,
  newHighs: 34,
  newLows: 11,
};

function clamp(value, min = 0, max = 100) {
  return Math.min(max, Math.max(min, Number(value) || 0));
}

function BreadthMetric({
  icon: Icon,
  label,
  value,
  detail,
  tone = "neutral",
}) {
  return (
    <div className="market-breadth-metric">
      <div className={`market-breadth-metric-icon ${tone}`}>
        <Icon size={16} />
      </div>

      <div>
        <span>{label}</span>
        <strong className={tone}>{value}</strong>
        <small>{detail}</small>
      </div>
    </div>
  );
}

function MarketBreadthCard({ breadth }) {
  const safeBreadth = breadth ?? FALLBACK_BREADTH;

  const advancing = Number(
    safeBreadth.advancing ?? FALLBACK_BREADTH.advancing
  );

  const declining = Number(
    safeBreadth.declining ?? FALLBACK_BREADTH.declining
  );

  const unchanged = Number(
    safeBreadth.unchanged ?? FALLBACK_BREADTH.unchanged
  );

  const aboveSma50 = clamp(
    safeBreadth.aboveSma50 ?? FALLBACK_BREADTH.aboveSma50
  );

  const aboveSma200 = clamp(
    safeBreadth.aboveSma200 ?? FALLBACK_BREADTH.aboveSma200
  );

  const newHighs = Number(
    safeBreadth.newHighs ?? FALLBACK_BREADTH.newHighs
  );

  const newLows = Number(
    safeBreadth.newLows ?? FALLBACK_BREADTH.newLows
  );

  const totalAssets =
    advancing + declining + unchanged || 1;

  const advancingPercentage =
    (advancing / totalAssets) * 100;

  const decliningPercentage =
    (declining / totalAssets) * 100;

  const unchangedPercentage =
    (unchanged / totalAssets) * 100;

  const breadthScore = clamp(
    advancingPercentage * 0.55 +
      aboveSma50 * 0.25 +
      aboveSma200 * 0.2
  );

  const breadthTone =
    breadthScore >= 65
      ? "positive"
      : breadthScore >= 45
        ? "warning"
        : "negative";

  const breadthState =
    breadthScore >= 70
      ? "Strong participation"
      : breadthScore >= 55
        ? "Constructive"
        : breadthScore >= 40
          ? "Mixed participation"
          : "Weak participation";

  const highLowBalance = newHighs - newLows;

  return (
    <section className="overview-surface market-breadth-card">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            MARKET PARTICIPATION
          </span>

          <h2>Market Breadth</h2>

          <p>
            Participation, trend health and internal market strength
          </p>
        </div>

        <div className={`market-breadth-state ${breadthTone}`}>
          <Gauge size={15} />
          {breadthState}
        </div>
      </div>

      <div className="market-breadth-main">
        <div className="market-breadth-score-panel">
          <div
            className={`market-breadth-score ${breadthTone}`}
            style={{
              "--breadth-progress": `${breadthScore * 3.6}deg`,
            }}
          >
            <div>
              <strong>{Math.round(breadthScore)}</strong>
              <span>/100</span>
            </div>
          </div>

          <div className="market-breadth-score-copy">
            <span>Breadth score</span>

            <strong className={breadthTone}>
              {breadthState}
            </strong>

            <small>
              Composite signal based on participation and trend
              confirmation
            </small>
          </div>
        </div>

        <div className="market-breadth-distribution">
          <div className="market-breadth-distribution-header">
            <span>Market distribution</span>
            <strong>{totalAssets} assets</strong>
          </div>

          <div className="market-breadth-bar">
            <span
              className="advancing"
              style={{ width: `${advancingPercentage}%` }}
            />

            <span
              className="unchanged"
              style={{ width: `${unchangedPercentage}%` }}
            />

            <span
              className="declining"
              style={{ width: `${decliningPercentage}%` }}
            />
          </div>

          <div className="market-breadth-legend">
            <div>
              <span className="positive" />
              <strong>{advancing}</strong>
              <small>
                Advancing · {advancingPercentage.toFixed(1)}%
              </small>
            </div>

            <div>
              <span className="neutral" />
              <strong>{unchanged}</strong>
              <small>
                Unchanged · {unchangedPercentage.toFixed(1)}%
              </small>
            </div>

            <div>
              <span className="negative" />
              <strong>{declining}</strong>
              <small>
                Declining · {decliningPercentage.toFixed(1)}%
              </small>
            </div>
          </div>
        </div>
      </div>

      <div className="market-breadth-metrics-grid">
        <BreadthMetric
          icon={ArrowUpRight}
          label="Above SMA 50"
          value={`${aboveSma50.toFixed(0)}%`}
          detail="Short-term trend participation"
          tone={
            aboveSma50 >= 60
              ? "positive"
              : aboveSma50 >= 45
                ? "warning"
                : "negative"
          }
        />

        <BreadthMetric
          icon={Activity}
          label="Above SMA 200"
          value={`${aboveSma200.toFixed(0)}%`}
          detail="Long-term trend confirmation"
          tone={
            aboveSma200 >= 60
              ? "positive"
              : aboveSma200 >= 45
                ? "warning"
                : "negative"
          }
        />

        <BreadthMetric
          icon={ArrowUpRight}
          label="New highs"
          value={newHighs}
          detail="Assets reaching fresh highs"
          tone="positive"
        />

        <BreadthMetric
          icon={ArrowDownRight}
          label="New lows"
          value={newLows}
          detail="Assets reaching fresh lows"
          tone={newLows > newHighs ? "negative" : "neutral"}
        />
      </div>

      <div className="market-breadth-footer">
        <div>
          <CircleMinus size={14} />
          <span>High / low balance</span>

          <strong
            className={
              highLowBalance > 0
                ? "positive"
                : highLowBalance < 0
                  ? "negative"
                  : "neutral"
            }
          >
            {highLowBalance > 0 ? "+" : ""}
            {highLowBalance}
          </strong>
        </div>

        <div>
          <Activity size={14} />
          <span>Participation spread</span>

          <strong className={breadthTone}>
            {(advancingPercentage - decliningPercentage).toFixed(1)}%
          </strong>
        </div>
      </div>
    </section>
  );
}

export default MarketBreadthCard;
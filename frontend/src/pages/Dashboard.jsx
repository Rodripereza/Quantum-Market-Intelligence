import MetricCard from "../components/ui/MetricCard";
import "./Dashboard.css";


const PORTFOLIO_HISTORY_PERIODS = [
  { label: "1M", value: "1mo" },
  { label: "3M", value: "3mo" },
  { label: "6M", value: "6mo" },
  { label: "YTD", value: "ytd" },
  { label: "1Y", value: "1y" },
  { label: "3Y", value: "3y" },
  { label: "MAX", value: "max" },
];

function getHistoryPeriodLabel(period) {
  return (
    PORTFOLIO_HISTORY_PERIODS.find(
      (item) => item.value === period
    )?.label ?? String(period || "").toUpperCase()
  );
}

/* =========================================================
   QMI — INSTITUTIONAL DASHBOARD
   Sprint 008 · Real Portfolio Metrics
   ========================================================= */

function toFiniteNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function money(value, currency = "USD") {
  const number = toFiniteNumber(value);

  if (number === null) {
    return "--";
  }

  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
}

function percentage(value, options = {}) {
  const {
    showPositiveSign = true,
    maximumFractionDigits = 2,
  } = options;

  const number = toFiniteNumber(value);

  if (number === null) {
    return "--";
  }

  const prefix = showPositiveSign && number > 0 ? "+" : "";

  return `${prefix}${number.toLocaleString("es-ES", {
    minimumFractionDigits: maximumFractionDigits,
    maximumFractionDigits,
  })}%`;
}

function compactPercentage(value) {
  const number = toFiniteNumber(value);

  if (number === null) {
    return "--";
  }

  return `${number.toLocaleString("es-ES", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })}%`;
}

function getStatusFromValue(value) {
  const number = toFiniteNumber(value);

  if (number === null || number === 0) {
    return "neutral";
  }

  return number > 0 ? "positive" : "negative";
}

function getConcentrationStatus(weight) {
  const number = toFiniteNumber(weight);

  if (number === null) {
    return "neutral";
  }

  if (number >= 60) {
    return "negative";
  }

  if (number >= 35) {
    return "warning";
  }

  return "positive";
}

function getConcentrationLabel(weight) {
  const number = toFiniteNumber(weight);

  if (number === null) {
    return "Unavailable";
  }

  if (number >= 60) {
    return "High concentration";
  }

  if (number >= 35) {
    return "Moderate concentration";
  }

  return "Diversified";
}

function resolvePortfolioCurrency(portfolio) {
  const explicitCurrency =
    portfolio?.currency ??
    portfolio?.summary?.currency ??
    null;

  if (explicitCurrency) {
    return explicitCurrency;
  }

  const positions = Array.isArray(portfolio?.positions)
    ? portfolio.positions
    : [];

  const currencies = [
    ...new Set(
      positions
        .map((position) => position?.currency)
        .filter(Boolean),
    ),
  ];

  if (currencies.length === 1) {
    return currencies[0];
  }

  return "USD";
}

function calculateDailyMetrics(portfolio) {
  const positions = Array.isArray(portfolio?.positions)
    ? portfolio.positions
    : [];

  let dailyProfitLoss = 0;
  let previousMarketValue = 0;
  let coveredPositions = 0;

  positions.forEach((position) => {
    const shares = toFiniteNumber(
      position?.shares ?? position?.quantity,
    );

    const currentPrice = toFiniteNumber(
      position?.current_price,
    );

    const previousClose = toFiniteNumber(
      position?.previous_close,
    );

    if (
      shares === null ||
      currentPrice === null ||
      previousClose === null
    ) {
      return;
    }

    dailyProfitLoss +=
      (currentPrice - previousClose) * shares;

    previousMarketValue += previousClose * shares;
    coveredPositions += 1;
  });

  if (coveredPositions === 0) {
    return {
      dailyProfitLoss: null,
      dailyReturn: null,
      coveredPositions: 0,
    };
  }

  const dailyReturn =
    previousMarketValue > 0
      ? (dailyProfitLoss / previousMarketValue) * 100
      : null;

  return {
    dailyProfitLoss,
    dailyReturn,
    coveredPositions,
  };
}

function normalizeWatchlist(market) {
  const assets =
    market?.assets ??
    market?.watchlist ??
    market?.items ??
    [];

  if (!Array.isArray(assets)) {
    return [];
  }

  return assets.slice(0, 6).map((asset, index) => {
    const ticker =
      asset?.ticker ??
      asset?.symbol ??
      asset?.code ??
      `ASSET-${index + 1}`;

    const company =
      asset?.company ??
      asset?.name ??
      asset?.description ??
      ticker;

    const price =
      asset?.price ??
      asset?.current_price ??
      asset?.last_price ??
      asset?.close;

    const change =
      asset?.change_pct ??
      asset?.change_percent ??
      asset?.percentage_change ??
      asset?.daily_change_pct;

    const normalizedChange = toFiniteNumber(change);

    return {
      ticker,
      company,
      price:
        toFiniteNumber(price) !== null
          ? money(price, asset?.currency ?? "USD")
          : "--",
      change:
        normalizedChange !== null
          ? percentage(normalizedChange)
          : "--",
      status: getStatusFromValue(normalizedChange),
    };
  });
}

function normalizeAllocation(portfolio) {
  const allocation =
    portfolio?.sector_allocation ??
    portfolio?.allocation ??
    portfolio?.summary?.sector_allocation ??
    [];

  if (!Array.isArray(allocation)) {
    return [];
  }

  return allocation.slice(0, 6).map((item, index) => ({
    label:
      item?.sector ??
      item?.label ??
      item?.name ??
      `Allocation ${index + 1}`,
    value:
      toFiniteNumber(
        item?.weight ??
          item?.percentage ??
          item?.value_pct ??
          item?.allocation,
      ) ?? 0,
  }));
}

function normalizeInsights(ai) {
  const insights =
    ai?.insights ??
    ai?.signals ??
    ai?.recommendations ??
    [];

  if (!Array.isArray(insights)) {
    return [];
  }

  return insights.slice(0, 3).map((insight, index) => ({
    type:
      insight?.type ??
      insight?.category ??
      insight?.signal ??
      "Insight",
    title:
      insight?.title ??
      insight?.name ??
      `AI insight ${index + 1}`,
    description:
      insight?.description ??
      insight?.message ??
      insight?.summary ??
      "No additional information is available.",
    status: [
      "positive",
      "negative",
      "warning",
      "neutral",
    ].includes(insight?.status)
      ? insight.status
      : "neutral",
  }));
}

function normalizeNews(market) {
  const news =
    market?.news ??
    market?.headlines ??
    market?.articles ??
    [];

  if (!Array.isArray(news)) {
    return [];
  }

  return news.slice(0, 4).map((item) => ({
    source:
      item?.source ??
      item?.category ??
      item?.publisher ??
      "MARKET",
    time:
      item?.time ??
      item?.published_time ??
      item?.publishedAt ??
      "--",
    title:
      item?.title ??
      item?.headline ??
      item?.summary ??
      "Market update unavailable",
  }));
}


function buildHistoryChart(history, benchmark = []) {
  if (!Array.isArray(history) || history.length < 2) {
    return null;
  }

  const width = 700;
  const height = 220;
  const topPadding = 18;
  const bottomPadding = 26;

  // Portfolio:
  // Prefer backend base-100 values. If they are unavailable,
  // normalize market_value locally so the chart never disappears.
  const rawPortfolio = history
    .map((point) => ({
      date: point?.date ?? "",
      normalized: toFiniteNumber(point?.normalized_value),
      marketValue: toFiniteNumber(point?.market_value),
    }))
    .filter(
      (point) =>
        point.date &&
        (point.normalized !== null ||
          point.marketValue !== null),
    );

  if (rawPortfolio.length < 2) {
    return null;
  }

  const firstMarketValue = rawPortfolio.find(
    (point) => point.marketValue !== null,
  )?.marketValue;

  const portfolioByDate = new Map(
    rawPortfolio.map((point) => {
      let value = point.normalized;

      if (
        value === null &&
        point.marketValue !== null &&
        firstMarketValue !== null &&
        firstMarketValue > 0
      ) {
        value =
          (point.marketValue / firstMarketValue) * 100;
      }

      return [point.date, value];
    }),
  );

  const portfolioDates = [...portfolioByDate.keys()]
    .filter(
      (date) =>
        toFiniteNumber(portfolioByDate.get(date)) !== null,
    )
    .sort();

  if (portfolioDates.length < 2) {
    return null;
  }

  // Benchmark:
  // Uses the backend normalized series when available.
  const benchmarkByDate = new Map(
    (Array.isArray(benchmark) ? benchmark : [])
      .map((point) => [
        point?.date ?? "",
        toFiniteNumber(point?.normalized_value),
      ])
      .filter(([date, value]) => date && value !== null),
  );

  const comparisonDates = portfolioDates.filter((date) =>
    benchmarkByDate.has(date),
  );

  const hasBenchmark = comparisonDates.length >= 2;

  // If benchmark is available, both lines use identical dates.
  // Otherwise the portfolio still renders normally.
  const chartDates = hasBenchmark
    ? comparisonDates
    : portfolioDates;

  const portfolioValues = chartDates.map((date) =>
    Number(portfolioByDate.get(date)),
  );

  const benchmarkValues = hasBenchmark
    ? chartDates.map((date) =>
        Number(benchmarkByDate.get(date)),
      )
    : [];

  const allValues = [
    ...portfolioValues,
    ...benchmarkValues,
  ];

  if (allValues.length < 2) {
    return null;
  }

  const minValue = Math.min(...allValues);
  const maxValue = Math.max(...allValues);

  const spread =
    maxValue - minValue ||
    Math.max(Math.abs(maxValue) * 0.02, 1);

  const chartMin = minValue - spread * 0.08;
  const chartMax = maxValue + spread * 0.08;
  const chartHeight =
    height - topPadding - bottomPadding;

  function buildCoordinates(values) {
    return values.map((value, index) => {
      const x =
        values.length === 1
          ? 0
          : (index / (values.length - 1)) * width;

      const normalized =
        (value - chartMin) /
        (chartMax - chartMin);

      const y =
        topPadding +
        chartHeight -
        normalized * chartHeight;

      return {
        x,
        y,
        value,
        date: chartDates[index] ?? "",
      };
    });
  }

  function buildPath(coordinates) {
    return coordinates
      .map(
        (point, index) =>
          `${index === 0 ? "M" : "L"}${point.x.toFixed(
            2,
          )},${point.y.toFixed(2)}`,
      )
      .join(" ");
  }

  const portfolioCoordinates =
    buildCoordinates(portfolioValues);

  const portfolioLinePath =
    buildPath(portfolioCoordinates);

  const first = portfolioCoordinates[0];
  const last =
    portfolioCoordinates[
      portfolioCoordinates.length - 1
    ];

  const portfolioAreaPath =
    `${portfolioLinePath} ` +
    `L${last.x.toFixed(2)},${height} ` +
    `L${first.x.toFixed(2)},${height} Z`;

  const benchmarkLinePath = hasBenchmark
    ? buildPath(
        buildCoordinates(benchmarkValues),
      )
    : null;

  const labelIndexes = [
    0,
    Math.round((chartDates.length - 1) * 0.2),
    Math.round((chartDates.length - 1) * 0.4),
    Math.round((chartDates.length - 1) * 0.6),
    Math.round((chartDates.length - 1) * 0.8),
    chartDates.length - 1,
  ];

  const labels = [...new Set(labelIndexes)].map(
    (index) => {
      const date = chartDates[index] ?? "";

      if (!date) {
        return "--";
      }

      const parsed = new Date(`${date}T00:00:00`);

      if (Number.isNaN(parsed.getTime())) {
        return date;
      }

      return parsed
        .toLocaleDateString("en-US", {
          month: "short",
        })
        .toUpperCase();
    },
  );

  return {
    portfolioLinePath,
    portfolioAreaPath,
    benchmarkLinePath,
    labels,
    hasBenchmark,
  };
}

function Dashboard({
  portfolio = null,
  portfolioHistory = null,
  portfolioHistoryPeriod = "1y",
  portfolioHistoryLoading = false,
  onPortfolioHistoryPeriodChange = () => {},
  market = null,
  ai = null,
}) {
  const summary = portfolio?.summary ?? portfolio ?? {};

  const positions = Array.isArray(portfolio?.positions)
    ? portfolio.positions
    : [];

  const historicalPoints =
    Array.isArray(portfolioHistory?.history)
      ? portfolioHistory.history
      : [];

  const benchmarkPoints =
    Array.isArray(portfolioHistory?.benchmark)
      ? portfolioHistory.benchmark
      : [];

  const historicalSummary =
    portfolioHistory?.summary ?? {};

  const benchmarkSummary =
    portfolioHistory?.benchmark_summary ?? {};

  const comparisonSummary =
    portfolioHistory?.comparison ?? {};

  const historyChart =
    buildHistoryChart(historicalPoints, benchmarkPoints);

  const historicalReturn =
    toFiniteNumber(
      comparisonSummary?.portfolio_return_pct ??
        historicalSummary?.return_pct,
    );

  const benchmarkReturn =
    toFiniteNumber(
      comparisonSummary?.benchmark_return_pct ??
        benchmarkSummary?.return_pct,
    );

  const alphaReturn =
    toFiniteNumber(comparisonSummary?.alpha_pct);

  const historicalAbsoluteReturn =
    toFiniteNumber(
      historicalSummary?.absolute_return
    );

  const historicalObservations =
    toFiniteNumber(
      historicalSummary?.observations
    );

  const historicalPeriodLabel =
    getHistoryPeriodLabel(
      portfolioHistoryPeriod
    );

  const portfolioCurrency =
    resolvePortfolioCurrency(portfolio);

  const portfolioValue =
    summary?.total_value ??
    summary?.portfolio_value ??
    summary?.current_value ??
    null;

  const totalCost =
    summary?.total_cost ??
    summary?.cost_basis ??
    null;

  const totalProfitLoss =
    summary?.total_pl ??
    summary?.unrealized_pl ??
    summary?.profit_loss ??
    null;

  const totalReturnPercentage =
    summary?.total_pl_pct ??
    summary?.total_return_pct ??
    summary?.return_pct ??
    summary?.unrealized_pl_pct ??
    null;

  const {
    dailyProfitLoss,
    dailyReturn,
    coveredPositions,
  } = calculateDailyMetrics(portfolio);

  const largestPositionWeight =
    summary?.largest_position_weight ??
    portfolio?.largest_position_weight ??
    null;

  const concentrationStatus =
    getConcentrationStatus(largestPositionWeight);

  const aiConfidence =
    ai?.confidence ??
    ai?.confidence_score ??
    ai?.score ??
    null;

  const aiStatus =
    ai?.status ??
    ai?.state ??
    "Unavailable";

  const marketIsOpen =
    market?.is_open ??
    market?.market_open ??
    null;

  const marketStatusRaw = String(
    market?.status ?? "",
  ).toLowerCase();

  const marketIsLive =
    marketIsOpen === true ||
    marketStatusRaw === "live" ||
    marketStatusRaw === "open";

  const marketStatusText =
    marketIsOpen === true
      ? "Market Open"
      : marketIsOpen === false
        ? "Market Closed"
        : marketStatusRaw === "live"
          ? "Market Live"
          : "Market Status --";

  const portfolioValueDisplay =
    toFiniteNumber(portfolioValue) !== null
      ? money(portfolioValue, portfolioCurrency)
      : "--";

  const totalCostDisplay =
    toFiniteNumber(totalCost) !== null
      ? money(totalCost, portfolioCurrency)
      : "--";

  const totalProfitLossDisplay =
    toFiniteNumber(totalProfitLoss) !== null
      ? money(totalProfitLoss, portfolioCurrency)
      : "--";

  const totalReturnPercentageDisplay =
    toFiniteNumber(totalReturnPercentage) !== null
      ? percentage(totalReturnPercentage)
      : "--";

  const dailyProfitLossDisplay =
    toFiniteNumber(dailyProfitLoss) !== null
      ? money(dailyProfitLoss, portfolioCurrency)
      : "--";

  const dailyPercentageDisplay =
    toFiniteNumber(dailyReturn) !== null
      ? percentage(dailyReturn)
      : "--";

  const dailyStatus =
    getStatusFromValue(dailyProfitLoss);

  const totalReturnStatus =
    getStatusFromValue(totalProfitLoss);

  const watchlist =
    normalizeWatchlist(market);

  const allocation =
    normalizeAllocation(portfolio);

  const insights =
    normalizeInsights(ai);

  const news =
    normalizeNews(market);

  const sectorCount =
    Array.isArray(portfolio?.sector_allocation)
      ? portfolio.sector_allocation.length
      : 0;

  const priceCoverage =
    positions.length > 0
      ? (positions.filter(
          (position) =>
            toFiniteNumber(position?.current_price) !== null,
        ).length /
          positions.length) *
        100
      : null;

  return (
    <main className="dashboard">
      <section className="dashboard__header">
        <div className="dashboard__heading">
          <span className="dashboard__eyebrow">
            QUANTUM MARKET INTELLIGENCE
          </span>

          <h1 className="dashboard__title">
            Dashboard Overview
          </h1>

          <p className="dashboard__description">
            Institutional market intelligence, portfolio
            monitoring and AI-assisted decision support from a
            unified control center.
          </p>
        </div>

        <div
          className={`dashboard__status ${
            marketIsLive
              ? "dashboard__status--open"
              : "dashboard__status--closed"
          }`}
          aria-label={marketStatusText}
        >
          <span
            className="dashboard__status-dot"
            aria-hidden="true"
          />

          {marketStatusText}
        </div>
      </section>

      <section
        className="dashboard__metrics"
        aria-label="Portfolio and market metrics"
      >
        <MetricCard
          label="Portfolio Value"
          value={portfolioValueDisplay}
          change={totalReturnPercentageDisplay}
          changeLabel="Total return"
          status={totalReturnStatus}
          icon="◈"
        />

        <MetricCard
          label="Daily P&L"
          value={dailyProfitLossDisplay}
          change={dailyPercentageDisplay}
          changeLabel={
            coveredPositions > 0
              ? "vs. previous close"
              : "market close data unavailable"
          }
          status={dailyStatus}
          icon={dailyStatus === "negative" ? "↘" : "↗"}
        />

        <MetricCard
          label="Total Return"
          value={totalReturnPercentageDisplay}
          change={totalProfitLossDisplay}
          changeLabel={`Cost basis ${totalCostDisplay}`}
          status={totalReturnStatus}
          icon="◇"
        />

        <MetricCard
          label="AI Confidence"
          value={
            toFiniteNumber(aiConfidence) !== null
              ? compactPercentage(aiConfidence)
              : "--"
          }
          change={aiStatus}
          changeLabel="Decision engine"
          status={
            toFiniteNumber(aiConfidence) === null
              ? "neutral"
              : Number(aiConfidence) >= 50
                ? "positive"
                : "warning"
          }
          icon="✦"
        />
      </section>

      <section className="dashboard__primary-grid">
        <article className="dashboard-panel dashboard-panel--portfolio">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                PORTFOLIO INTELLIGENCE
              </span>

              <h2 className="dashboard-panel__title">
                Portfolio performance
              </h2>
            </div>

            <span
              className={`dashboard-panel__badge ${
                totalReturnStatus === "negative"
                  ? "dashboard-panel__badge--negative"
                  : ""
              }`}
            >
              {historicalReturn !== null
                ? `${historicalPeriodLabel} ${percentage(historicalReturn)}`
                : `RETURN ${totalReturnPercentageDisplay}`}
            </span>
          </header>

          <div className="portfolio-summary">
            <div>
              <span className="portfolio-summary__label">
                Current value
              </span>

              <strong className="portfolio-summary__value">
                {portfolioValueDisplay}
              </strong>
            </div>

            <div
              className={`portfolio-summary__change portfolio-summary__change--${totalReturnStatus}`}
            >
              <span>Unrealized return</span>
              <strong>{totalProfitLossDisplay}</strong>

              {historicalAbsoluteReturn !== null && (
                <small
                  style={{
                    display: "block",
                    marginTop: "0.25rem",
                    color:
                      "var(--text-muted, #64748b)",
                    fontSize: "0.65rem",
                  }}
                >
                  {historicalPeriodLabel} history{" "}
                  {money(
                    historicalAbsoluteReturn,
                    portfolioHistory?.currency ||
                      portfolioCurrency
                  )}
                </small>
              )}
            </div>
          </div>

          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.4rem",
              margin: "0.8rem 0 0.35rem",
              alignItems: "center",
            }}
            aria-label="Portfolio history period selector"
          >
            {PORTFOLIO_HISTORY_PERIODS.map(
              (period) => {
                const selected =
                  period.value ===
                  portfolioHistoryPeriod;

                return (
                  <button
                    key={period.value}
                    type="button"
                    onClick={() =>
                      onPortfolioHistoryPeriodChange(
                        period.value
                      )
                    }
                    disabled={
                      portfolioHistoryLoading
                    }
                    aria-pressed={selected}
                    style={{
                      minWidth: "2.8rem",
                      height: "1.9rem",
                      padding: "0 0.65rem",
                      borderRadius: "0.45rem",
                      border: selected
                        ? "1px solid rgba(56, 189, 248, 0.55)"
                        : "1px solid rgba(148, 163, 184, 0.14)",
                      background: selected
                        ? "rgba(14, 165, 233, 0.14)"
                        : "rgba(15, 23, 42, 0.28)",
                      color: selected
                        ? "var(--text-primary, #e2e8f0)"
                        : "var(--text-muted, #64748b)",
                      fontSize: "0.67rem",
                      fontWeight: 700,
                      letterSpacing: "0.04em",
                      cursor:
                        portfolioHistoryLoading
                          ? "wait"
                          : "pointer",
                      opacity:
                        portfolioHistoryLoading &&
                        !selected
                          ? 0.55
                          : 1,
                    }}
                  >
                    {period.label}
                  </button>
                );
              }
            )}

            {portfolioHistoryLoading && (
              <span
                style={{
                  marginLeft: "0.25rem",
                  color:
                    "var(--text-muted, #64748b)",
                  fontSize: "0.67rem",
                }}
              >
                Loading {historicalPeriodLabel}…
              </span>
            )}
          </div>

          <div
            className="portfolio-chart"
            role="img"
            aria-label={
              historyChart
                ? "Portfolio performance compared with S&P 500"
                : "Portfolio historical performance unavailable"
            }
          >
            <div className="portfolio-chart__grid" />

            {historyChart ? (
              <>
                <svg
                  className="portfolio-chart__line"
                  viewBox="0 0 700 220"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <defs>
                    <linearGradient
                      id="portfolioHistoricalArea"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="currentColor"
                        stopOpacity="0.28"
                      />
                      <stop
                        offset="100%"
                        stopColor="currentColor"
                        stopOpacity="0"
                      />
                    </linearGradient>
                  </defs>

                  <path
                    className="portfolio-chart__area"
                    d={historyChart.portfolioAreaPath}
                    fill="url(#portfolioHistoricalArea)"
                  />

                  <path
                    className="portfolio-chart__stroke"
                    d={historyChart.portfolioLinePath}
                  />

                  {historyChart.benchmarkLinePath && (
                    <path
                      d={historyChart.benchmarkLinePath}
                      fill="none"
                      stroke="#f59e0b"
                      strokeWidth="2"
                      strokeDasharray="7 5"
                      vectorEffect="non-scaling-stroke"
                    />
                  )}
                </svg>

                <div className="portfolio-chart__axis">
                  {historyChart.labels.map(
                    (label, index) => (
                      <span key={`${label}-${index}`}>
                        {label}
                      </span>
                    )
                  )}
                </div>

                <div
                  style={{
                    position: "absolute",
                    top: "0.65rem",
                    right: "0.9rem",
                    display: "flex",
                    flexWrap: "wrap",
                    justifyContent: "flex-end",
                    gap: "0.65rem",
                    alignItems: "center",
                    fontSize: "0.68rem",
                    color: "var(--text-muted, #64748b)",
                  }}
                >
                  <span>
                    {historicalPeriodLabel} ·{" "}
                    {historicalObservations ?? historicalPoints.length} sessions
                  </span>

                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.32rem",
                    }}
                  >
                    <span
                      aria-hidden="true"
                      style={{
                        width: "0.9rem",
                        height: "2px",
                        borderRadius: "999px",
                        background: "currentColor",
                        display: "inline-block",
                      }}
                    />
                    Portfolio{" "}
                    <strong
                      style={{
                        color:
                          getStatusFromValue(historicalReturn) === "negative"
                            ? "var(--negative, #fb7185)"
                            : "var(--positive, #34d399)",
                      }}
                    >
                      {historicalReturn !== null
                        ? percentage(historicalReturn)
                        : "--"}
                    </strong>
                  </span>

                  {historyChart.hasBenchmark && (
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.32rem",
                        color: "#f59e0b",
                      }}
                    >
                      <span
                        aria-hidden="true"
                        style={{
                          width: "0.9rem",
                          borderTop: "2px dashed #f59e0b",
                          display: "inline-block",
                        }}
                      />
                      S&P 500{" "}
                      <strong>
                        {benchmarkReturn !== null
                          ? percentage(benchmarkReturn)
                          : "--"}
                      </strong>
                    </span>
                  )}

                  {alphaReturn !== null && historyChart.hasBenchmark && (
                    <span
                      style={{
                        padding: "0.18rem 0.42rem",
                        borderRadius: "0.35rem",
                        border:
                          getStatusFromValue(alphaReturn) === "negative"
                            ? "1px solid rgba(251, 113, 133, 0.28)"
                            : "1px solid rgba(52, 211, 153, 0.28)",
                        background:
                          getStatusFromValue(alphaReturn) === "negative"
                            ? "rgba(251, 113, 133, 0.08)"
                            : "rgba(52, 211, 153, 0.08)",
                      }}
                    >
                      Alpha{" "}
                      <strong
                        style={{
                          color:
                            getStatusFromValue(alphaReturn) === "negative"
                              ? "var(--negative, #fb7185)"
                              : "var(--positive, #34d399)",
                        }}
                      >
                        {percentage(alphaReturn)} pp
                      </strong>
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div
                style={{
                  position: "absolute",
                  inset: "0 0 1.75rem",
                  display: "grid",
                  placeItems: "center",
                  padding: "1.5rem",
                  textAlign: "center",
                }}
              >
                <div>
                  <div
                    style={{
                      color:
                        "var(--text-secondary, #cbd5e1)",
                      fontSize: "0.86rem",
                      fontWeight: 600,
                      marginBottom: "0.45rem",
                    }}
                  >
                    Historical performance unavailable
                  </div>

                  <div
                    style={{
                      color:
                        "var(--text-muted, #64748b)",
                      fontSize: "0.72rem",
                      lineHeight: 1.55,
                      maxWidth: "29rem",
                    }}
                  >
                    QMI could not retrieve enough historical
                    market observations for the current
                    portfolio.
                  </div>
                </div>
              </div>
            )}
          </div>
        </article>

        <article className="dashboard-panel dashboard-panel--allocation">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                ASSET ALLOCATION
              </span>

              <h2 className="dashboard-panel__title">
                Exposure profile
              </h2>
            </div>
          </header>

          <div className="allocation-score">
            <div
              className={`allocation-score__ring allocation-score__ring--${concentrationStatus}`}
              style={{
                "--risk-score": `${
                  Math.min(
                    Math.max(
                      toFiniteNumber(
                        largestPositionWeight,
                      ) ?? 0,
                      0,
                    ),
                    100,
                  )
                }%`,
              }}
            >
              <span>
                {toFiniteNumber(
                  largestPositionWeight,
                ) !== null
                  ? Math.round(
                      Number(largestPositionWeight),
                    )
                  : "--"}
              </span>

              <small>MAX WT</small>
            </div>

            <div>
              <strong>
                {getConcentrationLabel(
                  largestPositionWeight,
                )}
              </strong>

              <p>
                Largest-position weight derived from the current
                marked-to-market portfolio snapshot.
              </p>
            </div>
          </div>

          <div className="allocation-list">
            {allocation.length > 0 ? (
              allocation.map((item) => {
                const normalizedValue = Math.min(
                  Math.max(
                    toFiniteNumber(item.value) ?? 0,
                    0,
                  ),
                  100,
                );

                return (
                  <div
                    className="allocation-item"
                    key={item.label}
                  >
                    <div className="allocation-item__header">
                      <span>{item.label}</span>

                      <strong>
                        {normalizedValue.toLocaleString(
                          "es-ES",
                          {
                            minimumFractionDigits: 0,
                            maximumFractionDigits: 1,
                          },
                        )}
                        %
                      </strong>
                    </div>

                    <div className="allocation-item__track">
                      <span
                        style={{
                          width: `${normalizedValue}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              <div
                style={{
                  color:
                    "var(--text-muted, #64748b)",
                  fontSize: "0.76rem",
                  lineHeight: 1.5,
                }}
              >
                No portfolio allocation data available.
              </div>
            )}
          </div>
        </article>
      </section>

      <section className="dashboard__secondary-grid">
        <article className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                LIVE MARKET
              </span>

              <h2 className="dashboard-panel__title">
                Watchlist
              </h2>
            </div>
          </header>

          <div className="watchlist">
            <div className="watchlist__head">
              <span>Asset</span>
              <span>Price</span>
              <span>Change</span>
            </div>

            {watchlist.length > 0 ? (
              watchlist.map((asset) => (
                <div
                  className="watchlist__row"
                  key={asset.ticker}
                >
                  <div className="watchlist__asset">
                    <strong>{asset.ticker}</strong>
                    <span>{asset.company}</span>
                  </div>

                  <span className="watchlist__price">
                    {asset.price}
                  </span>

                  <span
                    className={`watchlist__change watchlist__change--${asset.status}`}
                  >
                    {asset.change}
                  </span>
                </div>
              ))
            ) : (
              <div
                style={{
                  padding: "1rem 0",
                  color:
                    "var(--text-muted, #64748b)",
                  fontSize: "0.76rem",
                }}
              >
                Live market data unavailable.
              </div>
            )}
          </div>
        </article>

        <article className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                QMI INTELLIGENCE
              </span>

              <h2 className="dashboard-panel__title">
                AI insights
              </h2>
            </div>

            <span className="dashboard-panel__badge">
              {insights.length} ACTIVE
            </span>
          </header>

          <div className="insight-list">
            {insights.length > 0 ? (
              insights.map((insight, index) => (
                <div
                  className="insight-item"
                  key={`${insight.title}-${index}`}
                >
                  <span
                    className={`insight-item__indicator insight-item__indicator--${insight.status}`}
                  />

                  <div>
                    <span className="insight-item__type">
                      {insight.type}
                    </span>

                    <strong>{insight.title}</strong>
                    <p>{insight.description}</p>
                  </div>
                </div>
              ))
            ) : (
              <div className="insight-item">
                <span className="insight-item__indicator insight-item__indicator--neutral" />

                <div>
                  <span className="insight-item__type">
                    STATUS
                  </span>

                  <strong>
                    No live AI insights available
                  </strong>

                  <p>
                    QMI will display decision-engine insights here
                    when the AI endpoint provides live signals.
                  </p>
                </div>
              </div>
            )}
          </div>
        </article>
      </section>

      <section className="dashboard__tertiary-grid">
        <article className="dashboard-panel">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                INFORMATION FLOW
              </span>

              <h2 className="dashboard-panel__title">
                Market intelligence
              </h2>
            </div>
          </header>

          <div className="news-list">
            {news.length > 0 ? (
              news.map((item, index) => (
                <article
                  className="news-item"
                  key={`${item.time}-${item.title}-${index}`}
                >
                  <div className="news-item__meta">
                    <span>{item.source}</span>
                    <time>{item.time}</time>
                  </div>

                  <h3>{item.title}</h3>
                </article>
              ))
            ) : (
              <article className="news-item">
                <div className="news-item__meta">
                  <span>STATUS</span>
                  <time>--</time>
                </div>

                <h3>
                  Live news feed is not connected to the
                  Dashboard yet.
                </h3>
              </article>
            )}
          </div>
        </article>

        <article className="dashboard-panel dashboard-panel--risk">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                PORTFOLIO CONTROLS
              </span>

              <h2 className="dashboard-panel__title">
                Live portfolio diagnostics
              </h2>
            </div>
          </header>

          <div className="risk-grid">
            <div className="risk-metric">
              <span>Largest position</span>

              <strong>
                {compactPercentage(
                  largestPositionWeight,
                )}
              </strong>

              <small>
                Current concentration
              </small>
            </div>

            <div className="risk-metric">
              <span>Open positions</span>

              <strong>{positions.length}</strong>

              <small>
                Persisted portfolio records
              </small>
            </div>

            <div className="risk-metric">
              <span>Sector groups</span>

              <strong>{sectorCount}</strong>

              <small>
                Current sector allocation
              </small>
            </div>

            <div className="risk-metric">
              <span>Price coverage</span>

              <strong>
                {compactPercentage(priceCoverage)}
              </strong>

              <small>
                Positions with live valuation
              </small>
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}

export default Dashboard;

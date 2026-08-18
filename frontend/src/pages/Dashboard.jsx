import MetricCard from "../components/ui/MetricCard";
import "./Dashboard.css";

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


function buildHistoryChart(history) {
  if (!Array.isArray(history) || history.length < 2) {
    return null;
  }

  const width = 700;
  const height = 220;
  const topPadding = 18;
  const bottomPadding = 26;

  const values = history
    .map((point) => toFiniteNumber(point?.market_value))
    .filter((value) => value !== null);

  if (values.length < 2) {
    return null;
  }

  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);

  const spread =
    maxValue - minValue || Math.max(Math.abs(maxValue) * 0.02, 1);

  const chartMin = minValue - spread * 0.08;
  const chartMax = maxValue + spread * 0.08;
  const chartHeight = height - topPadding - bottomPadding;

  const coordinates = history.map((point, index) => {
    const value =
      toFiniteNumber(point?.market_value) ?? chartMin;

    const x =
      history.length === 1
        ? 0
        : (index / (history.length - 1)) * width;

    const normalized =
      (value - chartMin) / (chartMax - chartMin);

    const y =
      topPadding +
      chartHeight -
      normalized * chartHeight;

    return {
      x,
      y,
      value,
      date: point?.date ?? "",
    };
  });

  const linePath = coordinates
    .map(
      (point, index) =>
        `${index === 0 ? "M" : "L"}${point.x.toFixed(2)},${point.y.toFixed(2)}`
    )
    .join(" ");

  const first = coordinates[0];
  const last = coordinates[coordinates.length - 1];

  const areaPath =
    `${linePath} ` +
    `L${last.x.toFixed(2)},${height} ` +
    `L${first.x.toFixed(2)},${height} Z`;

  const labelIndexes = [
    0,
    Math.round((history.length - 1) * 0.2),
    Math.round((history.length - 1) * 0.4),
    Math.round((history.length - 1) * 0.6),
    Math.round((history.length - 1) * 0.8),
    history.length - 1,
  ];

  const labels = [
    ...new Set(labelIndexes),
  ].map((index) => {
    const date = history[index]?.date ?? "";

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
  });

  return {
    linePath,
    areaPath,
    labels,
    startValue: values[0],
    endValue: values[values.length - 1],
  };
}

function Dashboard({
  portfolio = null,
  portfolioHistory = null,
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

  const historicalSummary =
    portfolioHistory?.summary ?? {};

  const historyChart =
    buildHistoryChart(historicalPoints);

  const historicalReturn =
    toFiniteNumber(historicalSummary?.return_pct);

  const historicalAbsoluteReturn =
    toFiniteNumber(
      historicalSummary?.absolute_return
    );

  const historicalObservations =
    toFiniteNumber(
      historicalSummary?.observations
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
                ? `1Y ${percentage(historicalReturn)}`
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
                  1Y history{" "}
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
            className="portfolio-chart"
            role="img"
            aria-label={
              historyChart
                ? "Historical portfolio market value"
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
                    d={historyChart.areaPath}
                    fill="url(#portfolioHistoricalArea)"
                  />

                  <path
                    className="portfolio-chart__stroke"
                    d={historyChart.linePath}
                  />
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
                    top: "0.75rem",
                    right: "0.9rem",
                    display: "flex",
                    gap: "0.55rem",
                    alignItems: "center",
                    fontSize: "0.68rem",
                    color:
                      "var(--text-muted, #64748b)",
                  }}
                >
                  <span>
                    {historicalObservations ?? historicalPoints.length} sessions
                  </span>

                  <span>·</span>

                  <strong
                    style={{
                      color:
                        getStatusFromValue(
                          historicalReturn
                        ) === "negative"
                          ? "var(--negative, #fb7185)"
                          : "var(--positive, #34d399)",
                    }}
                  >
                    {historicalReturn !== null
                      ? percentage(
                          historicalReturn
                        )
                      : "--"}
                  </strong>
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

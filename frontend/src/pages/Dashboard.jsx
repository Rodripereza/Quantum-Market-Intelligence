import MetricCard from "../components/ui/MetricCard";
import "./Dashboard.css";

const fallbackWatchlist = [
  {
    ticker: "NIO",
    company: "NIO Inc.",
    price: "$5.18",
    change: "+3.42%",
    status: "positive",
  },
  {
    ticker: "NVDA",
    company: "NVIDIA",
    price: "$172.36",
    change: "+1.18%",
    status: "positive",
  },
  {
    ticker: "PLTR",
    company: "Palantir",
    price: "$146.24",
    change: "-0.64%",
    status: "negative",
  },
  {
    ticker: "RKLB",
    company: "Rocket Lab",
    price: "$48.92",
    change: "+2.07%",
    status: "positive",
  },
];

const fallbackAllocation = [
  { label: "Technology", value: 42 },
  { label: "EV & Mobility", value: 28 },
  { label: "Aerospace", value: 18 },
  { label: "Cash", value: 12 },
];

const fallbackInsights = [
  {
    type: "Opportunity",
    title: "Momentum strengthening",
    description:
      "Three monitored assets are trading above their medium-term moving averages.",
    status: "positive",
  },
  {
    type: "Risk",
    title: "Portfolio concentration",
    description:
      "The largest position currently represents more than 35% of total exposure.",
    status: "warning",
  },
  {
    type: "Signal",
    title: "Volatility expansion",
    description:
      "Market volatility is increasing and may affect short-term position sizing.",
    status: "neutral",
  },
];

const fallbackNews = [
  {
    source: "MARKET",
    time: "14:32",
    title: "US equities advance as technology stocks lead gains",
  },
  {
    source: "PORTFOLIO",
    time: "13:48",
    title: "EV sector volatility remains elevated during the current session",
  },
  {
    source: "MACRO",
    time: "12:15",
    title: "Investors reassess rate expectations ahead of upcoming data",
  },
];

function toFiniteNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const number = Number(value);

  return Number.isFinite(number) ? number : null;
}

function money(value, currency = "EUR") {
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

function getRiskStatus(score) {
  const number = toFiniteNumber(score);

  if (number === null) {
    return "neutral";
  }

  if (number >= 75) {
    return "negative";
  }

  if (number >= 50) {
    return "warning";
  }

  return "positive";
}

function getRiskLabel(score) {
  const number = toFiniteNumber(score);

  if (number === null) {
    return "Unavailable";
  }

  if (number >= 75) {
    return "High";
  }

  if (number >= 50) {
    return "Moderate";
  }

  return "Controlled";
}

function normalizeWatchlist(market) {
  const assets =
    market?.assets ??
    market?.watchlist ??
    market?.items ??
    [];

  if (!Array.isArray(assets) || assets.length === 0) {
    return fallbackWatchlist;
  }

  return assets.slice(0, 4).map((asset, index) => {
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

  if (!Array.isArray(allocation) || allocation.length === 0) {
    return fallbackAllocation;
  }

  return allocation.slice(0, 5).map((item, index) => ({
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

  if (!Array.isArray(insights) || insights.length === 0) {
    return fallbackInsights;
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
    status: ["positive", "negative", "warning", "neutral"].includes(
      insight?.status,
    )
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

  if (!Array.isArray(news) || news.length === 0) {
    return fallbackNews;
  }

  return news.slice(0, 3).map((item, index) => ({
    source:
      item?.source ??
      item?.category ??
      item?.publisher ??
      "MARKET",
    time:
      item?.time ??
      item?.published_time ??
      item?.publishedAt ??
      `0${index + 1}:00`,
    title:
      item?.title ??
      item?.headline ??
      item?.summary ??
      "Market update unavailable",
  }));
}

function Dashboard({
  portfolio = null,
  market = null,
  ai = null,
}) {
  const summary = portfolio?.summary ?? portfolio ?? {};

  const portfolioValue =
    summary?.total_value ??
    summary?.portfolio_value ??
    summary?.current_value ??
    portfolio?.total_value ??
    null;

  const dailyProfitLoss =
    summary?.daily_pl ??
    summary?.daily_pnl ??
    summary?.day_profit_loss ??
    portfolio?.daily_pl ??
    null;

  const dailyProfitLossPercentage =
    summary?.daily_pl_pct ??
    summary?.daily_pnl_pct ??
    summary?.day_return ??
    portfolio?.daily_pl_pct ??
    null;

  const totalReturn =
    summary?.total_return ??
    summary?.total_return_value ??
    summary?.unrealized_pl ??
    summary?.profit_loss ??
    null;

  const totalReturnPercentage =
    summary?.total_return_pct ??
    summary?.return_pct ??
    summary?.unrealized_pl_pct ??
    null;

  const riskScore =
    portfolio?.risk_score ??
    summary?.risk_score ??
    64;

  const aiConfidence =
    ai?.confidence ??
    ai?.confidence_score ??
    ai?.score ??
    82.4;

  const marketIsOpen =
    market?.is_open ??
    market?.market_open ??
    market?.status === "open" ??
    true;

  const volatility =
    portfolio?.risk?.volatility ??
    summary?.volatility ??
    24.8;

  const maxDrawdown =
    portfolio?.risk?.max_drawdown ??
    summary?.max_drawdown ??
    -18.2;

  const beta =
    portfolio?.risk?.beta ??
    summary?.beta ??
    1.34;

  const cashPercentage =
    summary?.cash_weight ??
    summary?.cash_percentage ??
    portfolio?.cash_weight ??
    12;

  const portfolioValueDisplay =
    toFiniteNumber(portfolioValue) !== null
      ? money(portfolioValue)
      : "128.450,72 €";

  const dailyProfitLossDisplay =
    toFiniteNumber(dailyProfitLoss) !== null
      ? money(dailyProfitLoss)
      : "+3.542,18 €";

  const dailyPercentageDisplay =
    toFiniteNumber(dailyProfitLossPercentage) !== null
      ? percentage(dailyProfitLossPercentage)
      : "+1,92%";

  const totalReturnDisplay =
    toFiniteNumber(totalReturn) !== null
      ? money(totalReturn)
      : "+14.382,20 €";

  const totalReturnPercentageDisplay =
    toFiniteNumber(totalReturnPercentage) !== null
      ? percentage(totalReturnPercentage)
      : "+12,48%";

  const dailyStatus = getStatusFromValue(dailyProfitLoss);
  const riskStatus = getRiskStatus(riskScore);

  const watchlist = normalizeWatchlist(market);
  const allocation = normalizeAllocation(portfolio);
  const insights = normalizeInsights(ai);
  const news = normalizeNews(market);

  return (
    <main className="dashboard">
      <section className="dashboard__header">
        <div className="dashboard__heading">
          <span className="dashboard__eyebrow">
            QUANTUM MARKET INTELLIGENCE
          </span>

          <h1 className="dashboard__title">Dashboard Overview</h1>

          <p className="dashboard__description">
            Institutional market intelligence, portfolio monitoring and
            AI-assisted decision support from a unified control center.
          </p>
        </div>

        <div
          className={`dashboard__status ${
            marketIsOpen
              ? "dashboard__status--open"
              : "dashboard__status--closed"
          }`}
          aria-label={
            marketIsOpen
              ? "Market status: open"
              : "Market status: closed"
          }
        >
          <span
            className="dashboard__status-dot"
            aria-hidden="true"
          />

          {marketIsOpen ? "Market Open" : "Market Closed"}
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
          status={getStatusFromValue(totalReturnPercentage)}
          icon="◈"
        />

        <MetricCard
          label="Daily P&L"
          value={dailyProfitLossDisplay}
          change={dailyPercentageDisplay}
          changeLabel="vs. previous close"
          status={dailyStatus}
          icon={dailyStatus === "negative" ? "↘" : "↗"}
        />

        <MetricCard
          label="Risk Score"
          value={
            toFiniteNumber(riskScore) !== null
              ? `${Math.round(Number(riskScore))} / 100`
              : "--"
          }
          change={getRiskLabel(riskScore)}
          changeLabel="Portfolio exposure"
          status={riskStatus}
          icon="◇"
        />

        <MetricCard
          label="AI Confidence"
          value={
            toFiniteNumber(aiConfidence) !== null
              ? compactPercentage(aiConfidence)
              : "--"
          }
          change={ai?.status ?? "Operational"}
          changeLabel="Decision engine"
          status={
            toFiniteNumber(aiConfidence) !== null &&
            Number(aiConfidence) < 50
              ? "warning"
              : "positive"
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
                getStatusFromValue(totalReturnPercentage) === "negative"
                  ? "dashboard-panel__badge--negative"
                  : ""
              }`}
            >
              YTD {totalReturnPercentageDisplay}
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
              className={`portfolio-summary__change portfolio-summary__change--${getStatusFromValue(
                totalReturn,
              )}`}
            >
              <span>Unrealized return</span>
              <strong>{totalReturnDisplay}</strong>
            </div>
          </div>

          <div
            className="portfolio-chart"
            role="img"
            aria-label="Portfolio performance chart"
          >
            <div className="portfolio-chart__grid" />

            <svg
              className="portfolio-chart__line"
              viewBox="0 0 700 220"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <defs>
                <linearGradient
                  id="portfolioArea"
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
                d="M0,184 C55,175 72,150 124,158 C180,166 210,119 260,126 C320,134 346,84 401,98 C453,111 488,63 535,76 C584,90 622,38 700,28 L700,220 L0,220 Z"
              />

              <path
                className="portfolio-chart__stroke"
                d="M0,184 C55,175 72,150 124,158 C180,166 210,119 260,126 C320,134 346,84 401,98 C453,111 488,63 535,76 C584,90 622,38 700,28"
              />
            </svg>

            <div className="portfolio-chart__axis">
              <span>JAN</span>
              <span>MAR</span>
              <span>MAY</span>
              <span>JUL</span>
              <span>SEP</span>
              <span>NOV</span>
            </div>
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
              className={`allocation-score__ring allocation-score__ring--${riskStatus}`}
              style={{
                "--risk-score": `${Math.min(
                  Math.max(toFiniteNumber(riskScore) ?? 0, 0),
                  100,
                )}%`,
              }}
            >
              <span>
                {toFiniteNumber(riskScore) !== null
                  ? Math.round(Number(riskScore))
                  : "--"}
              </span>

              <small>RISK</small>
            </div>

            <div>
              <strong>{getRiskLabel(riskScore)} exposure</strong>

              <p>
                The portfolio risk profile is calculated from current
                concentration, diversification and market exposure.
              </p>
            </div>
          </div>

          <div className="allocation-list">
            {allocation.map((item) => {
              const normalizedValue = Math.min(
                Math.max(toFiniteNumber(item.value) ?? 0, 0),
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
                      {normalizedValue.toLocaleString("es-ES", {
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 1,
                      })}
                      %
                    </strong>
                  </div>

                  <div className="allocation-item__track">
                    <span style={{ width: `${normalizedValue}%` }} />
                  </div>
                </div>
              );
            })}
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

            <button
              className="dashboard-panel__action"
              type="button"
            >
              View market
            </button>
          </header>

          <div className="watchlist">
            <div className="watchlist__head">
              <span>Asset</span>
              <span>Price</span>
              <span>Change</span>
            </div>

            {watchlist.map((asset) => (
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
            ))}
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
            {insights.map((insight, index) => (
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
            ))}
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

            <button
              className="dashboard-panel__action"
              type="button"
            >
              All news
            </button>
          </header>

          <div className="news-list">
            {news.map((item, index) => (
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
            ))}
          </div>
        </article>

        <article className="dashboard-panel dashboard-panel--risk">
          <header className="dashboard-panel__header">
            <div>
              <span className="dashboard-panel__eyebrow">
                RISK ANALYTICS
              </span>

              <h2 className="dashboard-panel__title">
                Portfolio controls
              </h2>
            </div>
          </header>

          <div className="risk-grid">
            <div className="risk-metric">
              <span>Volatility</span>
              <strong>{compactPercentage(volatility)}</strong>
              <small>30-day annualized</small>
            </div>

            <div className="risk-metric">
              <span>Max drawdown</span>
              <strong>{compactPercentage(maxDrawdown)}</strong>
              <small>Current portfolio</small>
            </div>

            <div className="risk-metric">
              <span>Beta</span>
              <strong>
                {toFiniteNumber(beta) !== null
                  ? Number(beta).toLocaleString("es-ES", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })
                  : "--"}
              </strong>
              <small>vs. S&amp;P 500</small>
            </div>

            <div className="risk-metric">
              <span>Cash reserve</span>
              <strong>{compactPercentage(cashPercentage)}</strong>
              <small>Available liquidity</small>
            </div>
          </div>
        </article>
      </section>
    </main>
  );
}

export default Dashboard;
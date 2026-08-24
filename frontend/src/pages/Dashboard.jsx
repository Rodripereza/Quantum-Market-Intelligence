import { useEffect, useState } from "react";
import "./Dashboard.css";



function QmiIcon({ name, size = 16 }) {
  const common = {
    width: size, height: size, viewBox: "0 0 24 24", fill: "none",
    stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round",
    strokeLinejoin: "round", "aria-hidden": "true",
  };

  const icons = {
    command: <><path d="M4 17V7"/><path d="M8 17V11"/><path d="M12 17V4"/><path d="M16 17V9"/><path d="M20 17V6"/></>,
    performance: <><path d="M3 17l5-5 4 3 7-8"/><path d="M15 7h4v4"/></>,
    risk: <><path d="M12 3l8 4v5c0 5-3.4 8-8 9-4.6-1-8-4-8-9V7l8-4z"/><path d="M12 8v5"/><path d="M12 17h.01"/></>,
    decision: <><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/><path d="M4.9 4.9L7 7M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></>,
    news: <><path d="M5 4h12a2 2 0 012 2v14H7a2 2 0 01-2-2V4z"/><path d="M8 8h8M8 12h8M8 16h5"/></>,
    market: <><path d="M4 18V9M10 18V5M16 18v-7M22 18H2"/></>,
  };

  return <svg {...common}>{icons[name] ?? icons.command}</svg>;
}

function SectionIdentity({ icon, kicker, title }) {
  return (
    <div className="gf-section-identity">
      <span className="gf-section-icon"><QmiIcon name={icon} size={16} /></span>
      <div>
        <span className="gf-kicker">{kicker}</span>
        <h2>{title}</h2>
      </div>
    </div>
  );
}

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

function cleanNewsTitle(title, source) {
  const rawTitle = String(title || "").trim();
  const rawSource = String(source || "").trim();

  if (!rawTitle || !rawSource) {
    return rawTitle;
  }

  const suffix = ` - ${rawSource}`;

  return rawTitle.toLowerCase().endsWith(suffix.toLowerCase())
    ? rawTitle.slice(0, -suffix.length).trim()
    : rawTitle;
}

function getNewsImpactRank(impact) {
  const normalized = String(impact || "").toLowerCase();

  if (normalized === "high") {
    return 3;
  }

  if (normalized === "medium") {
    return 2;
  }

  if (normalized === "low") {
    return 1;
  }

  return 0;
}

function formatNewsTime(value) {
  if (!value || value === "--") {
    return "--";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  const elapsedMs = Date.now() - date.getTime();
  const elapsedMinutes = Math.floor(elapsedMs / 60000);

  if (elapsedMinutes >= 0 && elapsedMinutes < 1) {
    return "now";
  }

  if (elapsedMinutes >= 1 && elapsedMinutes < 60) {
    return `${elapsedMinutes}m ago`;
  }

  const elapsedHours = Math.floor(elapsedMinutes / 60);

  if (elapsedHours >= 1 && elapsedHours < 24) {
    return `${elapsedHours}h ago`;
  }

  const elapsedDays = Math.floor(elapsedHours / 24);

  if (elapsedDays >= 1 && elapsedDays < 7) {
    return `${elapsedDays}d ago`;
  }

  return date.toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function normalizeNews(newsPayload) {
  const news =
    newsPayload?.articles ??
    newsPayload?.news ??
    newsPayload?.headlines ??
    [];

  if (!Array.isArray(news)) {
    return [];
  }

  const normalized = news
    .map((item) => {
      const source =
        item?.source ??
        item?.publisher ??
        item?.category ??
        "MARKET";

      const publishedAt =
        item?.published_at ??
        item?.published_time ??
        item?.publishedAt ??
        item?.time ??
        "--";

      const title =
        item?.title ??
        item?.headline ??
        item?.summary ??
        "Market update unavailable";

      return {
        source,
        time: publishedAt,
        title: cleanNewsTitle(title, source),
        url: item?.url ?? null,
        sentiment: String(item?.sentiment ?? "neutral").toLowerCase(),
        impact: String(item?.impact ?? "medium").toLowerCase(),
        category: item?.category ?? "markets",
      };
    })
    .filter((item) => item.title);

  const deduplicated = [];
  const seen = new Set();

  normalized.forEach((item) => {
    const key = item.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, " ")
      .trim();

    if (!key || seen.has(key)) {
      return;
    }

    seen.add(key);
    deduplicated.push(item);
  });

  return deduplicated
    .sort((a, b) => {
      const impactDifference =
        getNewsImpactRank(b.impact) -
        getNewsImpactRank(a.impact);

      if (impactDifference !== 0) {
        return impactDifference;
      }

      const aTime = new Date(a.time).getTime();
      const bTime = new Date(b.time).getTime();

      const safeATime = Number.isFinite(aTime) ? aTime : 0;
      const safeBTime = Number.isFinite(bTime) ? bTime : 0;

      return safeBTime - safeATime;
    })
    .slice(0, 6);
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

  const benchmarkCoordinates = hasBenchmark
    ? buildCoordinates(benchmarkValues)
    : [];

  const benchmarkLinePath = hasBenchmark
    ? buildPath(benchmarkCoordinates)
    : null;

  const portfolioLastPoint =
    portfolioCoordinates[portfolioCoordinates.length - 1] ?? null;

  const benchmarkLastPoint =
    benchmarkCoordinates[benchmarkCoordinates.length - 1] ?? null;

  const baselineY =
    chartMin <= 100 && chartMax >= 100
      ? topPadding +
        chartHeight -
        ((100 - chartMin) / (chartMax - chartMin)) * chartHeight
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

  const yTicks = [
    chartMax,
    chartMin + (chartMax - chartMin) * 0.75,
    chartMin + (chartMax - chartMin) * 0.5,
    chartMin + (chartMax - chartMin) * 0.25,
    chartMin,
  ];

  return {
    portfolioLinePath,
    portfolioAreaPath,
    benchmarkLinePath,
    portfolioLastPoint,
    benchmarkLastPoint,
    baselineY,
    labels,
    hasBenchmark,
    chartMin,
    chartMax,
    yTicks,
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
  const [newsPayload, setNewsPayload] = useState(null);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsError, setNewsError] = useState(null);
  const [newsRefreshKey, setNewsRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadMarketIntelligence() {
      setNewsLoading(true);
      setNewsError(null);

      try {
        const response = await fetch(
          "http://127.0.0.1:8000/api/news?limit=12&query=stock%20market%20OR%20S%26P%20500%20OR%20Federal%20Reserve",
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const payload = await response.json();

        if (!cancelled) {
          setNewsPayload(payload);
        }
      } catch (error) {
        if (!cancelled) {
          setNewsPayload(null);
          setNewsError(error instanceof Error ? error.message : "Request failed");
        }
      } finally {
        if (!cancelled) {
          setNewsLoading(false);
        }
      }
    }

    loadMarketIntelligence();

    return () => {
      cancelled = true;
    };
  }, [newsRefreshKey]);

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

  const riskMetrics =
    portfolioHistory?.risk_metrics ?? {};

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

  const riskVolatility =
    toFiniteNumber(riskMetrics?.volatility_pct);

  const riskSharpe =
    toFiniteNumber(riskMetrics?.sharpe_ratio);

  const riskMaxDrawdown =
    toFiniteNumber(riskMetrics?.max_drawdown_pct);

  const riskBeta =
    toFiniteNumber(riskMetrics?.beta);

  const riskTrackingError =
    toFiniteNumber(riskMetrics?.tracking_error_pct);

  const riskInformationRatio =
    toFiniteNumber(riskMetrics?.information_ratio);

  const riskObservations =
    toFiniteNumber(riskMetrics?.observations);

  const historicalAbsoluteReturn =
    toFiniteNumber(
      historicalSummary?.absolute_return
    );

  const historicalStartValue =
    toFiniteNumber(historicalSummary?.start_value);

  const historicalEndValue =
    toFiniteNumber(historicalSummary?.end_value);

  const historicalMaxValue =
    toFiniteNumber(historicalSummary?.max_value);

  const historicalMinValue =
    toFiniteNumber(historicalSummary?.min_value);

  const relativePerformanceLabel =
    alphaReturn === null
      ? "--"
      : alphaReturn > 0
        ? "OUTPERFORMING"
        : alphaReturn < 0
          ? "UNDERPERFORMING"
          : "IN LINE";

  const relativePerformanceStatus =
    alphaReturn === null
      ? "neutral"
      : getStatusFromValue(alphaReturn);

  const drawdownSeverity =
    riskMaxDrawdown === null
      ? "neutral"
      : Math.abs(riskMaxDrawdown) >= 30
        ? "negative"
        : Math.abs(riskMaxDrawdown) >= 15
          ? "warning"
          : "positive";

  const drawdownBarWidth =
    riskMaxDrawdown === null
      ? 0
      : Math.min(Math.abs(riskMaxDrawdown), 50) / 50 * 100;

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
    normalizeNews(newsPayload);

  const newsProvider =
    newsPayload?.provider ?? "Market feed";

  const newsCount =
    toFiniteNumber(newsPayload?.count);

  const newsGeneratedAt =
    newsPayload?.generated_at ?? null;

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

  const terminalMarketAssets = watchlist.slice(0, 4);

  const marketUpdatedAt =
    market?.updated_at ??
    market?.last_update ??
    market?.timestamp ??
    newsGeneratedAt ??
    null;

  const terminalRiskLabel =
    concentrationStatus === "negative"
      ? "HIGH"
      : concentrationStatus === "warning"
        ? "MODERATE"
        : concentrationStatus === "positive"
          ? "CONTROLLED"
          : "--";

  const marketRegime =
    market?.regime ??
    market?.market_regime ??
    market?.regime_label ??
    "--";

  const normalizedAiConfidence =
    toFiniteNumber(aiConfidence);

  const aiConfidenceDisplay =
    normalizedAiConfidence !== null
      ? `${normalizedAiConfidence.toLocaleString("es-ES", {
          minimumFractionDigits: 0,
          maximumFractionDigits: 0,
        })}%`
      : "--";

  const newsSentimentCounts = news.reduce(
    (accumulator, item) => {
      const sentiment = ["positive", "negative", "neutral"].includes(
        item.sentiment,
      )
        ? item.sentiment
        : "neutral";

      accumulator[sentiment] += 1;
      return accumulator;
    },
    { positive: 0, negative: 0, neutral: 0 },
  );

  const dominantNewsSentiment =
    news.length === 0
      ? "--"
      : Object.entries(newsSentimentCounts).sort(
          (a, b) => b[1] - a[1],
        )[0][0].toUpperCase();

  const decisionEngineLabel =
    String(aiStatus || "").toLowerCase() === "unavailable"
      ? "AWAITING SIGNAL"
      : String(aiStatus || "--").toUpperCase();

  return (
    <main className="gf-dashboard">
      <header className="gf-topline">
        <div className="gf-topline__identity">
          <span className="gf-product-mark">Q</span>
          <div>
            <span className="gf-kicker">QUANTUM MARKET INTELLIGENCE</span>
            <h1>Portfolio Command Center</h1>
          </div>
        </div>

        <div className="gf-topline__status">
          <div>
            <span>MARKET</span>
            <strong className={marketIsLive ? "is-positive" : ""}>
              {marketStatusText}
            </strong>
          </div>
          <div>
            <span>PORTFOLIO RISK</span>
            <strong className={`is-${concentrationStatus}`}>
              {terminalRiskLabel}
            </strong>
          </div>
          <div>
            <span>AI ENGINE</span>
            <strong>{decisionEngineLabel}</strong>
          </div>
          <div>
            <span>UPDATED</span>
            <strong>
              {marketUpdatedAt
                ? formatNewsTime(marketUpdatedAt)
                : "LIVE"}
            </strong>
          </div>
        </div>
      </header>

      <section className="gf-market-strip" aria-label="Live market strip">
        <div className="gf-market-strip__portfolio">
          <span>ACTIVE PORTFOLIO</span>
          <strong>{portfolioValueDisplay}</strong>
          <small className={`is-${totalReturnStatus}`}>
            {totalReturnPercentageDisplay} total return
          </small>
        </div>

        {watchlist.slice(0, 6).map((asset) => (
          <div className="gf-market-tile" key={asset.ticker}>
            <span>{asset.ticker}</span>
            <strong>{asset.price}</strong>
            <small className={`is-${asset.status}`}>
              {asset.change}
            </small>
          </div>
        ))}
      </section>

      <section className="gf-kpis" aria-label="Executive portfolio metrics">
        <article className="gf-kpi gf-kpi--primary">
          <div className="gf-kpi__head">
            <span>PORTFOLIO VALUE</span>
            <i>LIVE</i>
          </div>
          <strong>{portfolioValueDisplay}</strong>
          <div className="gf-kpi__footer">
            <span className={`is-${totalReturnStatus}`}>
              {totalReturnPercentageDisplay}
            </span>
            <small>Total return</small>
          </div>
        </article>

        <article className="gf-kpi">
          <div className="gf-kpi__head">
            <span>DAILY P&amp;L</span>
            <i className={`is-${dailyStatus}`}>
              {dailyStatus === "negative" ? "▼" : dailyStatus === "positive" ? "▲" : "—"}
            </i>
          </div>
          <strong>{dailyProfitLossDisplay}</strong>
          <div className="gf-kpi__footer">
            <span className={`is-${dailyStatus}`}>
              {dailyPercentageDisplay}
            </span>
            <small>vs. previous close</small>
          </div>
        </article>

        <article className="gf-kpi">
          <div className="gf-kpi__head">
            <span>TOTAL RETURN</span>
            <i>YTD</i>
          </div>
          <strong>{totalReturnPercentageDisplay}</strong>
          <div className="gf-kpi__footer">
            <span className={`is-${totalReturnStatus}`}>
              {totalProfitLossDisplay}
            </span>
            <small>Cost basis {totalCostDisplay}</small>
          </div>
        </article>

        <article className="gf-kpi">
          <div className="gf-kpi__head">
            <span>ALPHA vs S&amp;P 500</span>
            <i>{historicalPeriodLabel}</i>
          </div>
          <strong className={alphaReturn !== null ? `is-${getStatusFromValue(alphaReturn)}` : ""}>
            {alphaReturn !== null ? `${percentage(alphaReturn)} pp` : "--"}
          </strong>
          <div className="gf-kpi__footer">
            <span>
              S&amp;P {benchmarkReturn !== null ? percentage(benchmarkReturn) : "--"}
            </span>
            <small>Benchmark relative performance</small>
          </div>
        </article>
      </section>

      <section className="gf-main-grid">
        <article className="gf-panel gf-performance gf-performance--pro">
          <header className="gf-panel__header gf-performance__header">
            <div>
              <span className="gf-kicker">PORTFOLIO PERFORMANCE PRO</span>
              <h2>Portfolio vs S&amp;P 500</h2>
            </div>

            <div className="gf-performance__header-actions">
              <div className={`gf-relative-badge is-${relativePerformanceStatus}`}>
                {relativePerformanceLabel}
              </div>

              <div className="gf-period-control">
                <span>PERIOD</span>
                <div
                  className="gf-periods"
                  aria-label="Portfolio history period selector"
                >
                {PORTFOLIO_HISTORY_PERIODS.map((period) => {
                  const selected =
                    period.value === portfolioHistoryPeriod;

                  return (
                    <button
                      key={period.value}
                      type="button"
                      onClick={() =>
                        onPortfolioHistoryPeriodChange(period.value)
                      }
                      disabled={portfolioHistoryLoading}
                      className={selected ? "is-active" : ""}
                    >
                      {period.label}
                    </button>
                  );
                })}
                </div>
              </div>
            </div>
          </header>

          <div className="gf-performance__summary gf-performance__summary--pro gf-performance__summary--clean">
            <div>
              <span>{historicalPeriodLabel} PORTFOLIO RETURN</span>
              <strong
                className={
                  historicalReturn !== null
                    ? `is-${getStatusFromValue(historicalReturn)}`
                    : ""
                }
              >
                {historicalReturn !== null
                  ? percentage(historicalReturn)
                  : "--"}
              </strong>
              <small>
                {historicalAbsoluteReturn !== null
                  ? `${money(
                      historicalAbsoluteReturn,
                      portfolioCurrency,
                    )} absolute`
                  : "Absolute return --"}
              </small>
            </div>

            <div>
              <span>{historicalPeriodLabel} S&amp;P 500</span>
              <strong
                className={
                  benchmarkReturn !== null
                    ? `is-${getStatusFromValue(benchmarkReturn)}`
                    : ""
                }
              >
                {benchmarkReturn !== null
                  ? percentage(benchmarkReturn)
                  : "--"}
              </strong>
              <small>Benchmark return</small>
            </div>

            <div>
              <span>RELATIVE ALPHA</span>
              <strong
                className={
                  alphaReturn !== null
                    ? `is-${getStatusFromValue(alphaReturn)}`
                    : ""
                }
              >
                {alphaReturn !== null
                  ? `${percentage(alphaReturn)} pp`
                  : "--"}
              </strong>
              <small>{relativePerformanceLabel}</small>
            </div>

            <div>
              <span>OBSERVATIONS</span>
              <strong>
                {historicalObservations ??
                  historicalPoints.length ??
                  "--"}
              </strong>
              <small>Trading sessions</small>
            </div>
          </div>

          <div className="gf-performance__body">
            <div className="gf-performance__plot">
              <div className="gf-chart gf-chart--pro">
                <div className="gf-chart__grid" />

                {historyChart ? (
                  <>
                    <svg
                      className="gf-chart__svg"
                      viewBox="0 0 700 220"
                      preserveAspectRatio="none"
                      aria-hidden="true"
                    >
                      <defs>
                        <linearGradient
                          id="gfPortfolioArea"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#5b8cff"
                            stopOpacity="0.24"
                          />
                          <stop
                            offset="100%"
                            stopColor="#5b8cff"
                            stopOpacity="0"
                          />
                        </linearGradient>
                      </defs>

                      <path
                        className="gf-chart__area"
                        d={historyChart.portfolioAreaPath}
                        fill="url(#gfPortfolioArea)"
                      />

                      {historyChart.baselineY !== null && (
                        <line
                          className="gf-chart__baseline"
                          x1="0"
                          x2="700"
                          y1={historyChart.baselineY}
                          y2={historyChart.baselineY}
                        />
                      )}

                      <path
                        className="gf-chart__portfolio"
                        d={historyChart.portfolioLinePath}
                      />

                      {historyChart.benchmarkLinePath && (
                        <path
                          className="gf-chart__benchmark"
                          d={historyChart.benchmarkLinePath}
                        />
                      )}

                      {historyChart.portfolioLastPoint && (
                        <circle
                          className="gf-chart__endpoint gf-chart__endpoint--portfolio"
                          cx={historyChart.portfolioLastPoint.x}
                          cy={historyChart.portfolioLastPoint.y}
                          r="3.5"
                        />
                      )}

                      {historyChart.benchmarkLastPoint && (
                        <circle
                          className="gf-chart__endpoint gf-chart__endpoint--benchmark"
                          cx={historyChart.benchmarkLastPoint.x}
                          cy={historyChart.benchmarkLastPoint.y}
                          r="3"
                        />
                      )}
                    </svg>

                    <div className="gf-chart__legend">
                      <span>
                        <i className="portfolio" />
                        Portfolio
                      </span>
                      <span>
                        <i className="benchmark" />
                        S&amp;P 500
                      </span>
                      <span>
                        {historicalObservations ??
                          historicalPoints.length}{" "}
                        sessions
                      </span>
                    </div>

                    <div className="gf-chart__yaxis">
                      {historyChart.yTicks.map((tick, index) => (
                        <span key={`${tick}-${index}`}>
                          {tick.toFixed(0)}
                        </span>
                      ))}
                    </div>

                    <div className="gf-chart__axis">
                      {historyChart.labels.map(
                        (label, index) => (
                          <span key={`${label}-${index}`}>
                            {label}
                          </span>
                        ),
                      )}
                    </div>
                  </>
                ) : (
                  <div className="gf-empty">
                    Historical performance unavailable
                  </div>
                )}
              </div>
            </div>

            <aside className="gf-performance__intel">
              <div className="gf-performance-intel__title">
                <span>PERFORMANCE INTELLIGENCE</span>
                <strong>{historicalPeriodLabel}</strong>
              </div>

              <div className="gf-performance-intel__hero">
                <span>RELATIVE PERFORMANCE</span>
                <strong
                  className={`is-${relativePerformanceStatus}`}
                >
                  {relativePerformanceLabel}
                </strong>
                <small>
                  Alpha{" "}
                  {alphaReturn !== null
                    ? `${percentage(alphaReturn)} pp`
                    : "--"}
                </small>
              </div>

              <div className="gf-performance-intel__rows">
                <div>
                  <span>Start value</span>
                  <strong>
                    {historicalStartValue !== null
                      ? money(
                          historicalStartValue,
                          portfolioCurrency,
                        )
                      : "--"}
                  </strong>
                </div>

                <div>
                  <span>End value</span>
                  <strong>
                    {historicalEndValue !== null
                      ? money(
                          historicalEndValue,
                          portfolioCurrency,
                        )
                      : portfolioValueDisplay}
                  </strong>
                </div>

                <div>
                  <span>Period high</span>
                  <strong>
                    {historicalMaxValue !== null
                      ? money(
                          historicalMaxValue,
                          portfolioCurrency,
                        )
                      : "--"}
                  </strong>
                </div>

                <div>
                  <span>Period low</span>
                  <strong>
                    {historicalMinValue !== null
                      ? money(
                          historicalMinValue,
                          portfolioCurrency,
                        )
                      : "--"}
                  </strong>
                </div>
              </div>

              <div className="gf-drawdown">
                <div className="gf-drawdown__head">
                  <span>MAX DRAWDOWN</span>
                  <strong
                    className={`is-${drawdownSeverity}`}
                  >
                    {riskMaxDrawdown !== null
                      ? percentage(
                          riskMaxDrawdown,
                          {
                            showPositiveSign: false,
                          },
                        )
                      : "--"}
                  </strong>
                </div>

                <div className="gf-drawdown__track">
                  <span
                    className={`is-${drawdownSeverity}`}
                    style={{
                      width: `${drawdownBarWidth}%`,
                    }}
                  />
                </div>

                <small>
                  0% ────────────── -50%
                </small>
              </div>

            </aside>
          </div>

        </article>

        <article className="gf-panel gf-risk">
          <header className="gf-panel__header">
            <SectionIdentity icon="risk" kicker="PORTFOLIO INTELLIGENCE" title="Exposure & Risk" />
            <span className={`gf-risk__badge is-${concentrationStatus}`}>
              {terminalRiskLabel}
            </span>
          </header>

          <div className="gf-risk__hero">
            <div
              className={`gf-risk__ring is-${concentrationStatus}`}
              style={{
                "--risk-score": `${Math.min(
                  Math.max(toFiniteNumber(largestPositionWeight) ?? 0, 0),
                  100,
                )}%`,
              }}
            >
              <strong>
                {toFiniteNumber(largestPositionWeight) !== null
                  ? `${Math.round(Number(largestPositionWeight))}%`
                  : "--"}
              </strong>
              <span>MAX WEIGHT</span>
            </div>

            <div>
              <span>CONCENTRATION</span>
              <h3>{getConcentrationLabel(largestPositionWeight)}</h3>
              <p>
                Largest-position weight in the current marked-to-market portfolio.
              </p>
            </div>
          </div>

          <div className="gf-risk__scale">
            <div>
              <span>Largest position</span>
              <strong>{compactPercentage(largestPositionWeight)}</strong>
            </div>
            <div className="gf-risk__track">
              <span
                className={`is-${concentrationStatus}`}
                style={{
                  width: `${Math.min(
                    Math.max(toFiniteNumber(largestPositionWeight) ?? 0, 0),
                    100,
                  )}%`,
                }}
              />
            </div>
          </div>

          <div className="gf-risk__metrics">
            <div>
              <span>BETA</span>
              <strong>{riskBeta !== null ? riskBeta.toFixed(2) : "--"}</strong>
            </div>
            <div>
              <span>VOLATILITY</span>
              <strong>
                {riskVolatility !== null
                  ? percentage(riskVolatility, { showPositiveSign: false })
                  : "--"}
              </strong>
            </div>
            <div>
              <span>MAX DD</span>
              <strong className="is-negative">
                {riskMaxDrawdown !== null
                  ? percentage(riskMaxDrawdown, { showPositiveSign: false })
                  : "--"}
              </strong>
            </div>
            <div>
              <span>SHARPE</span>
              <strong>{riskSharpe !== null ? riskSharpe.toFixed(2) : "--"}</strong>
            </div>
          </div>

          <div className="gf-allocation">
            <div className="gf-subhead">
              <span>SECTOR EXPOSURE</span>
              <small>{sectorCount} groups</small>
            </div>

            {allocation.length > 0 ? (
              allocation.map((item) => {
                const value = Math.min(
                  Math.max(toFiniteNumber(item.value) ?? 0, 0),
                  100,
                );

                return (
                  <div className="gf-allocation__row" key={item.label}>
                    <div>
                      <span>{item.label}</span>
                      <strong>{value.toFixed(0)}%</strong>
                    </div>
                    <div>
                      <span style={{ width: `${value}%` }} />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="gf-empty gf-empty--small">
                No allocation data available.
              </div>
            )}
          </div>

          <div className="gf-risk__footer">
            <div>
              <span>PRICE COVERAGE</span>
              <strong>{compactPercentage(priceCoverage)}</strong>
            </div>
            <div>
              <span>OPEN POSITIONS</span>
              <strong>{positions.length}</strong>
            </div>
          </div>
        </article>

        <article className="gf-panel gf-decision gf-decision--primary">
          <header className="gf-panel__header">
            <SectionIdentity icon="decision" kicker="QMI DECISION ENGINE" title="Decision Intelligence" />
            <span className="gf-panel__counter">{insights.length} MODEL SIGNALS</span>
          </header>

          <div className="gf-decision__overview">
            <div className="gf-decision__signal">
              <i className="gf-context-icon"><QmiIcon name="decision" size={15} /></i>
              <span>GLOBAL SIGNAL</span>
              <strong>{decisionEngineLabel}</strong>
              <small>
                {insights.length > 0
                  ? "Decision-engine output available"
                  : "Awaiting model signals"}
              </small>
            </div>

            <div>
              <i className="gf-context-icon"><QmiIcon name="performance" size={15} /></i>
              <span>CONFIDENCE</span>
              <strong>{aiConfidenceDisplay}</strong>
              <small>Model confidence</small>
            </div>

            <div>
              <i className="gf-context-icon"><QmiIcon name="market" size={15} /></i>
              <span>MARKET REGIME</span>
              <strong>{String(marketRegime).toUpperCase()}</strong>
              <small>{marketStatusText}</small>
            </div>

            <div>
              <i className="gf-context-icon"><QmiIcon name="risk" size={15} /></i>
              <span>PORTFOLIO RISK</span>
              <strong className={`is-${concentrationStatus}`}>
                {terminalRiskLabel}
              </strong>
              <small>{getConcentrationLabel(largestPositionWeight)}</small>
            </div>
          </div>

          <div className="gf-factor-table">
            <div className="gf-factor-table__head">
              <span>FACTOR</span>
              <span>SIGNAL</span>
              <span>CONTEXT</span>
            </div>

            <div>
              <strong className="gf-factor-name"><i><QmiIcon name="performance" size={14} /></i>Technical</strong>
              <span>--</span>
              <small>Awaiting technical signal</small>
            </div>

            <div>
              <strong className="gf-factor-name"><i><QmiIcon name="command" size={14} /></i>Fundamental</strong>
              <span>--</span>
              <small>Awaiting fundamental score</small>
            </div>

            <div>
              <strong className="gf-factor-name"><i><QmiIcon name="market" size={14} /></i>Market</strong>
              <span>{String(marketRegime).toUpperCase()}</span>
              <small>{marketStatusText}</small>
            </div>

            <div>
              <strong className="gf-factor-name"><i><QmiIcon name="risk" size={14} /></i>Risk</strong>
              <span className={`is-${concentrationStatus}`}>{terminalRiskLabel}</span>
              <small>
                Beta {riskBeta !== null ? riskBeta.toFixed(2) : "--"} · DD{" "}
                {riskMaxDrawdown !== null
                  ? percentage(riskMaxDrawdown, {
                      showPositiveSign: false,
                      maximumFractionDigits: 1,
                    })
                  : "--"}
              </small>
            </div>

            <div>
              <strong className="gf-factor-name"><i><QmiIcon name="news" size={14} /></i>News Sentiment</strong>
              <span>{dominantNewsSentiment}</span>
              <small>{news.length} ranked articles</small>
            </div>
          </div>

          <div className="gf-decision__live">
            {insights.length > 0 ? (
              insights.map((insight, index) => (
                <div key={`${insight.title}-${index}`}>
                  <span className={`gf-signal-dot is-${insight.status}`} />
                  <div>
                    <small>{insight.type}</small>
                    <strong>{insight.title}</strong>
                    <p>{insight.description}</p>
                  </div>
                </div>
              ))
            ) : (
              <div>
                <span className="gf-signal-dot" />
                <div>
                  <strong>Decision engine awaiting model signals</strong>
                  <p>
                    Live market, portfolio, risk and news context is available.
                    Model-derived recommendations remain blank until the AI endpoint
                    provides validated signals.
                  </p>
                </div>
              </div>
            )}
          </div>
        </article>
      </section>

      <section className="gf-panel gf-news">
        <header className="gf-panel__header">
          <SectionIdentity icon="news" kicker="INFORMATION FLOW" title="Market Intelligence" />

          <div className="gf-news__actions">
            <span>{newsCount ?? news.length} ARTICLES</span>
            <button
              type="button"
              onClick={() => setNewsRefreshKey((value) => value + 1)}
              disabled={newsLoading}
            >
              {newsLoading ? "REFRESHING" : "REFRESH"}
            </button>
          </div>
        </header>

        <div className="gf-news__meta">
          <span>{newsProvider}</span>
          <span>
            {newsGeneratedAt ? `Updated ${formatNewsTime(newsGeneratedAt)}` : "Live market feed"}
          </span>
        </div>

        {newsError ? (
          <div className="gf-empty">
            Market intelligence unavailable: {newsError}
          </div>
        ) : news.length > 0 ? (
          <div className="gf-news__grid">
            {news.map((item, index) => (
              <article className="gf-news-card" key={`${item.title}-${index}`}>
                <div className="gf-news-card__meta">
                  <span>{item.source}</span>
                  <time>{formatNewsTime(item.time)}</time>
                </div>

                <div className="gf-news-card__badges">
                  <span className={`is-${item.sentiment}`}>
                    {item.sentiment.toUpperCase()}
                  </span>
                  <span className={`impact-${item.impact}`}>
                    {item.impact.toUpperCase()} IMPACT
                  </span>
                </div>

                <h3>
                  {item.url ? (
                    <a href={item.url} target="_blank" rel="noreferrer">
                      {item.title}
                    </a>
                  ) : (
                    item.title
                  )}
                </h3>
              </article>
            ))}
          </div>
        ) : (
          <div className="gf-empty">
            {newsLoading
              ? "Loading market intelligence…"
              : "No market intelligence articles available."}
          </div>
        )}
      </section>
    </main>
  );
}

export default Dashboard;

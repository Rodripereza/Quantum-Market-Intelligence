import {
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  CircleDot,
  Crosshair,
  TrendingUp,
  Wallet,
} from "lucide-react";

import MarketBreadthCard from "../components/overview/MarketBreadthCard";
import MarketSnapshot from "../components/overview/MarketSnapshot";
import PositionAllocationChart from "../components/overview/PositionAllocationChart";
import SectorExposureChart from "../components/overview/SectorExposureChart";
import TopMoversCard from "../components/overview/TopMoversCard";
import PortfolioIntelligenceCard from "../components/overview/PortfolioIntelligenceCard";
import PortfolioPerformanceCard from "../components/overview/PortfolioPerformanceCard";

const FALLBACK_MARKET_ASSETS = [
  {
    ticker: "SPY",
    name: "S&P 500 ETF",
    price: 634.18,
    change_pct: 0.62,
  },
  {
    ticker: "QQQ",
    name: "Nasdaq 100 ETF",
    price: 568.42,
    change_pct: 0.84,
  },
  {
    ticker: "DIA",
    name: "Dow Jones ETF",
    price: 451.27,
    change_pct: 0.31,
  },
  {
    ticker: "IWM",
    name: "Russell 2000 ETF",
    price: 229.76,
    change_pct: -0.48,
  },
  {
    ticker: "VIX",
    name: "Volatility Index",
    price: 16.21,
    change_pct: -3.14,
  },
  {
    ticker: "DXY",
    name: "US Dollar Index",
    price: 97.63,
    change_pct: 0.18,
  },
];

function money(number, currency = "USD") {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(Number(number));
}

function percentage(number) {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  const value = Number(number);

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function MetricCard({
  className = "",
  icon: Icon,
  label,
  value,
  detail,
  tone = "neutral",
}) {
  return (
    <article className={`overview-kpi-card ${tone} ${className}`.trim()}>
      <div className="overview-kpi-icon">
        <Icon size={20} strokeWidth={1.8} />
      </div>

      <div className="overview-kpi-content">
        <span className="overview-kpi-label">{label}</span>
        <strong className="overview-kpi-value">{value}</strong>
        <span className="overview-kpi-detail">{detail}</span>
      </div>
    </article>
  );
}

function Overview({
  portfolio,
  market,
  ai,
  allocation,
  sectorAllocation,
  performanceData,
  navigate,
}) {
  const safePortfolio = portfolio ?? {};
  const safeMarket = market ?? {};
  const resolvedMarket = {
    ...safeMarket,
    assets:
      Array.isArray(safeMarket.assets) &&
      safeMarket.assets.length > 0
        ? safeMarket.assets
        : FALLBACK_MARKET_ASSETS,
  };

  const safeAi = ai ?? {};

  const safeAllocation = Array.isArray(allocation)
    ? allocation
    : [];

  const safeSectorAllocation = Array.isArray(
    sectorAllocation
  )
    ? sectorAllocation
    : [];

  const safeNavigate =
    typeof navigate === "function"
      ? navigate
      : () => {};

  const totalValue =
    safePortfolio.total_value ??
    safePortfolio.market_value ??
    safePortfolio.total_cost;

  const dailyProfitLoss = Number(
    safePortfolio.daily_profit_loss ??
      safePortfolio.total_pl ??
      0
  );

  const dailyReturn = Number(
    safePortfolio.daily_return ??
      safePortfolio.daily_pl_pct ??
      0
  );

  const totalReturn = Number(
    safePortfolio.total_return_pct ??
      safePortfolio.total_pl_pct ??
      0
  );

  const aiOutlook = String(
    safeAi.outlook ??
      safeAi.market_outlook ??
      safeAi.signal ??
      "Neutral"
  ).toUpperCase();

  const aiConfidence = Number(
    safeAi.confidence ??
      safeAi.confidence_score ??
      safeAi.score ??
      0
  );

  const dailyTone =
    dailyProfitLoss > 0
      ? "positive"
      : dailyProfitLoss < 0
        ? "negative"
        : "neutral";

  const totalReturnTone =
    totalReturn > 0
      ? "positive"
      : totalReturn < 0
        ? "negative"
        : "neutral";

  const aiTone =
    aiOutlook.includes("BULL") ||
    aiOutlook.includes("POSITIVE") ||
    aiOutlook.includes("BUY")
      ? "positive"
      : aiOutlook.includes("BEAR") ||
          aiOutlook.includes("NEGATIVE") ||
          aiOutlook.includes("SELL")
        ? "negative"
        : "neutral";

  const DailyIcon =
    dailyProfitLoss >= 0
      ? ArrowUpRight
      : ArrowDownRight;

  return (
    <div className="overview-dashboard overview-executive-v4">
      <section className="overview-titlebar">
        <div>
          <div className="overview-titlebar-kicker">
            <CircleDot size={11} />
            QMI EXECUTIVE COMMAND
          </div>

          <h1>Overview</h1>
          <p>Executive Summary</p>
        </div>

        <div className="overview-titlebar-status">
          <span className="overview-market-status-dot" />
          Market Open
        </div>
      </section>

      <section className="overview-kpi-grid">
        <MetricCard
          icon={Wallet}
          label="Portfolio Value"
          value={money(totalValue)}
          detail={`${percentage(dailyReturn)} today`}
          tone="primary"
        />

        <MetricCard
          icon={DailyIcon}
          label="Daily P/L"
          value={money(dailyProfitLoss)}
          detail={percentage(dailyReturn)}
          tone={dailyTone}
        />

        <MetricCard
          icon={Crosshair}
          label="Total Return"
          value={percentage(totalReturn)}
          detail="Since inception"
          tone={totalReturnTone}
        />

        <MetricCard
          icon={BrainCircuit}
          label="AI Outlook"
          value={aiOutlook}
          detail={`${aiConfidence.toFixed(0)}% confidence`}
          tone={aiTone}
          className="overview-kpi-ai"
        />
      </section>

      <section className="overview-hero-grid">
        <PortfolioPerformanceCard
          performanceData={performanceData}
        />

        <PortfolioIntelligenceCard
          portfolio={safePortfolio}
          ai={safeAi}
        />
      </section>

      <section className="overview-secondary-grid">
        <MarketSnapshot
          market={resolvedMarket}
          navigate={safeNavigate}
        />

        <MarketBreadthCard />

        <TopMoversCard />

        <PositionAllocationChart
          allocation={safeAllocation}
          navigate={safeNavigate}
        />
      </section>

      <section className="overview-bottom-grid">
        <SectorExposureChart
          sectorAllocation={safeSectorAllocation}
        />

        <article className="overview-ai-summary-card">
          <header className="overview-ai-summary-header">
            <div className="overview-ai-summary-icon">
              <BrainCircuit size={17} strokeWidth={1.8} />
            </div>

            <div>
              <span>AI Market Summary</span>
              <strong>Executive interpretation</strong>
            </div>
          </header>

          <div className="overview-ai-summary-body">
            <p>
              Portfolio momentum remains constructive while
              risk conditions stay within normal operating
              ranges.
            </p>

            <p>
              Market breadth, trend confirmation and current
              exposure should be evaluated together before
              any portfolio adjustment.
            </p>
          </div>

          <footer className="overview-ai-summary-footer">
            <TrendingUp size={14} />
            QMI intelligence layer
          </footer>
        </article>
      </section>
    </div>
  );
}

export default Overview;
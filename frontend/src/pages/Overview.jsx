import {
  ArrowDownRight,
  ArrowUpRight,
  BriefcaseBusiness,
  CircleDot,
  Wallet,
} from "lucide-react";

import MarketBreadthCard from "../components/overview/MarketBreadthCard";
import MarketSnapshot from "../components/overview/MarketSnapshot";
import MarketTrendChart from "../components/overview/MarketTrendChart";
import PortfolioIntelligenceCard from "../components/overview/PortfolioIntelligenceCard";
import PortfolioPerformanceCard from "../components/overview/PortfolioPerformanceCard";
import PositionAllocationChart from "../components/overview/PositionAllocationChart";
import SectorExposureChart from "../components/overview/SectorExposureChart";
import TopMoversCard from "../components/overview/TopMoversCard";

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

function Overview({
  portfolio,
  market,
  ai,
  trend,
  allocation,
  sectorAllocation,
  performanceData,
  navigate,
}) {
  const safePortfolio = portfolio ?? {};
  const safeMarket = market ?? {};
  const safeAi = ai ?? {};

  const safeTrend = Array.isArray(trend)
    ? trend
    : [];

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
      safePortfolio.total_pl_pct ??
      0
  );

  const positionCount =
    safePortfolio.position_count ?? 0;

  const cashPercentage = Number(
    safePortfolio.cash_percentage ?? 0
  );

  const performanceTone =
    dailyProfitLoss > 0
      ? "positive"
      : dailyProfitLoss < 0
        ? "negative"
        : "neutral";

  const PerformanceIcon =
    dailyProfitLoss >= 0
      ? ArrowUpRight
      : ArrowDownRight;

  return (
    <div className="overview-dashboard institutional-overview">
      <section className="terminal-command-header">
        <div className="terminal-command-identity">
          <div className="terminal-command-label">
            <CircleDot size={12} />
            QMI PORTFOLIO COMMAND
          </div>

          <h2>Portfolio Overview</h2>

          <p>
            Real-time performance, exposure, risk and
            intelligence monitoring.
          </p>
        </div>

        <div className="terminal-command-stats">
          <div className="terminal-primary-value">
            <span>Net portfolio value</span>

            <strong>{money(totalValue)}</strong>
          </div>

          <div
            className={`terminal-daily-change ${performanceTone}`}
          >
            <PerformanceIcon size={18} />

            <div>
              <strong>
                {percentage(dailyReturn)}
              </strong>

              <span>
                {money(dailyProfitLoss)} today
              </span>
            </div>
          </div>

          <div className="terminal-header-stat">
            <Wallet size={16} />

            <div>
              <span>Positions</span>
              <strong>{positionCount}</strong>
            </div>
          </div>

          <div className="terminal-header-stat">
            <BriefcaseBusiness size={16} />

            <div>
              <span>Cash</span>
              <strong>
                {cashPercentage.toFixed(1)}%
              </strong>
            </div>
          </div>
        </div>
      </section>

      <section className="institutional-primary-grid">
        <PortfolioPerformanceCard
          performanceData={performanceData}
        />

        <PortfolioIntelligenceCard
          portfolio={safePortfolio}
          ai={safeAi}
        />
      </section>

      <section className="institutional-market-grid">
        <MarketTrendChart trend={safeTrend} />

        <MarketSnapshot
          market={safeMarket}
          navigate={safeNavigate}
        />
      </section>

      <section className="institutional-secondary-grid">
        <TopMoversCard />

        <MarketBreadthCard />
      </section>

      <section className="institutional-allocation-grid">
        <PositionAllocationChart
          allocation={safeAllocation}
          navigate={safeNavigate}
        />

        <SectorExposureChart
          sectorAllocation={
            safeSectorAllocation
          }
        />
      </section>
    </div>
  );
}

export default Overview;
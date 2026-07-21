import {
  Brain,
  BriefcaseBusiness,
  CircleDollarSign,
  Layers3,
  LineChart,
  Wallet,
} from "lucide-react";

import ExecutiveMetric from "../components/overview/ExecutiveMetric";
import HeroMiniMetric from "../components/overview/HeroMiniMetric";
import HeroValueCard from "../components/overview/HeroValueCard";
import MarketSnapshot from "../components/overview/MarketSnapshot";
import MarketTrendChart from "../components/overview/MarketTrendChart";
import PositionAllocationChart from "../components/overview/PositionAllocationChart";
import SectorExposureChart from "../components/overview/SectorExposureChart";

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
    maximumFractionDigits: 2,
  }).format(number);
}

function pct(number) {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return `${Number(number || 0).toFixed(2)}%`;
}

function Overview({
  portfolio,
  market,
  ai,
  trend,
  allocation,
  sectorAllocation,
  navigate,
}) {
  return (
    <div className="overview-dashboard">
      <section className="executive-hero">
        <div className="executive-hero-copy">
          <div className="executive-label">
            <span className="executive-pulse" />
            QMI EXECUTIVE WORKSPACE
          </div>

          <h2>Portfolio intelligence at a glance</h2>

          <p>
            Consolidated market, portfolio, risk and AI intelligence from your
            private investment workspace.
          </p>

          <div className="hero-mini-metrics">
            <HeroMiniMetric
              label="AI confidence"
              value={ai?.confidence ? `${ai.confidence}%` : "--"}
              detail={ai?.status || "Analytical engine"}
              icon={<Brain size={19} />}
              tone="primary"
            />

            <HeroMiniMetric
              label="Portfolio"
              value={`${portfolio?.position_count ?? 0} positions`}
              detail={
                portfolio?.position_count > 0
                  ? "Portfolio active"
                  : "Awaiting positions"
              }
              icon={<Wallet size={19} />}
              tone={
                portfolio?.position_count > 0 ? "positive" : "neutral"
              }
            />
          </div>

          <div className="executive-actions">
            <button
              className="primary-overview-action"
              onClick={() => navigate("portfolio")}
            >
              <BriefcaseBusiness size={16} />
              Manage Portfolio
            </button>

            <button
              className="secondary-overview-action"
              onClick={() => navigate("market")}
            >
              <LineChart size={16} />
              Explore Markets
            </button>
          </div>
        </div>

        <HeroValueCard portfolio={portfolio} />
      </section>

      <section className="executive-metrics-grid">
        <ExecutiveMetric
          label="Cost basis"
          value={money(portfolio?.total_cost)}
          description="Capital currently invested"
          icon={<CircleDollarSign size={18} />}
        />

        <ExecutiveMetric
          label="Open positions"
          value={portfolio?.position_count ?? "--"}
          description="Active portfolio holdings"
          icon={<Wallet size={18} />}
        />

        <ExecutiveMetric
          label="Largest exposure"
          value={pct(portfolio?.largest_position_weight)}
          description="Maximum individual position weight"
          icon={<Layers3 size={18} />}
          tone="warning"
        />

        <ExecutiveMetric
          label="AI intelligence"
          value={ai?.status || "Loading"}
          description="Analytical architecture status"
          icon={<Brain size={18} />}
          tone="primary"
        />
      </section>

      <section className="overview-main-grid">
        <MarketTrendChart trend={trend} />

        <MarketSnapshot
          market={market}
          navigate={navigate}
        />
      </section>

      <section className="overview-allocation-grid">
        <PositionAllocationChart
          allocation={allocation}
          navigate={navigate}
        />

        <SectorExposureChart
          sectorAllocation={sectorAllocation}
        />
      </section>
    </div>
  );
}

export default Overview;
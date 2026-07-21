import {
  Activity,
  ArrowUpRight,
  Brain,
  BriefcaseBusiness,
  ChartNoAxesCombined,
  CircleDollarSign,
  Layers3,
  LineChart,
  Radar,
  ShieldCheck,
  TrendingUp,
  Wallet
} from "lucide-react";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import ExecutiveMetric from "../components/overview/ExecutiveMetric";
import EmptyChartState from "../components/overview/EmptyChartState";

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
    maximumFractionDigits: 2
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

function MarketSnapshot({ market, navigate }) {
  const assets = market?.assets || [];

  return (
    <section className="overview-surface market-snapshot">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            LIVE INTELLIGENCE
          </span>

          <h2>Market Snapshot</h2>

          <p>
            Current prices and daily market movement
          </p>
        </div>

        <button
          className="overview-icon-action"
          onClick={() => navigate("market")}
          title="Open Market"
        >
          <ArrowUpRight size={17} />
        </button>
      </div>

      {assets.length > 0 ? (
        <div className="market-snapshot-list">
          {assets.slice(0, 6).map((asset) => (
            <div
              className="market-snapshot-row"
              key={asset.ticker}
            >
              <div className="market-symbol">
                <strong>{asset.ticker}</strong>
                <span>{asset.name}</span>
              </div>

              <div className="market-price">
                <strong>{money(asset.price)}</strong>

                <span
                  className={
                    asset.change_pct >= 0
                      ? "market-change positive"
                      : "market-change negative"
                  }
                >
                  {pct(asset.change_pct)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyChartState
          icon={<Radar size={22} />}
          title="Market feed unavailable"
          description="Start the backend to load the current market snapshot."
          action="Open Market"
          onAction={() => navigate("market")}
        />
      )}
    </section>
  );
}

function Overview({
  portfolio,
  market,
  ai,
  trend,
  allocation,
  sectorAllocation,
  navigate
}) {
  const totalPL = Number(portfolio?.total_pl || 0);
  const totalPLPct = Number(portfolio?.total_pl_pct || 0);

  const hasAllocation = allocation?.length > 0;
  const hasSectorAllocation = sectorAllocation?.length > 0;

  return (
    <div className="overview-dashboard">
      <section className="executive-hero">
        <div className="executive-hero-copy">
          <div className="executive-label">
            <span className="executive-pulse" />
            QMI EXECUTIVE WORKSPACE
          </div>

          <h2>
            Portfolio intelligence at a glance
          </h2>

          <p>
            Consolidated market, portfolio, risk and AI
            intelligence from your private investment
            workspace.
          </p>

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

        <div className="hero-portfolio-value">
          <span>Total portfolio value</span>

          <strong>
            {money(portfolio?.total_value)}
          </strong>

          <div
            className={
              totalPL >= 0
                ? "hero-performance positive"
                : "hero-performance negative"
            }
          >
            <TrendingUp size={15} />

            <span>
              {money(portfolio?.total_pl)} ·{" "}
              {pct(totalPLPct)}
            </span>
          </div>

          <small>
            Updated from the persistent QMI portfolio
            engine
          </small>
        </div>
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
          value={pct(
            portfolio?.largest_position_weight
          )}
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
        <section className="overview-surface trend-surface">
          <div className="overview-section-heading">
            <div>
              <span className="section-kicker">
                ANALYTICAL SIGNAL
              </span>

              <h2>Market Intelligence Trend</h2>

              <p>
                Composite foundation signal over the last
                six months
              </p>
            </div>

            <div className="chart-period-selector">
              <button>1M</button>
              <button>3M</button>
              <button className="active">6M</button>
              <button>1Y</button>
            </div>
          </div>

          <div className="trend-chart">
            <ResponsiveContainer
              width="100%"
              height={310}
            >
              <AreaChart
                data={trend}
                margin={{
                  top: 18,
                  right: 8,
                  left: -16,
                  bottom: 0
                }}
              >
                <defs>
                  <linearGradient
                    id="qmiTrendGradient"
                    x1="0"
                    y1="0"
                    x2="0"
                    y2="1"
                  >
                    <stop
                      offset="0%"
                      stopColor="#648fff"
                      stopOpacity={0.34}
                    />

                    <stop
                      offset="100%"
                      stopColor="#648fff"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  strokeDasharray="2 5"
                  stroke="#202b3a"
                  vertical={false}
                />

                <XAxis
                  dataKey="month"
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <YAxis
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <Tooltip
                  contentStyle={{
                    background: "#101722",
                    border: "1px solid #2b3b50",
                    borderRadius: "10px",
                    boxShadow:
                      "0 16px 40px rgba(0,0,0,.4)"
                  }}
                  labelStyle={{
                    color: "#a9b5c5"
                  }}
                />

                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#648fff"
                  strokeWidth={2.4}
                  fill="url(#qmiTrendGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="trend-footer">
            <div>
              <Activity size={15} />
              <span>Signal momentum</span>
              <strong>Positive</strong>
            </div>

            <div>
              <ShieldCheck size={15} />
              <span>Risk state</span>
              <strong>Controlled</strong>
            </div>

            <div>
              <ChartNoAxesCombined size={15} />
              <span>Trend score</span>
              <strong>
                {trend?.at(-1)?.value ?? "--"}
              </strong>
            </div>
          </div>
        </section>

        <MarketSnapshot
          market={market}
          navigate={navigate}
        />
      </section>

      <section className="overview-allocation-grid">
        <section className="overview-surface">
          <div className="overview-section-heading">
            <div>
              <span className="section-kicker">
                PORTFOLIO STRUCTURE
              </span>

              <h2>Position Allocation</h2>

              <p>
                Market value distribution across holdings
              </p>
            </div>

            <button
              className="overview-text-action"
              onClick={() => navigate("portfolio")}
            >
              View portfolio
              <ArrowUpRight size={14} />
            </button>
          </div>

          {hasAllocation ? (
            <ResponsiveContainer
              width="100%"
              height={250}
            >
              <BarChart
                data={allocation}
                margin={{
                  top: 18,
                  right: 8,
                  left: -12,
                  bottom: 0
                }}
              >
                <CartesianGrid
                  strokeDasharray="2 5"
                  stroke="#202b3a"
                  vertical={false}
                />

                <XAxis
                  dataKey="ticker"
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <YAxis
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <Tooltip
                  formatter={(value) => money(value)}
                  contentStyle={{
                    background: "#101722",
                    border: "1px solid #2b3b50",
                    borderRadius: "10px"
                  }}
                />

                <Bar
                  dataKey="value"
                  fill="#648fff"
                  radius={[5, 5, 0, 0]}
                  maxBarSize={42}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState
              icon={<Wallet size={22} />}
              title="No portfolio positions"
              description="Add your first holding to generate the allocation chart."
              action="Add position"
              onAction={() => navigate("portfolio")}
            />
          )}
        </section>

        <section className="overview-surface">
          <div className="overview-section-heading">
            <div>
              <span className="section-kicker">
                RISK DISTRIBUTION
              </span>

              <h2>Sector Exposure</h2>

              <p>
                Capital concentration by economic sector
              </p>
            </div>
          </div>

          {hasSectorAllocation ? (
            <ResponsiveContainer
              width="100%"
              height={250}
            >
              <BarChart
                data={sectorAllocation}
                layout="vertical"
                margin={{
                  top: 12,
                  right: 15,
                  left: 15,
                  bottom: 0
                }}
              >
                <CartesianGrid
                  strokeDasharray="2 5"
                  stroke="#202b3a"
                  horizontal={false}
                />

                <XAxis
                  type="number"
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <YAxis
                  type="category"
                  dataKey="sector"
                  width={90}
                  stroke="#68768a"
                  tickLine={false}
                  axisLine={false}
                  tick={{
                    fontSize: 11
                  }}
                />

                <Tooltip
                  formatter={(value) => money(value)}
                  contentStyle={{
                    background: "#101722",
                    border: "1px solid #2b3b50",
                    borderRadius: "10px"
                  }}
                />

                <Bar
                  dataKey="value"
                  fill="#41c7a1"
                  radius={[0, 5, 5, 0]}
                  maxBarSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState
              icon={<Layers3 size={22} />}
              title="No sector exposure"
              description="Sector distribution will appear after portfolio positions are loaded."
            />
          )}
        </section>
      </section>
    </div>
  );
}

export default Overview;
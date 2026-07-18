import {
  Activity,
  Brain,
  LineChart,
  Wallet,
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
  YAxis,
} from "recharts";

import Card from "../components/ui/Card";
import Panel from "../components/ui/Panel";

function money(value, currency = "USD") {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

function pct(value) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(Number(value))
  ) {
    return "--";
  }

  return `${Number(value || 0).toFixed(2)}%`;
}

function MarketPanel({ market }) {
  return (
    <Panel
      title="Market Overview"
      subtitle={market?.source || "loading"}
    >
      {(market?.assets || []).map((asset) => (
        <div className="row" key={asset.ticker}>
          <div>
            <strong>{asset.ticker}</strong>
            <span>{asset.name}</span>
          </div>

          <div>
            <strong>{money(asset.price)}</strong>

            <em className={asset.change_pct >= 0 ? "pos" : "neg"}>
              {pct(asset.change_pct)}
            </em>
          </div>
        </div>
      ))}
    </Panel>
  );
}

export default function Overview({
  portfolio,
  market,
  ai,
  trend,
  allocation,
  sectorAllocation,
  navigate,
}) {
  return (
    <>
      <div className="grid4">
        <Card
          title="Portfolio Value"
          value={money(portfolio?.total_value)}
          subtitle="SQLite portfolio data"
          icon={<Wallet size={18} />}
        />

        <Card
          title="Total P/L"
          value={money(portfolio?.total_pl)}
          subtitle={`${pct(portfolio?.total_pl_pct)} total result`}
          icon={<Activity size={18} />}
        />

        <Card
          title="Open Positions"
          value={portfolio?.position_count ?? "--"}
          subtitle={`Largest weight ${pct(
            portfolio?.largest_position_weight
          )}`}
          icon={<LineChart size={18} />}
        />

        <Card
          title="AI Layer"
          value={ai?.status || "Loading"}
          subtitle="Architecture prepared"
          icon={<Brain size={18} />}
        />
      </div>

      <div className="quick-grid">
        <button type="button" onClick={() => navigate("market")}>
          Open Market
        </button>

        <button type="button" onClick={() => navigate("portfolio")}>
          Open Portfolio
        </button>

        <button type="button" onClick={() => navigate("ai")}>
          Open AI Layer
        </button>

        <button type="button" onClick={() => navigate("risk")}>
          Open Risk
        </button>
      </div>

      <div className="layout">
        <Panel
          title="Market Intelligence Trend"
          subtitle="Foundation analytical signal"
        >
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trend}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#20314d"
              />

              <XAxis dataKey="month" stroke="#9db7df" />
              <YAxis stroke="#9db7df" />
              <Tooltip />

              <Area
                type="monotone"
                dataKey="value"
                stroke="#3da5ff"
                fill="#163d63"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        <MarketPanel market={market} />
      </div>

      <div className="layout">
        <Panel
          title="Portfolio Allocation"
          subtitle="Position value distribution"
        >
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={allocation}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#20314d"
              />

              <XAxis dataKey="ticker" stroke="#9db7df" />
              <YAxis stroke="#9db7df" />
              <Tooltip />

              <Bar
                dataKey="value"
                fill="#3da5ff"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel
          title="Sector Exposure"
          subtitle="Allocation by sector"
        >
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={sectorAllocation}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#20314d"
              />

              <XAxis dataKey="sector" stroke="#9db7df" />
              <YAxis stroke="#9db7df" />
              <Tooltip />

              <Bar
                dataKey="value"
                fill="#3da5ff"
                radius={[8, 8, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>
    </>
  );
}
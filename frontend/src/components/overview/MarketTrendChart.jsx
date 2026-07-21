import {
  Activity,
  ChartNoAxesCombined,
  ShieldCheck,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function MarketTrendChart({ trend = [] }) {
  return (
    <section className="overview-surface trend-surface">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            ANALYTICAL SIGNAL
          </span>

          <h2>Market Intelligence Trend</h2>

          <p>
            Composite foundation signal over the last six months
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
        <ResponsiveContainer width="100%" height={310}>
          <AreaChart
            data={trend}
            margin={{
              top: 18,
              right: 8,
              left: -16,
              bottom: 0,
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
              tick={{ fontSize: 11 }}
            />

            <YAxis
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11 }}
            />

            <Tooltip
              contentStyle={{
                background: "#101722",
                border: "1px solid #2b3b50",
                borderRadius: "10px",
                boxShadow: "0 16px 40px rgba(0,0,0,.4)",
              }}
              labelStyle={{
                color: "#a9b5c5",
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
          <strong>{trend?.at(-1)?.value ?? "--"}</strong>
        </div>
      </div>
    </section>
  );
}

export default MarketTrendChart;
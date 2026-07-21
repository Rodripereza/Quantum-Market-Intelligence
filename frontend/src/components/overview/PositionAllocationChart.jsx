import { ArrowUpRight, Wallet } from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import EmptyChartState from "./EmptyChartState";

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

function PositionAllocationChart({
  allocation = [],
  navigate,
}) {
  const hasAllocation = allocation.length > 0;

  return (
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
              bottom: 0,
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
                fontSize: 11,
              }}
            />

            <YAxis
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{
                fontSize: 11,
              }}
            />

            <Tooltip
              formatter={(value) => money(value)}
              contentStyle={{
                background: "#101722",
                border: "1px solid #2b3b50",
                borderRadius: "10px",
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
  );
}

export default PositionAllocationChart;
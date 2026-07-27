import { ArrowUpRight, Wallet } from "lucide-react";
import EmptyChartState from "./EmptyChartState";
import SectionHeader from "../ui/SectionHeader";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
    <section className="overview-surface position-allocation-card">
      <SectionHeader
        size="compact"
        eyebrow="Portfolio Structure"
        title="Position Allocation"
        subtitle="Market value distribution across holdings"
        actions={
          <button
            className="overview-text-action"
            type="button"
            onClick={() => navigate("portfolio")}
          >
            View portfolio
            <ArrowUpRight size={14} />
          </button>
        }
      />

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
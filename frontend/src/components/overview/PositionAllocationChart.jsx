import { ArrowUpRight, Wallet } from "lucide-react";

import EmptyChartState from "./EmptyChartState";
import SectionHeader from "../ui/SectionHeader";
import Card from "../ui/Card";
import ChartTooltip from "../ui/charts/ChartTooltip";
import { chartTheme } from "../ui/charts/chartTheme";

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
    <Card
      surface
      variant="default"
      hover={false}
      className="position-allocation-card"
    >
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
              stroke={chartTheme.colors.grid}
              strokeDasharray={
                chartTheme.grid.strokeDasharray
              }
              vertical={false}
            />

            <XAxis
              dataKey="ticker"
              stroke={chartTheme.colors.axis}
              tickLine={false}
              axisLine={false}
              tick={{
                fontSize:
                  chartTheme.typography.xAxisFontSize,
                fontFamily:
                  chartTheme.typography.axisFontFamily,
                fill: chartTheme.colors.axisText,
              }}
            />

            <YAxis
              stroke={chartTheme.colors.axis}
              tickLine={false}
              axisLine={false}
              tick={{
                fontSize:
                  chartTheme.typography.yAxisFontSize,
                fill: chartTheme.colors.axisText,
              }}
            />

            <Tooltip
              content={
                <ChartTooltip
                  valueKey="value"
                  valueFormatter={money}
                />
              }
              cursor={chartTheme.cursor}
            />

            <Bar
              dataKey="value"
              fill={chartTheme.colors.primarySoft}
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
    </Card>
  );
}

export default PositionAllocationChart;
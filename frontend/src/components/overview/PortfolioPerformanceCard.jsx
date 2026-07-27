import { useMemo, useState } from "react";
import SectionHeader from "../ui/SectionHeader";
import Card from "../ui/Card";
import SegmentedControl from "../ui/SegmentedControl";
import { chartTheme } from "../ui/charts/chartTheme";
import ChartTooltip from "../ui/charts/ChartTooltip";

import {
  ArrowDownRight,
  ArrowUpRight,
  CalendarDays,
  Minus,
  TrendingUp,
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

const PERIODS = ["1D", "1W", "1M", "YTD"];
function formatCurrency(value) {
  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return numericValue.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

const FALLBACK_DATA = {
  "1D": [
    { label: "09:30", value: 245100 },
    { label: "10:30", value: 245980 },
    { label: "11:30", value: 246420 },
    { label: "12:30", value: 246050 },
    { label: "13:30", value: 247180 },
    { label: "14:30", value: 247940 },
    { label: "15:30", value: 248430 },
  ],

  "1W": [
    { label: "Mon", value: 239800 },
    { label: "Tue", value: 241650 },
    { label: "Wed", value: 240920 },
    { label: "Thu", value: 244780 },
    { label: "Fri", value: 248430 },
  ],

  "1M": [
    { label: "W1", value: 231400 },
    { label: "W2", value: 235900 },
    { label: "W3", value: 242100 },
    { label: "W4", value: 248430 },
  ],

  YTD: [
    { label: "Jan", value: 210000 },
    { label: "Feb", value: 216700 },
    { label: "Mar", value: 222900 },
    { label: "Apr", value: 228300 },
    { label: "May", value: 237600 },
    { label: "Jun", value: 248430 },
  ],
};

function PortfolioPerformanceCard({
  performanceData,
}) {
  const [period, setPeriod] = useState("YTD");

  const data = useMemo(() => {
    const selectedData =
      performanceData?.[period];

    if (
      Array.isArray(selectedData) &&
      selectedData.length > 0
    ) {
      return selectedData;
    }

    return FALLBACK_DATA[period];
  }, [performanceData, period]);

  const metrics = useMemo(() => {
    const firstValue = Number(data.at(0)?.value);
    const lastValue = Number(data.at(-1)?.value);

    if (
      data.length < 2 ||
      Number.isNaN(firstValue) ||
      Number.isNaN(lastValue)
    ) {
      return {
        currentValue: "--",
        absoluteChange: 0,
        percentageChange: 0,
      };
    }

    const absoluteChange =
      lastValue - firstValue;

    const percentageChange =
      firstValue !== 0
        ? (absoluteChange / Math.abs(firstValue)) *
          100
        : 0;

    return {
      currentValue: lastValue,
      absoluteChange,
      percentageChange,
    };
  }, [data]);

  const tone =
    metrics.absoluteChange > 0
      ? "positive"
      : metrics.absoluteChange < 0
        ? "negative"
        : "neutral";

  const ChangeIcon =
    metrics.absoluteChange > 0
      ? ArrowUpRight
      : metrics.absoluteChange < 0
        ? ArrowDownRight
        : Minus;

  const currentValue =
    metrics.currentValue === "--"
      ? "--"
      : Number(
          metrics.currentValue
        ).toLocaleString("en-US", {
          style: "currency",
          currency: "USD",
          maximumFractionDigits: 0,
        });

  const absoluteChange =
    Number(
      metrics.absoluteChange
    ).toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 0,
      signDisplay: "always",
    });

  return (
    <Card
      surface
      variant="hero"
      padding="none"
      hover={false}
      className="portfolio-performance-card"
    >
      <SectionHeader
        eyebrow="PORTFOLIO PERFORMANCE"
        title="Performance Analysis"
        subtitle="Portfolio value evolution across the selected period"
        className="overview-section-heading"
        actions={
          <SegmentedControl
            options={PERIODS}
            value={period}
            onChange={setPeriod}
            size="compact"
            ariaLabel="Portfolio performance period"
          />
        }
      />

      <div className="performance-summary">
        <div className="performance-current-value">
          <span>Current portfolio value</span>

          <strong>{currentValue}</strong>

          <small>
            <CalendarDays size={13} />
            Selected period: {period}
          </small>
        </div>

        <div
          className={`performance-change ${tone}`}
        >
          <ChangeIcon size={19} />

          <div>
            <strong>
              {metrics.percentageChange > 0
                ? "+"
                : ""}
              {metrics.percentageChange.toFixed(2)}
              %
            </strong>

            <span>{absoluteChange}</span>
          </div>
        </div>
      </div>

      <div className="performance-chart">
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart
            key={period}
            data={data}
            margin={{
              top: 20,
              right: 12,
              left: -10,
              bottom: 0,
            }}
          >
            <defs>
              <linearGradient
                id="portfolioPerformanceGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopColor={chartTheme.colors.primary}
                  stopOpacity={0.18}
                />

                <stop
                  offset="55%"
                  stopColor={chartTheme.colors.primarySoft}
                  stopOpacity={0.06}
                />

                <stop
                  offset="100%"
                  stopColor={chartTheme.colors.primarySoft}
                  stopOpacity={0}

                />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke={chartTheme.colors.grid}
              strokeDasharray={chartTheme.grid.strokeDasharray}
              vertical={false}
            />

            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              stroke={chartTheme.colors.axis}
              tick={{
                fontSize: chartTheme.typography.xAxisFontSize,
                fontFamily: chartTheme.typography.axisFontFamily,
                fill: chartTheme.colors.axisText,
              }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              stroke={chartTheme.colors.axis}
              tick={{
                fontSize: chartTheme.typography.yAxisFontSize,
                fill: chartTheme.colors.axisText,
              }}
              width={68}
              tickMargin={8}
              domain={[
                "dataMin - 5000",
                "dataMax + 5000",
              ]}
              tickFormatter={(value) =>
                `$${Math.round(value / 1000)}k`
              }
            />

            <Tooltip
               content={
                <ChartTooltip
                  valueKey="value"
                  valueFormatter={formatCurrency}
              />
            }
            cursor={chartTheme.cursor}
          />

            <Area
              type="monotone"
              dataKey="value"
              stroke={chartTheme.colors.primary}
              strokeWidth={chartTheme.area.strokeWidth}
              fill="url(#portfolioPerformanceGradient)"
              activeDot={{
                r: chartTheme.area.activeDotRadius,
                strokeWidth: chartTheme.area.activeDotStrokeWidth,
                stroke: chartTheme.colors.activeDotStroke,
                fill: chartTheme.colors.primaryLight,
              }}
              animationDuration={chartTheme.animation.duration}
              animationEasing={chartTheme.animation.easing}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="performance-footer">
        <div>
          <TrendingUp size={15} />
          <span>Performance state</span>

          <strong className={tone}>
            {tone === "positive"
              ? "Outperforming"
              : tone === "negative"
                ? "Under pressure"
                : "Stable"}
          </strong>
        </div>

        <div>
          <span>Period return</span>

          <strong className={tone}>
            {metrics.percentageChange > 0
              ? "+"
              : ""}
            {metrics.percentageChange.toFixed(2)}%
          </strong>
        </div>
      </div>
    </Card>
  );
}

export default PortfolioPerformanceCard;
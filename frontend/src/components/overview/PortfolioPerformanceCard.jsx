import { useMemo, useState } from "react";

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

function PerformanceTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  const value = Number(payload[0]?.value);

  return (
    <div className="performance-tooltip">
      <span>{label}</span>

      <strong>
        {Number.isNaN(value)
          ? "--"
          : value.toLocaleString("en-US", {
              style: "currency",
              currency: "USD",
              maximumFractionDigits: 0,
            })}
      </strong>
    </div>
  );
}

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
    <section className="overview-surface portfolio-performance-card">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            PORTFOLIO PERFORMANCE
          </span>

          <h2>Performance Analysis</h2>

          <p>
            Portfolio value evolution across the
            selected period
          </p>
        </div>

        <div className="performance-period-selector">
          {PERIODS.map((item) => (
            <button
              key={item}
              type="button"
              className={
                period === item ? "active" : ""
              }
              onClick={() => setPeriod(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

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
        <ResponsiveContainer width="100%" height={280}>
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
                  stopColor="#648fff"
                  stopOpacity={0.4}
                />

                <stop
                  offset="100%"
                  stopColor="#648fff"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="#202b3a"
              strokeDasharray="3 6"
              vertical={false}
            />

            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              stroke="#68768a"
              tick={{
                fontSize: 11,
              }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              stroke="#68768a"
              tick={{
                fontSize: 11,
              }}
              width={70}
              domain={[
                "dataMin - 5000",
                "dataMax + 5000",
              ]}
              tickFormatter={(value) =>
                `$${Math.round(value / 1000)}k`
              }
            />

            <Tooltip
              content={<PerformanceTooltip />}
              cursor={{
                stroke: "#648fff",
                strokeWidth: 1,
                strokeDasharray: "4 4",
              }}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke="#648fff"
              strokeWidth={2.7}
              fill="url(#portfolioPerformanceGradient)"
              activeDot={{
                r: 5,
                strokeWidth: 3,
                stroke: "#111923",
                fill: "#8caaff",
              }}
              animationDuration={650}
              animationEasing="ease-out"
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
    </section>
  );
}

export default PortfolioPerformanceCard;
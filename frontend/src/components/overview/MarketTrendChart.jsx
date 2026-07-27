import { useMemo, useState } from "react";

import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  ChartNoAxesCombined,
  Minus,
  ShieldCheck,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceDot,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function TrendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  const value = Number(payload[0]?.value);

  return (
    <div className="trend-tooltip">
      <span className="trend-tooltip-label">
        {label}
      </span>

      <strong className="trend-tooltip-value">
        {Number.isNaN(value) ? "--" : value.toFixed(1)}
      </strong>

      <span className="trend-tooltip-caption">
        Intelligence score
      </span>
    </div>
  );
}

function MarketTrendChart({ trend = [] }) {
  const [period, setPeriod] = useState("6M");

  const filteredTrend = useMemo(() => {
    const periodPoints = {
      "1M": 2,
      "3M": 3,
      "6M": 6,
      "1Y": 12,
    };

    const pointsToShow =
      periodPoints[period] ?? trend.length;

    return trend.slice(-pointsToShow);
  }, [period, trend]);

  const trendMetrics = useMemo(() => {
    const firstValue = Number(
      filteredTrend.at(0)?.value
    );

    const lastValue = Number(
      filteredTrend.at(-1)?.value
    );

    if (
      filteredTrend.length < 2 ||
      Number.isNaN(firstValue) ||
      Number.isNaN(lastValue)
    ) {
      return {
        momentum: "Neutral",
        riskState: "Unavailable",
        score: "--",
        change: 0,
        percentageChange: 0,
      };
    }

    const change = lastValue - firstValue;

    const percentageChange =
      firstValue !== 0
        ? (change / Math.abs(firstValue)) * 100
        : 0;

    const absoluteChange = Math.abs(change);

    let momentum = "Neutral";

    if (change > 2) {
      momentum = "Positive";
    } else if (change < -2) {
      momentum = "Negative";
    }

    let riskState = "Controlled";

    if (absoluteChange >= 15) {
      riskState = "Elevated";
    } else if (absoluteChange >= 8) {
      riskState = "Moderate";
    }

    return {
      momentum,
      riskState,
      score: lastValue,
      change,
      percentageChange,
    };
  }, [filteredTrend]);

  const latestPoint = filteredTrend.at(-1);

  const momentumTone =
    trendMetrics.momentum.toLowerCase();

  const riskTone =
    trendMetrics.riskState.toLowerCase();

  const changeTone =
    trendMetrics.change > 0
      ? "positive"
      : trendMetrics.change < 0
        ? "negative"
        : "neutral";

  const ChangeIcon =
    trendMetrics.change > 0
      ? ArrowUpRight
      : trendMetrics.change < 0
        ? ArrowDownRight
        : Minus;

  return (
    <section className="overview-surface trend-surface">
      <div className="overview-section-heading trend-heading">
        <div>
          <span className="section-kicker">
            ANALYTICAL SIGNAL
          </span>

          <h2>Market Intelligence Trend</h2>

          <p>
            Composite foundation signal over the
            selected period
          </p>
        </div>

        <div className="chart-period-selector">
          {["1M", "3M", "6M", "1Y"].map(
            (item) => (
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
            )
          )}
        </div>
      </div>

      <div className="trend-summary">
        <div className="trend-current-value">
          <span>Current score</span>

          <strong>
            {trendMetrics.score === "--"
              ? "--"
              : Number(
                  trendMetrics.score
                ).toFixed(1)}
          </strong>
        </div>

        <div
          className={`trend-change-indicator ${changeTone}`}
        >
          <ChangeIcon size={17} />

          <div>
            <strong>
              {trendMetrics.change > 0 ? "+" : ""}
              {trendMetrics.change.toFixed(1)} pts
            </strong>

            <span>
              {trendMetrics.percentageChange > 0
                ? "+"
                : ""}
              {trendMetrics.percentageChange.toFixed(
                1
              )}
              %
            </span>
          </div>
        </div>
      </div>

      <div className="trend-chart">
        <ResponsiveContainer width="100%" height={310}>
          <AreaChart
            key={period}
            data={filteredTrend}
            margin={{
              top: 24,
              right: 18,
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
                  stopColor="#7b9eff"
                  stopOpacity={0.16}
                />

                <stop
                  offset="60%"
                  stopColor="#648fff"
                  stopOpacity={0.05}
                />

                <stop
                  offset="100%"
                  stopColor="#648fff"
                  stopOpacity={0}
                />
              </linearGradient>

              <filter
                id="qmiTrendGlow"
                x="-50%"
                y="-50%"
                width="200%"
                height="200%"
              >
                <feGaussianBlur
                  stdDeviation="1.35"
                  result="blur"
                />

                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <CartesianGrid
              stroke="rgba(125,145,170,.10)"
              strokeDasharray="2 7"
              vertical={false}
            />

            <XAxis
              dataKey="month"
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{
                fontSize: 10,
                fontFamily: "JetBrains Mono",
                fill: "#657286",
              }}
              tickMargin={12}
              minTickGap={20}
            />

            <YAxis
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{
                fontSize: 10,
                fontFamily: "JetBrains Mono",
                fill: "#657286",
              }}
              domain={["dataMin - 5", "dataMax + 5"]}
            />

            <Tooltip
              content={<TrendTooltip />}
              cursor={{
                stroke: "rgba(118,153,255,.45)",
                strokeWidth: 1,
                strokeDasharray: "2 5",
              }}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke="#648fff"
              strokeWidth={1.9}
              fill="url(#qmiTrendGradient)"
              filter="url(#qmiTrendGlow)"
              activeDot={{
                r: 4,
                strokeWidth: 2,
                stroke: "#0d141d",
                fill: "#90adff",
              }}
              isAnimationActive
              animationDuration={650}
              animationEasing="ease-out"
            />

            {latestPoint && (
              <ReferenceDot
                x={latestPoint.month}
                y={latestPoint.value}
                r={4}
                fill="#90adff"
                stroke="#0d141d"
                strokeWidth={2}
                isFront
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="trend-footer">
        <div>
          <Activity size={15} />

          <span>Signal momentum</span>

          <strong
            className={`trend-status ${momentumTone}`}
          >
            {trendMetrics.momentum}
          </strong>
        </div>

        <div>
          <ShieldCheck size={15} />

          <span>Risk state</span>

          <strong
            className={`trend-status ${riskTone}`}
          >
            {trendMetrics.riskState}
          </strong>
        </div>

        <div>
          <ChartNoAxesCombined size={15} />

          <span>Selected period</span>

          <strong>{period}</strong>
        </div>
      </div>
    </section>
  );
}

export default MarketTrendChart;
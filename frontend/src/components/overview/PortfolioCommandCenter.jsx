import { useMemo, useState } from "react";

import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BrainCircuit,
  BriefcaseBusiness,
  Gauge,
  Minus,
  ShieldCheck,
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

function money(value) {
  const number = Number(value);

  if (Number.isNaN(number)) {
    return "--";
  }

  return number.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  });
}

function number(value, decimals = 2) {
  const parsedValue = Number(value);

  if (Number.isNaN(parsedValue)) {
    return "--";
  }

  return parsedValue.toFixed(decimals);
}

function CommandTooltip({ active, payload, label }) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div className="command-tooltip">
      <span>{label}</span>

      <strong>{money(payload[0]?.value)}</strong>
    </div>
  );
}

function CommandMetric({
  icon: Icon,
  label,
  value,
  tone = "neutral",
}) {
  return (
    <div className="command-metric">
      <Icon size={14} />

      <div>
        <span>{label}</span>
        <strong className={tone}>{value}</strong>
      </div>
    </div>
  );
}

export default function PortfolioCommandCenter({
  portfolio,
  ai,
  performanceData,
}) {
  const [period, setPeriod] = useState("YTD");

  const safePortfolio = portfolio ?? {};
  const safeAi = ai ?? {};

  const data = useMemo(() => {
    const selectedData = performanceData?.[period];

    if (
      Array.isArray(selectedData) &&
      selectedData.length > 0
    ) {
      return selectedData;
    }

    return FALLBACK_DATA[period];
  }, [performanceData, period]);

  const performance = useMemo(() => {
    const firstValue = Number(data.at(0)?.value);
    const lastValue = Number(data.at(-1)?.value);

    if (
      data.length < 2 ||
      Number.isNaN(firstValue) ||
      Number.isNaN(lastValue)
    ) {
      return {
        value: "--",
        change: 0,
        percentage: 0,
      };
    }

    const change = lastValue - firstValue;

    const percentage =
      firstValue !== 0
        ? (change / Math.abs(firstValue)) * 100
        : 0;

    return {
      value: lastValue,
      change,
      percentage,
    };
  }, [data]);

  const riskScore = Math.min(
    100,
    Math.max(
      0,
      Number(safePortfolio.risk_score ?? 73)
    )
  );

  const sharpeRatio = Number(
    safePortfolio.sharpe_ratio ?? 1.81
  );

  const beta = Number(
    safePortfolio.beta ?? 0.92
  );

  const volatility = Number(
    safePortfolio.volatility ?? 17.4
  );

  const positionCount = Number(
    safePortfolio.position_count ?? 0
  );

  const aiConfidence = Math.min(
    100,
    Math.max(
      0,
      Number(
        safeAi.confidence ??
          safePortfolio.ai_confidence ??
          84
      )
    )
  );

  const aiOutlook =
    safeAi.outlook ??
    safePortfolio.ai_outlook ??
    "Bullish";

  const aiSummary =
    safeAi.summary ??
    safePortfolio.ai_summary ??
    "Portfolio conditions remain constructive. Momentum, diversification and risk remain inside the current operating range.";

  const performanceTone =
    performance.change > 0
      ? "positive"
      : performance.change < 0
        ? "negative"
        : "neutral";

  const riskTone =
    riskScore >= 80
      ? "negative"
      : riskScore >= 60
        ? "warning"
        : "positive";

  const volatilityTone =
    volatility >= 30
      ? "negative"
      : volatility >= 20
        ? "warning"
        : "positive";

  const outlookTone =
    aiOutlook.toLowerCase().includes("bull")
      ? "positive"
      : aiOutlook.toLowerCase().includes("bear")
        ? "negative"
        : "warning";

  const ChangeIcon =
    performance.change > 0
      ? ArrowUpRight
      : performance.change < 0
        ? ArrowDownRight
        : Minus;

  return (
    <section className="portfolio-command-center">
      <header className="command-center-header">
        <div>
          <span className="command-center-kicker">
            QMI PORTFOLIO COMMAND CENTER
          </span>

          <h2>Executive Portfolio Intelligence</h2>

          <p>
            Performance, exposure, risk and AI intelligence
            within one institutional operating surface.
          </p>
        </div>

        <div className="command-period-selector">
          {PERIODS.map((item) => (
            <button
              key={item}
              type="button"
              className={period === item ? "active" : ""}
              onClick={() => setPeriod(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </header>

      <div className="command-center-summary">
        <div className="command-primary-value">
          <span>Current portfolio value</span>

          <strong>
            {performance.value === "--"
              ? "--"
              : money(performance.value)}
          </strong>
        </div>

        <div
          className={`command-performance-change ${performanceTone}`}
        >
          <ChangeIcon size={18} />

          <div>
            <strong>
              {performance.percentage > 0 ? "+" : ""}
              {performance.percentage.toFixed(2)}%
            </strong>

            <span>
              {money(Math.abs(performance.change))}
              {" "}
              {performance.change >= 0
                ? "gain"
                : "loss"}
            </span>
          </div>
        </div>

        <div className={`command-risk-value ${riskTone}`}>
          <span>Risk score</span>
          <strong>{riskScore}</strong>
          <small>/100</small>
        </div>

        <div className="command-ai-value">
          <BrainCircuit size={16} />

          <div>
            <span>AI outlook</span>

            <strong className={outlookTone}>
              {aiOutlook}
            </strong>
          </div>

          <small>{aiConfidence}%</small>
        </div>
      </div>

      <div className="command-center-main">
        <div className="command-chart-region">
          <ResponsiveContainer width="100%" height={330}>
            <AreaChart
              key={period}
              data={data}
              margin={{
                top: 18,
                right: 12,
                left: -8,
                bottom: 0,
              }}
            >
              <defs>
                <linearGradient
                  id="commandCenterGradient"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="#7699ff"
                    stopOpacity={0.18}
                  />

                  <stop
                    offset="58%"
                    stopColor="#648fff"
                    stopOpacity={0.05}
                  />

                  <stop
                    offset="100%"
                    stopColor="#648fff"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid
                stroke="rgba(125, 145, 170, 0.10)"
                strokeDasharray="2 7"
                vertical={false}
              />

              <XAxis
                dataKey="label"
                axisLine={false}
                tickLine={false}
                tickMargin={12}
                tick={{
                  fontSize: 10,
                  fontFamily: "JetBrains Mono",
                  fill: "#657286",
                }}
              />

              <YAxis
                axisLine={false}
                tickLine={false}
                width={68}
                tickMargin={8}
                domain={[
                  "dataMin - 5000",
                  "dataMax + 5000",
                ]}
                tick={{
                  fontSize: 10,
                  fontFamily: "JetBrains Mono",
                  fill: "#657286",
                }}
                tickFormatter={(value) =>
                  `$${Math.round(value / 1000)}k`
                }
              />

              <Tooltip
                content={<CommandTooltip />}
                cursor={{
                  stroke: "rgba(118, 153, 255, 0.5)",
                  strokeWidth: 1,
                  strokeDasharray: "2 5",
                }}
              />

              <Area
                type="monotone"
                dataKey="value"
                stroke="#7699ff"
                strokeWidth={1.9}
                fill="url(#commandCenterGradient)"
                activeDot={{
                  r: 4,
                  strokeWidth: 2,
                  stroke: "#0d141e",
                  fill: "#9ab3ff",
                }}
                animationDuration={500}
                animationEasing="ease-out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <aside className="command-intelligence-region">
          <div className="command-intelligence-heading">
            <div>
              <span>AI portfolio assessment</span>

              <strong className={outlookTone}>
                {aiOutlook}
              </strong>
            </div>

            <ShieldCheck size={17} />
          </div>

          <p>{aiSummary}</p>

          <div className="command-confidence">
            <div>
              <span>Model confidence</span>
              <strong>{aiConfidence}%</strong>
            </div>

            <div className="command-confidence-track">
              <span
                style={{
                  width: `${aiConfidence}%`,
                }}
              />
            </div>
          </div>

          <div className="command-risk-classification">
            <span>Risk classification</span>

            <strong className={riskTone}>
              {riskScore >= 80
                ? "Elevated"
                : riskScore >= 60
                  ? "Moderate"
                  : "Controlled"}
            </strong>
          </div>
        </aside>
      </div>

      <footer className="command-metrics-strip">
        <CommandMetric
          icon={TrendingUp}
          label="Sharpe ratio"
          value={number(sharpeRatio)}
          tone={
            sharpeRatio >= 1
              ? "positive"
              : "warning"
          }
        />

        <CommandMetric
          icon={Gauge}
          label="Portfolio beta"
          value={number(beta)}
        />

        <CommandMetric
          icon={Activity}
          label="Volatility"
          value={`${number(volatility, 1)}%`}
          tone={volatilityTone}
        />

        <CommandMetric
          icon={BriefcaseBusiness}
          label="Positions"
          value={positionCount}
        />

        <CommandMetric
          icon={ShieldCheck}
          label="Risk governance"
          value="Operational"
          tone="positive"
        />
      </footer>
    </section>
  );
}
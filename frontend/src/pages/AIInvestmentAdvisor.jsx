import "../styles/advisor.css";

import AdvisorHero from "../components/advisor/AdvisorHero";
import RecommendationCard from "../components/advisor/RecommendationCard";

import {
  Activity,
  BriefcaseBusiness,
  CalendarDays,
  ChartNoAxesCombined,
  CircleGauge,
  CircleHelp,
  Gauge,
  LineChart,
  Radar,
  ShieldAlert,
  Target,
  TrendingDown,
  TrendingUp
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

const sentimentTrend = [
  { month: "Dec", price: 5.1, sentiment: 48, confidence: 58 },
  { month: "Jan", price: 6.2, sentiment: 55, confidence: 63 },
  { month: "Feb", price: 8.4, sentiment: 69, confidence: 71 },
  { month: "Mar", price: 5.9, sentiment: 58, confidence: 69 },
  { month: "Apr", price: 4.6, sentiment: 47, confidence: 67 },
  { month: "May", price: 5.1, sentiment: 56, confidence: 70 },
  { month: "Jun", price: 5.8, sentiment: 64, confidence: 74 }
];

const recommendationFactors = [
  {
    factor: "Fundamentals",
    impact: 22,
    description: "Balance sheet resilience and improving margin outlook."
  },
  {
    factor: "Event Intelligence",
    impact: 18,
    description: "Product launches, expansion and operational catalysts."
  },
  {
    factor: "Forecast AI",
    impact: 16,
    description: "Positive 30-day model projection with elevated confidence."
  },
  {
    factor: "Explainable AI",
    impact: 12,
    description: "Composite model signal supports the current recommendation."
  },
  {
    factor: "Technical Trend",
    impact: 6,
    description: "Momentum improving near relevant support levels."
  },
  {
    factor: "News Sentiment",
    impact: 4,
    description: "Media and social sentiment remain constructive."
  },
  {
    factor: "Macro Risk",
    impact: -8,
    description: "Rates and geopolitical uncertainty remain headwinds."
  },
  {
    factor: "Valuation",
    impact: -6,
    description: "Relative valuation remains above the sector median."
  }
];

function ScoreRing({ value, label, tone = "positive" }) {
  return (
    <div className={`advisor-score-ring ${tone}`}>
      <div
        className="advisor-score-ring-visual"
        style={{
          "--score": `${value * 3.6}deg`
        }}
      >
        <div>
          <strong>{value}%</strong>
          <span>{label}</span>
        </div>
      </div>
    </div>
  );
}

function ScenarioCard({
  title,
  probability,
  target,
  returnRange,
  tone,
  icon
}) {
  return (
    <article className={`advisor-scenario-card ${tone}`}>
      <div className="advisor-scenario-header">
        <div>
          <span>{title}</span>
          <strong>{probability}%</strong>
        </div>

        {icon}
      </div>

      <div className="advisor-scenario-metric">
        <span>Target</span>
        <strong>{target}</strong>
      </div>

      <div className="advisor-scenario-metric">
        <span>Estimated return</span>
        <strong>{returnRange}</strong>
      </div>
    </article>
  );
}

function AIInvestmentAdvisor() {
  return (
    <div className="advisor-dashboard">
      <AdvisorHero />

      <section className="advisor-kpi-grid">
        <RecommendationCard
          recommendation="HOLD"
          bias="Slightly bullish"
          confidence="High"
          description="Maintaining the current position is presently the most balanced strategy."
        />

        <article className="advisor-card">
          <span className="advisor-card-label">
            Confidence score
          </span>

          <ScoreRing value={74} label="High" />
        </article>

        <article className="advisor-card">
          <span className="advisor-card-label">
            Risk level
          </span>

          <div className="advisor-risk-score">
            <strong>6 / 10</strong>
            <span>Moderate</span>
          </div>

          <div className="advisor-risk-scale">
            <span />
            <span />
            <span />
            <span />
            <span />
            <i />
          </div>
        </article>

        <article className="advisor-card">
          <span className="advisor-card-label">
            Historical success rate
          </span>

          <div className="advisor-large-metric positive">
            68%
          </div>

          <div className="advisor-mini-trend">
            <TrendingUp size={34} />
          </div>

          <small>312 comparable historical signals</small>
        </article>

        <article className="advisor-card">
          <span className="advisor-card-label">
            Recommended horizon
          </span>

          <div className="advisor-horizon-list">
            <div>
              <span>1–4 weeks</span>
              <strong>Neutral</strong>
            </div>
            <div>
              <span>1–3 months</span>
              <strong>Bullish</strong>
            </div>
            <div>
              <span>3–12 months</span>
              <strong>Strong bullish</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="advisor-main-grid">
        <article className="advisor-card advisor-chart-card">
          <div className="advisor-card-heading">
            <div>
              <span className="advisor-card-label">
                Price and sentiment evolution
              </span>
              <h3>Composite market trajectory</h3>
            </div>

            <button type="button">6M</button>
          </div>

          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={sentimentTrend}>
              <defs>
                <linearGradient
                  id="advisorPriceFill"
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                >
                  <stop
                    offset="0%"
                    stopColor="#4f8cff"
                    stopOpacity={0.28}
                  />
                  <stop
                    offset="100%"
                    stopColor="#4f8cff"
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="2 5"
                stroke="#243044"
                vertical={false}
              />

              <XAxis
                dataKey="month"
                stroke="#6d788b"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="#6d788b"
                tickLine={false}
                axisLine={false}
              />

              <Tooltip
                contentStyle={{
                  background: "#101722",
                  border: "1px solid #2b3b50",
                  borderRadius: "10px"
                }}
              />

              <Area
                type="monotone"
                dataKey="price"
                stroke="#4f8cff"
                fill="url(#advisorPriceFill)"
                strokeWidth={2}
              />

              <Line
                type="monotone"
                dataKey="sentiment"
                stroke="#54d17a"
                strokeWidth={2}
                dot={false}
              />

              <Line
                type="monotone"
                dataKey="confidence"
                stroke="#a56bff"
                strokeWidth={2}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>

          <div className="advisor-chart-legend">
            <span className="price">Price</span>
            <span className="sentiment">AI sentiment</span>
            <span className="confidence">Confidence</span>
          </div>
        </article>

        <article className="advisor-card advisor-factors-card">
          <div className="advisor-card-heading">
            <div>
              <span className="advisor-card-label">
                Explainable AI
              </span>
              <h3>Why this recommendation?</h3>
            </div>

            <CircleHelp size={18} />
          </div>

          <div className="advisor-factor-table">
            <div className="advisor-factor-table-head">
              <span>Factor</span>
              <span>Impact</span>
              <span>Explanation</span>
            </div>

            {recommendationFactors.map((item) => (
              <div
                className="advisor-factor-row"
                key={item.factor}
              >
                <strong>{item.factor}</strong>

                <span
                  className={
                    item.impact >= 0 ? "positive" : "negative"
                  }
                >
                  {item.impact >= 0 ? "+" : ""}
                  {item.impact}
                </span>

                <p>{item.description}</p>
              </div>
            ))}

            <div className="advisor-factor-total">
              <span>Total score</span>
              <strong>+64 / 100</strong>
            </div>
          </div>
        </article>
      </section>

      <section className="advisor-lower-grid">
        <article className="advisor-card">
          <div className="advisor-card-heading">
            <div>
              <span className="advisor-card-label">
                Projected scenarios
              </span>
              <h3>30-day outlook</h3>
            </div>

            <Target size={18} />
          </div>

          <div className="advisor-scenario-grid">
            <ScenarioCard
              title="Bullish"
              probability={30}
              target="$5.85 – $6.30"
              returnRange="+12% to +21%"
              tone="bullish"
              icon={<TrendingUp size={22} />}
            />

            <ScenarioCard
              title="Base"
              probability={50}
              target="$4.95 – $5.45"
              returnRange="-1% to +5%"
              tone="base"
              icon={<LineChart size={22} />}
            />

            <ScenarioCard
              title="Bearish"
              probability={20}
              target="$4.20 – $4.60"
              returnRange="-17% to -8%"
              tone="bearish"
              icon={<TrendingDown size={22} />}
            />
          </div>
        </article>

        <article className="advisor-card">
          <div className="advisor-card-heading">
            <div>
              <span className="advisor-card-label">
                Conviction by horizon
              </span>
              <h3>Signal durability</h3>
            </div>

            <Gauge size={18} />
          </div>

          <div className="advisor-conviction-list">
            {[
              ["1–4 weeks", 60],
              ["1–3 months", 74],
              ["3–6 months", 78],
              ["6–12 months", 82]
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <div>
                  <i style={{ width: `${value}%` }} />
                </div>
                <strong>{value}%</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="advisor-card">
          <div className="advisor-card-heading">
            <div>
              <span className="advisor-card-label">
                Suggested position management
              </span>
              <h3>Portfolio action mix</h3>
            </div>

            <BriefcaseBusiness size={18} />
          </div>

          <div className="advisor-position-management">
            <ScoreRing value={72} label="Hold" tone="positive" />

            <div>
              <span>
                <i className="hold" />
                Hold
                <strong>72%</strong>
              </span>

              <span>
                <i className="add" />
                Add
                <strong>18%</strong>
              </span>

              <span>
                <i className="reduce" />
                Reduce
                <strong>10%</strong>
              </span>

              <span>
                <i className="sell" />
                Sell
                <strong>0%</strong>
              </span>
            </div>
          </div>
        </article>
      </section>

      <section className="advisor-position-strip">
        <div>
          <span>Current position</span>
          <strong>4,020 shares</strong>
          <small>$20,980.20</small>
        </div>

        <div>
          <span>Average price</span>
          <strong>$12.85</strong>
        </div>

        <div>
          <span>Current P/L</span>
          <strong className="negative">-$30,687.00</strong>
          <small className="negative">-59.38%</small>
        </div>

        <div>
          <span>Next evaluation</span>
          <strong>26/06/2026</strong>
          <small>Daily review</small>
        </div>

        <div>
          <span>Primary sources</span>
          <strong>Market + AI models</strong>
          <small>Multi-source intelligence</small>
        </div>
      </section>
    </div>
  );
}

export default AIInvestmentAdvisor;
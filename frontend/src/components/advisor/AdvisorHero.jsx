import {
  Brain,
  Sparkles
} from "lucide-react";

export default function AdvisorHero() {
  return (
    <section className="advisor-header">
      <div>
        <div className="advisor-eyebrow">
          <Brain size={16} />

          AI INVESTMENT ADVISOR

          <span>PRO</span>
        </div>

        <h2>
          Professional multi-factor recommendation engine
        </h2>

        <p>
          Consolidated analysis combining fundamentals,
          technicals, sentiment, forecasting, risk and
          portfolio context.
        </p>
      </div>

      <div className="advisor-header-status">
        <Sparkles size={17} />
        Explainable AI active
      </div>
    </section>
  );
}
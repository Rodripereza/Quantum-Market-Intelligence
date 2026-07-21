import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";

import {
  Brain,
  Sparkles,
} from "lucide-react";

export default function AdvisorHero() {
  return (
    <Card
      className="advisor-header"
      padding="large"
      as="section"
    >
      <SectionHeader
        eyebrow={
          <div className="advisor-eyebrow">
            <Brain size={16} />
            AI INVESTMENT ADVISOR
            <span>PRO</span>
          </div>
        }
        title="Professional multi-factor recommendation engine"
        subtitle="Consolidated analysis combining fundamentals, technicals, sentiment, forecasting, risk and portfolio context."
        actions={
          <div className="advisor-header-status">
            <Sparkles size={17} />
            Explainable AI active
          </div>
        }
      />
    </Card>
  );
}
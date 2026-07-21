import {
  Activity,
  ArrowUpRight
} from "lucide-react";

export default function RecommendationCard({
  recommendation = "HOLD",
  bias = "Slightly bullish",
  description = "Maintaining the current position is presently the most balanced strategy.",
  confidence = "High"
}) {
  const normalizedRecommendation =
    recommendation.toLowerCase();

  const tone =
    normalizedRecommendation === "buy"
      ? "positive"
      : normalizedRecommendation === "sell"
        ? "negative"
        : "neutral";

  return (
    <article
      className={`advisor-card advisor-recommendation-card recommendation-${tone}`}
    >
      <div className="recommendation-card-header">
        <span className="advisor-card-label">
          Global recommendation
        </span>

        <span className={`recommendation-status ${tone}`}>
          {confidence} conviction
        </span>
      </div>

      <div className="advisor-recommendation-value">
        <div>
          <strong>{recommendation}</strong>

          <div className={`recommendation-bias ${tone}`}>
            <span>{bias}</span>
            <ArrowUpRight size={14} />
          </div>
        </div>

        <div className="advisor-recommendation-icon">
          <Activity size={25} />
        </div>
      </div>

      <p>{description}</p>

      <div className="recommendation-card-footer">
        <div>
          <span>Signal state</span>
          <strong>Active</strong>
        </div>

        <div>
          <span>Model consensus</span>
          <strong>Balanced</strong>
        </div>

        <div>
          <span>Review cycle</span>
          <strong>Daily</strong>
        </div>
      </div>
    </article>
  );
}
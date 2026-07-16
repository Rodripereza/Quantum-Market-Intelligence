import Card from "./Card";
import "./MetricCard.css";

function MetricCard({
  label,
  value,
  change,
  changeLabel,
  icon,
  status = "neutral",
}) {
  const normalizedStatus = [
    "positive",
    "negative",
    "warning",
    "neutral",
  ].includes(status)
    ? status
    : "neutral";

  return (
    <Card
      className={`metric-card metric-card--${normalizedStatus}`}
      padding="compact"
    >
      <div className="metric-card__top">
        <span className="metric-card__label">{label}</span>

        {icon && (
          <span className="metric-card__icon" aria-hidden="true">
            {icon}
          </span>
        )}
      </div>

      <div className="metric-card__value">{value}</div>

      {(change || changeLabel) && (
        <div className="metric-card__footer">
          {change && (
            <span
              className={`metric-card__change metric-card__change--${normalizedStatus}`}
            >
              {change}
            </span>
          )}

          {changeLabel && (
            <span className="metric-card__change-label">
              {changeLabel}
            </span>
          )}
        </div>
      )}
    </Card>
  );
}

export default MetricCard;
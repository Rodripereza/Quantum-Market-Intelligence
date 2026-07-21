function HeroMiniMetric({
  label,
  value,
  detail,
  icon,
  tone = "neutral",
}) {
  const allowedTones = [
    "neutral",
    "primary",
    "positive",
    "warning",
  ];

  const normalizedTone = allowedTones.includes(tone)
    ? tone
    : "neutral";

  return (
    <article
      className={`hero-mini-metric hero-mini-metric--${normalizedTone}`}
    >
      <div className="hero-mini-metric__icon" aria-hidden="true">
        {icon}
      </div>

      <div className="hero-mini-metric__content">
        <span className="hero-mini-metric__label">
          {label}
        </span>

        <strong className="hero-mini-metric__value">
          {value}
        </strong>

        {detail && (
          <small className="hero-mini-metric__detail">
            {detail}
          </small>
        )}
      </div>
    </article>
  );
}

export default HeroMiniMetric;
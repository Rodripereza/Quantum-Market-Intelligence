function ExecutiveMetric({
  label,
  value,
  description,
  icon,
  tone = "neutral",
}) {
  return (
    <article className={`executive-metric ${tone}`}>
      <div className="executive-metric-top">
        <span>{label}</span>

        <div className="executive-metric-icon">
          {icon}
        </div>
      </div>

      <strong>{value}</strong>

      <small>{description}</small>
    </article>
  );
}

export default ExecutiveMetric;
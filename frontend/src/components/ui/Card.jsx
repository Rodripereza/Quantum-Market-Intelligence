import "./Card.css";

function Card({
  children,
  title,
  subtitle,
  actions,
  className = "",
  padding = "normal",
}) {
  const cardClassName = [
    "qmi-card",
    `qmi-card--padding-${padding}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <section className={cardClassName}>
      {(title || subtitle || actions) && (
        <header className="qmi-card__header">
          <div className="qmi-card__heading">
            {title && <h2 className="qmi-card__title">{title}</h2>}

            {subtitle && (
              <p className="qmi-card__subtitle">{subtitle}</p>
            )}
          </div>

          {actions && (
            <div className="qmi-card__actions">{actions}</div>
          )}
        </header>
      )}

      <div className="qmi-card__content">{children}</div>
    </section>
  );
}

export default Card;
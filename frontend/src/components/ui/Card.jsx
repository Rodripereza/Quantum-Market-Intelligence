import "./Card.css";

function joinClasses(...classes) {
  return classes.filter(Boolean).join(" ");
}

function Card({
  children,
  className = "",
  as: Component = "section",
  variant = "default",
  padding = "default",
  hover = true,
  loading = false,
  disabled = false,
  accent = "none",
  surface = false,
  ...rest
}) {
  return (
    <Component
      className={joinClasses(
        "qmi-card",
        surface && "overview-surface",
        `qmi-card--${variant}`,
        `qmi-card--padding-${padding}`,
        `qmi-card--accent-${accent}`,
        hover && !disabled && "qmi-card--hoverable",
        loading && "qmi-card--loading",
        disabled && "qmi-card--disabled",
        className
      )}
      aria-busy={loading || undefined}
      aria-disabled={disabled || undefined}
      {...rest}
    >
      {loading && (
        <div
          className="qmi-card__loading-overlay"
          aria-hidden="true"
        >
          <span className="qmi-card__loading-spinner" />
        </div>
      )}

      {children}
    </Component>
  );
}

function CardHeader({
  children,
  className = "",
  divided = false,
}) {
  return (
    <div
      className={joinClasses(
        "qmi-card__header",
        divided && "qmi-card__header--divided",
        className
      )}
    >
      {children}
    </div>
  );
}

function CardBody({
  children,
  className = "",
}) {
  return (
    <div
      className={joinClasses(
        "qmi-card__body",
        className
      )}
    >
      {children}
    </div>
  );
}

function CardFooter({
  children,
  className = "",
}) {
  return (
    <footer
      className={joinClasses(
        "qmi-card__footer",
        className
      )}
    >
      {children}
    </footer>
  );
}

export default Card;

export {
  CardHeader,
  CardBody,
  CardFooter,
};
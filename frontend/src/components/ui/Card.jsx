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
}) {
  return (
    <Component
      className={joinClasses(
        "qmi-card",
        `qmi-card--${variant}`,
        `qmi-card--padding-${padding}`,
        className
      )}
    >
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
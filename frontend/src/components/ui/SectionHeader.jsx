export default function SectionHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  className = "",
  as: Component = "header",
}) {
  const sectionHeaderClassName = [
    "qmi-section-header",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Component className={sectionHeaderClassName}>
      <div className="qmi-section-header__content">
        {eyebrow && (
          <span className="qmi-section-header__eyebrow">
            {eyebrow}
          </span>
        )}

        {title && (
          <h2 className="qmi-section-header__title">
            {title}
          </h2>
        )}

        {subtitle && (
          <p className="qmi-section-header__subtitle">
            {subtitle}
          </p>
        )}
      </div>

      {actions && (
        <div className="qmi-section-header__actions">
          {actions}
        </div>
      )}
    </Component>
  );
}
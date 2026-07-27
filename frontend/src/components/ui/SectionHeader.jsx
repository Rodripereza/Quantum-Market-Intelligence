import "./SectionHeader.css";

export default function SectionHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  className = "",
  size = "default",
  as: Component = "header",
}) {
  const normalizedSize = ["default", "compact"].includes(size)
    ? size
    : "default";

  const sectionHeaderClassName = [
    "qmi-section-header",
    `qmi-section-header--${normalizedSize}`,
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
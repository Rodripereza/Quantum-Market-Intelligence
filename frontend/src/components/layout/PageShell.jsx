export default function PageShell({
  active,
  children
}) {
  return (
    <section
      className={`page-shell page-${active.id}`}
    >
      <header className="page-intro">
        <div className="page-intro-copy">
          <span className="page-intro-kicker">
            QMI MODULE
          </span>

          <h2>{active.label}</h2>

          <p>
            {active.description}
          </p>
        </div>

        <div className="page-intro-meta">
          <span className="version-badge">
            Foundation v1.3
          </span>

          <span className="page-intro-status">
            Operational
          </span>
        </div>
      </header>

      <div className="page-content">
        {children}
      </div>
    </section>
  );
}
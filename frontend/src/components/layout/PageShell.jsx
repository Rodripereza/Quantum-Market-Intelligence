export default function PageShell({ active, children }) {
  return (
    <section className={`page-shell page-${active.id}`}>
      <div className="page-intro">
        <div>
          <h2>{active.description}</h2>
          <p>
            Portfolio Engine v1.3 active. Positions, allocation, P/L and sector
            exposure are persisted in SQLite.
          </p>
        </div>

        <div className="version-badge">
          Portfolio v1.3
        </div>
      </div>

      {children}
    </section>
  );
}
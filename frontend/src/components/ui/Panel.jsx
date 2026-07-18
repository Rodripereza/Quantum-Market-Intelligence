export default function Panel({
  title,
  subtitle,
  children,
  action,
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>

        {action}
      </div>

      {children}
    </section>
  );
}
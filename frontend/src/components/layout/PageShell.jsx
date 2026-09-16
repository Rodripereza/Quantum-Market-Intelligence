export default function PageShell({ active, children }) {
  return (
    <section
      className="page-shell page-shell-compact"
      data-qmi-page={active?.label || "QMI"}
    >
      {children}
    </section>
  );
}

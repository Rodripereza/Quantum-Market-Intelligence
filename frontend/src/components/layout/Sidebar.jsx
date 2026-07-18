import { ChevronRight, X } from "lucide-react";

export default function Sidebar({
  page,
  navigate,
  open,
  close,
  navSections,
}) {
  return (
    <>
      <aside className={`sidebar ${open ? "mobile-open" : ""}`}>
        <div className="brand-row">
          <div className="logo">QMI</div>

          <button
            className="icon-button mobile-only"
            onClick={close}
            type="button"
          >
            <X size={18} />
          </button>
        </div>

        <div className="workspace-card">
          <span>Workspace</span>
          <strong>Institutional Research</strong>
        </div>

        {navSections.map((section) => (
          <nav key={section.title} className="nav-section">
            <div className="nav-title">{section.title}</div>

            {section.items.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  className={page === item.id ? "active" : ""}
                  onClick={() => navigate(item.id)}
                  type="button"
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  <ChevronRight size={15} className="nav-arrow" />
                </button>
              );
            })}
          </nav>
        ))}
      </aside>

      {open && <div className="overlay" onClick={close} />}
    </>
  );
}
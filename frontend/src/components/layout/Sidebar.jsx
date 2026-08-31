import {
  ChevronRight,
  CircleDot,
  Command,
  X
} from "lucide-react";

export default function Sidebar({
  page,
  navigate,
  open,
  close,
  navSections,
  activeTicker = "NIO"
}) {
  return (
    <>
      <aside
        className={`sidebar ${open ? "mobile-open" : ""}`}
      >
        <div className="sidebar-header">
          <div className="brand-row">
            <div className="brand-mark">
              <div className="brand-symbol">
                <Command size={17} />
              </div>

              <div>
                <div className="logo">QMI</div>
                <span className="brand-subtitle">
                  Intelligence Terminal
                </span>
              </div>
            </div>

            <button
              className="icon-button mobile-only"
              onClick={close}
              type="button"
            >
              <X size={18} />
            </button>
          </div>

          <div className="workspace-card">
            <div className="workspace-card-top">
              <span>Private workspace</span>

              <div className="workspace-status">
                <CircleDot size={11} />
                Active
              </div>
            </div>

            <strong>Institutional Research</strong>

            <small>
              Quantum Market Intelligence
            </small>
          </div>
        </div>

        <div className="sidebar-navigation">
          {navSections.map((section) => (
            <nav
              key={section.title}
              className="nav-section"
              aria-label={section.title}
            >
              <div className="nav-title">
                {section.title}
              </div>

              <div className="nav-items">
                {section.items
                  .filter(
                    (item) =>
                      item.id !== "deliveries" ||
                      String(activeTicker).toUpperCase() === "NIO"
                  )
                  .map((item) => {
                  const Icon = item.icon;
                  const isActive = page === item.id;

                  return (
                    <button
                      key={item.id}
                      className={
                        isActive
                          ? "sidebar-nav-item active"
                          : "sidebar-nav-item"
                      }
                      onClick={() => navigate(item.id)}
                      type="button"
                    >
                      <span className="sidebar-nav-icon">
                        <Icon size={16} />
                      </span>

                      <span className="sidebar-nav-copy">
                        <strong>{item.label}</strong>
                        <small>{item.description}</small>
                      </span>

                      <ChevronRight
                        size={14}
                        className="nav-arrow"
                      />
                    </button>
                  );
                })}
              </div>
            </nav>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-footer-status">
            <span className="sidebar-footer-dot" />

            <div>
              <strong>Foundation v1.3</strong>
              <small>Architecture operational</small>
            </div>
          </div>
        </div>
      </aside>

      {open && (
        <div
          className="overlay"
          onClick={close}
          role="button"
          tabIndex={0}
          aria-label="Close navigation"
        />
      )}
    </>
  );
}


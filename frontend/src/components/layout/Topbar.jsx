import {
  Bell,
  ChevronRight,
  Command,
  Menu,
  Search,
  User,
} from "lucide-react";

export default function Topbar({
  active,
  apiOk,
  user,
  logout,
  openSidebar,
}) {
  return (
    <header className="topbar topbar-premium qmi-global-header">
      <div className="qmi-global-header__main">
        <div className="qmi-global-header__identity">
          <button
            className="qmi-global-header__menu mobile-only"
            onClick={openSidebar}
            type="button"
            aria-label="Open navigation"
          >
            <Menu size={18} />
          </button>

          <div className="qmi-global-header__brand">
            <span className="qmi-global-header__brand-icon">
              <Command size={14} />
            </span>
            <strong>QMI</strong>
          </div>

          <span className="qmi-global-header__divider" />

          <div className="qmi-global-header__page">
            <strong>{active?.label || "Overview"}</strong>
            <span>{active?.description || "Quantum Market Intelligence"}</span>
          </div>
        </div>

        <div className="qmi-global-header__actions">
          <button className="qmi-global-header__search" type="button">
            <Search size={14} />
            <span>Search tickers, modules...</span>
            <kbd>Ctrl K</kbd>
          </button>

          <div className={`qmi-global-header__api ${apiOk ? "online" : "offline"}`}>
            <span />
            <strong>{apiOk ? "API Online" : "API Offline"}</strong>
          </div>

          <button
            className="qmi-global-header__notification"
            type="button"
            aria-label="Notifications"
          >
            <Bell size={16} />
          </button>

          <div className="qmi-global-header__user">
            <div className="qmi-global-header__avatar">
              <User size={14} />
            </div>
            <div>
              <strong>{user?.name || "Rodri"}</strong>
              <span>{user?.role || "Founder / Investor"}</span>
            </div>
            <button
              className="qmi-global-header__logout"
              onClick={() => logout()}
              type="button"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="qmi-global-header__sub">
        <div className="qmi-global-header__breadcrumb">
          <span>QMI</span>
          <ChevronRight size={11} />
          <strong>{active?.label || "Overview"}</strong>
        </div>

        <div className="qmi-global-header__meta">
          <span className="qmi-global-header__operational">
            <i />
            OPERATIONAL
          </span>
          <span>Foundation v1.3</span>
        </div>
      </div>
    </header>
  );
}

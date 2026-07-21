import {
  Bell,
  ChevronRight,
  CircleDot,
  Command,
  Menu,
  Search,
  User
} from "lucide-react";

export default function Topbar({
  active,
  apiOk,
  user,
  logout,
  openSidebar
}) {
  return (
    <header className="topbar topbar-premium">
      <div className="title-block topbar-title-block">
        <button
          className="icon-button mobile-only"
          onClick={openSidebar}
          type="button"
          aria-label="Open navigation"
        >
          <Menu size={20} />
        </button>

        <div className="topbar-title-content">
          <div className="topbar-system-line">
            <span className="topbar-system-icon">
              <Command size={12} />
            </span>

            <span>
              QUANTUM MARKET INTELLIGENCE
            </span>

            <span className="topbar-system-separator">
              /
            </span>

            <span>FOUNDATION v1.3</span>
          </div>

          <div className="topbar-heading-row">
            <div>
              <h1>{active.label}</h1>

              <div className="breadcrumb">
                <span>QMI</span>
                <ChevronRight size={13} />
                <span>{active.label}</span>
              </div>
            </div>

            <div className="topbar-page-status">
              <CircleDot size={12} />
              Workspace active
            </div>
          </div>
        </div>
      </div>

      <div className="top-actions topbar-actions-premium">
        <button
          className="topbar-search"
          type="button"
        >
          <Search size={15} />

          <span>Search modules, tickers or commands</span>

          <kbd>Ctrl K</kbd>
        </button>

        <button
          className="topbar-icon-action"
          type="button"
          aria-label="Notifications"
        >
          <Bell size={17} />

          <span className="notification-dot" />
        </button>

        <div
          className={
            apiOk
              ? "topbar-api-status online"
              : "topbar-api-status offline"
          }
        >
          <span className="api-status-dot" />

          <div>
            <strong>
              {apiOk ? "API Online" : "API Offline"}
            </strong>

            <small>
              {apiOk
                ? "FastAPI operational"
                : "Backend unavailable"}
            </small>
          </div>
        </div>

        <div className="topbar-user-menu">
          <div className="topbar-user-avatar">
            <User size={15} />
          </div>

          <div className="topbar-user-copy">
            <strong>{user?.name || "Rodri"}</strong>

            <span>
              {user?.role || "Founder / Investor"}
            </span>
          </div>

          <button
            className="topbar-logout"
            onClick={() => logout()}
            type="button"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
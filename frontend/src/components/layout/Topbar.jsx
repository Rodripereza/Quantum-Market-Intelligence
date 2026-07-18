import {
  Bell,
  ChevronRight,
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
    <header className="topbar">
      <div className="title-block">
        <button
          className="icon-button mobile-only"
          onClick={openSidebar}
          type="button"
        >
          <Menu size={20} />
        </button>

        <div>
          <div className="eyebrow">
            QUANTUM MARKET INTELLIGENCE · FOUNDATION v1.3
          </div>

          <h1>{active.label}</h1>

          <div className="breadcrumb">
            <span>QMI</span>
            <ChevronRight size={14} />
            <span>{active.label}</span>
          </div>
        </div>
      </div>

      <div className="top-actions">
        <div className="search-pill">
          <Search size={16} />
          <span>Search modules</span>
        </div>

        <button className="icon-button" type="button">
          <Bell size={18} />
        </button>

        <span className={apiOk ? "ok" : "bad"}>
          {apiOk ? "API OK" : "API OFFLINE"}
        </span>

        <div className="user-card">
          <User size={18} />

          <div>
            <strong>{user?.name || "Rodri"}</strong>
            <span>
              {user?.email || user?.role || "Founder / Investor"}
            </span>
          </div>
        </div>

        <button
          className="logout-button"
          onClick={() => logout()}
          type="button"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
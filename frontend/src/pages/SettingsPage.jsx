import Panel from "../components/ui/Panel";

function SettingsPage({ apiOk, user }) {
  return (
    <Panel
      title="Settings"
      subtitle="Local environment"
    >
      <div className="metric-list">
        <div>
          <strong>Frontend</strong>
          <span>React + Vite</span>
        </div>

        <div>
          <strong>Backend</strong>
          <span>FastAPI + SQLite</span>
        </div>

        <div>
          <strong>Python target</strong>
          <span>3.12.x</span>
        </div>

        <div>
          <strong>API status</strong>
          <span>{apiOk ? "Online" : "Offline"}</span>
        </div>

        <div>
          <strong>User</strong>
          <span>{user?.name || "Rodri"}</span>
        </div>

        <div>
          <strong>Email</strong>
          <span>
            {user?.email || "rodripereza8@gmail.com"}
          </span>
        </div>

        <div>
          <strong>Workspace</strong>
          <span>
            {user?.workspace ||
              "Quantum Market Intelligence"}
          </span>
        </div>
      </div>
    </Panel>
  );
}

export default SettingsPage;
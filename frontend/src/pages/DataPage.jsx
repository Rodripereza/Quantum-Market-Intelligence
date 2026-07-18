import Panel from "../components/ui/Panel";

function DataPage({ portfolio, market }) {
  return (
    <Panel
      title="Data Layer"
      subtitle="SQLite operational foundation"
    >
      <div className="metric-list">
        <div>
          <strong>Database</strong>
          <span>backend/data/qmi_foundation.db</span>
        </div>

        <div>
          <strong>Portfolio records</strong>
          <span>{portfolio?.positions?.length ?? "--"}</span>
        </div>

        <div>
          <strong>Sector groups</strong>
          <span>{portfolio?.sector_allocation?.length ?? "--"}</span>
        </div>

        <div>
          <strong>Market assets</strong>
          <span>{market?.assets?.length ?? "--"}</span>
        </div>
      </div>
    </Panel>
  );
}

export default DataPage;
import MetricCard from "../components/ui/MetricCard";
import "./Dashboard.css";

function Dashboard() {
  return (
    <main className="dashboard">
      <section className="dashboard__header">
        <div>
          <span className="dashboard__eyebrow">
            QUANTUM MARKET INTELLIGENCE
          </span>

          <h1 className="dashboard__title">Dashboard Overview</h1>

          <p className="dashboard__description">
            Market intelligence, portfolio monitoring and AI-assisted analysis.
          </p>
        </div>

        <div className="dashboard__status">
          <span className="dashboard__status-dot" />
          Market Open
        </div>
      </section>

      <section className="dashboard__metrics">
        <MetricCard
          label="Portfolio Value"
          value="$128,450.72"
          change="+2.84%"
          changeLabel="Today"
          status="positive"
          icon="◈"
        />

        <MetricCard
          label="Daily P&L"
          value="+$3,542.18"
          change="+1.92%"
          changeLabel="vs. previous close"
          status="positive"
          icon="↗"
        />

        <MetricCard
          label="Risk Score"
          value="Moderate"
          change="64 / 100"
          changeLabel="Portfolio exposure"
          status="warning"
          icon="◇"
        />

        <MetricCard
          label="AI Confidence"
          value="82.4%"
          change="+4.6%"
          changeLabel="Last 24 hours"
          status="positive"
          icon="✦"
        />
      </section>
    </main>
  );
}

export default Dashboard;
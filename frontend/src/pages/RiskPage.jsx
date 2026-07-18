import { Gauge, PieChart, Shield } from "lucide-react";

import Card from "../components/ui/Card";
import Panel from "../components/ui/Panel";

function pct(number) {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return `${Number(number || 0).toFixed(2)}%`;
}

function RiskPage({ portfolio }) {
  const concentration = Math.max(
    ...(portfolio?.positions || []).map((position) => position.weight),
    0
  );

  return (
    <Panel
      title="Risk Layer"
      subtitle="Authenticated risk workspace"
    >
      <div className="grid3">
        <Card
          title="Max Position Weight"
          value={pct(concentration)}
          subtitle="Concentration signal"
          icon={<Gauge size={18} />}
        />

        <Card
          title="Open Positions"
          value={portfolio?.positions?.length ?? "--"}
          subtitle="Portfolio breadth"
          icon={<PieChart size={18} />}
        />

        <Card
          title="Risk Engine"
          value="Prepared"
          subtitle="Future scoring module"
          icon={<Shield size={18} />}
        />
      </div>
    </Panel>
  );
}

export default RiskPage;
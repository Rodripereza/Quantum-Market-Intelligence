import { Layers3 } from "lucide-react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import EmptyChartState from "./EmptyChartState";

function money(number, currency = "USD") {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(number);
}

function SectorExposureChart({ sectorAllocation = [] }) {
  const hasSectorAllocation = sectorAllocation.length > 0;

  return (
    <section className="overview-surface">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            RISK DISTRIBUTION
          </span>

          <h2>Sector Exposure</h2>

          <p>
            Capital concentration by economic sector
          </p>
        </div>
      </div>

      {hasSectorAllocation ? (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart
            data={sectorAllocation}
            layout="vertical"
            margin={{
              top: 12,
              right: 15,
              left: 15,
              bottom: 0,
            }}
          >
            <CartesianGrid
              strokeDasharray="2 5"
              stroke="#202b3a"
              horizontal={false}
            />

            <XAxis
              type="number"
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11 }}
            />

            <YAxis
              type="category"
              dataKey="sector"
              width={90}
              stroke="#68768a"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11 }}
            />

            <Tooltip
              formatter={(value) => money(value)}
              contentStyle={{
                background: "#101722",
                border: "1px solid #2b3b50",
                borderRadius: "10px",
              }}
            />

            <Bar
              dataKey="value"
              fill="#41c7a1"
              radius={[0, 5, 5, 0]}
              maxBarSize={24}
            />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <EmptyChartState
          icon={<Layers3 size={22} />}
          title="No sector exposure"
          description="Sector distribution will appear after portfolio positions are loaded."
        />
      )}
    </section>
  );
}

export default SectorExposureChart;
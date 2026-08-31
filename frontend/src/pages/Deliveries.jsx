import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { getNioDeliveries } from "../services/nioDeliveryService";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const QUARTERS = [
  { label: "Q1", months: [1, 2, 3] },
  { label: "Q2", months: [4, 5, 6] },
  { label: "Q3", months: [7, 8, 9] },
  { label: "Q4", months: [10, 11, 12] },
];

function n(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function fmt(value) {
  const number = n(value);
  return number === null ? "—" : Math.round(number).toLocaleString("en-US");
}

function pct(value, digits = 1) {
  const number = n(value);
  if (number === null) return "—";
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}%`;
}

function pretty(value) {
  if (!value) return "—";
  return String(value).replaceAll("_", " ");
}

function fmtCny(value, digits = 0) {
  const number = n(value);
  if (number === null) return "—";
  return `¥${number.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

function fmtCnyK(value, digits = 1) {
  const number = n(value);
  if (number === null) return "—";
  return `¥${(number / 1000).toFixed(digits)}K`;
}

function fmtCnyB(value, digits = 2) {
  const number = n(value);
  if (number === null) return "—";
  return `¥${(number / 1_000_000_000).toFixed(digits)}B`;
}

function aspTone(value) {
  const number = n(value);
  if (number === null) return "neutral";
  if (number > 1) return "positive";
  if (number < -1) return "negative";
  return "neutral";
}

function AspTrendChart({ rows }) {
  const values = (rows || [])
    .filter(
      (row) =>
        n(row?.reported_asp_rmb) !== null ||
        n(row?.forecast_asp_rmb) !== null ||
        n(row?.model_mix_asp_rmb) !== null
    )
    .slice(-8);

  if (values.length < 2) {
    return (
      <div className="qmi-asp-chart-empty">
        Insufficient ASP history.
      </div>
    );
  }

  const width = 1000;
  const height = 280;
  const padX = 36;
  const padY = 28;

  const effectiveValues = values
    .flatMap((row) => [
      n(row.reported_asp_rmb),
      n(row.forecast_asp_rmb),
      n(row.model_mix_asp_rmb),
    ])
    .filter((value) => value !== null);

  const min = Math.min(...effectiveValues) * 0.90;
  const max = Math.max(...effectiveValues) * 1.05;
  const range = Math.max(max - min, 1);

  const point = (value, index) => {
    const x =
      padX +
      (index / Math.max(values.length - 1, 1)) * (width - padX * 2);
    const y =
      height -
      padY -
      ((Number(value) - min) / range) * (height - padY * 2);
    return { x, y };
  };

  const reported = values
    .map((row, index) => {
      const value = n(row.reported_asp_rmb);
      if (value === null) return null;
      return { ...point(value, index), value, quarter: row.quarter };
    })
    .filter(Boolean);

  const forecast = values
    .map((row, index) => {
      const value = n(row.forecast_asp_rmb);
      if (value === null) return null;
      return { ...point(value, index), value, quarter: row.quarter };
    })
    .filter(Boolean);

  const mix = values
    .map((row, index) => {
      const value = n(row.model_mix_asp_rmb);
      if (value === null) return null;
      return { ...point(value, index), value, quarter: row.quarter };
    })
    .filter(Boolean);

  const polyline = (series) =>
    series.map((item) => `${item.x},${item.y}`).join(" ");

  return (
    <div className="qmi-asp-chart-wrap">
      <div className="qmi-asp-chart-legend">
        <span><i className="reported" /> Reported ASP</span>
        <span><i className="forecast" /> Forecast ASP</span>
        <span><i className="mix" /> Model-Mix ASP</span>
      </div>

      <svg
        className="qmi-asp-chart"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="Quarterly ASP trend"
      >
        {[0.2, 0.4, 0.6, 0.8].map((ratio) => (
          <line
            key={ratio}
            x1={padX}
            x2={width - padX}
            y1={padY + ratio * (height - padY * 2)}
            y2={padY + ratio * (height - padY * 2)}
            stroke="rgba(148,163,184,.09)"
            strokeWidth="1"
          />
        ))}

        {mix.length > 1 ? (
          <polyline
            points={polyline(mix)}
            fill="none"
            stroke="#64748b"
            strokeWidth="2"
            strokeDasharray="8 7"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ) : null}

        {reported.length > 1 ? (
          <polyline
            points={polyline(reported)}
            fill="none"
            stroke="#60a5fa"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ) : null}

        {forecast.length > 1 ? (
          <polyline
            points={polyline(forecast)}
            fill="none"
            stroke="#d946ef"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ) : null}

        {[...mix, ...reported, ...forecast].map((item, index) => (
          <circle
            key={`${item.quarter}-${item.value}-${index}`}
            cx={item.x}
            cy={item.y}
            r="3.3"
            fill="#f8fafc"
            stroke="rgba(15,23,42,.9)"
            strokeWidth="1.2"
          />
        ))}
      </svg>

      <div className="qmi-asp-chart-labels">
        {values.map((row) => (
          <span key={row.quarter}>{row.quarter}</span>
        ))}
      </div>
    </div>
  );
}

function quarterTotal(records, months, getter) {
  const values = months
    .map((month) => {
      const row = records.find((item) => item.month === month);
      return row ? getter(row) : null;
    })
    .filter((value) => n(value) !== null);

  if (!values.length) return null;
  return values.reduce((sum, value) => sum + Number(value), 0);
}

function yearTotal(records, getter) {
  const values = records
    .map(getter)
    .filter((value) => n(value) !== null);

  if (!values.length) return null;
  return values.reduce((sum, value) => sum + Number(value), 0);
}

function brandValue(row, brand) {
  if (!row?.brands) return null;
  const candidates = [
    brand,
    brand.toUpperCase(),
    brand.toLowerCase(),
  ];
  for (const key of candidates) {
    if (row.brands[key] !== undefined && row.brands[key] !== null) {
      return row.brands[key];
    }
  }
  return null;
}

function modelValue(row, model) {
  const payload = row?.models?.[model];
  if (payload === null || payload === undefined) return null;
  if (typeof payload === "number") return payload;
  return payload?.deliveries ?? null;
}

function HeatCell({ value, max }) {
  const number = n(value);
  if (number === null) {
    return <div className="qmi-delivery-heat-cell is-empty">—</div>;
  }

  const ratio = max > 0 ? Math.min(number / max, 1) : 0;
  const alpha = 0.10 + ratio * 0.72;

  return (
    <div
      className="qmi-delivery-heat-cell"
      style={{
        background: `rgba(45, 212, 191, ${alpha})`,
        borderColor: `rgba(94, 234, 212, ${0.16 + ratio * 0.45})`,
        color: ratio > 0.62 ? "#ecfeff" : "#cbd5e1",
      }}
      title={`${fmt(number)} deliveries`}
    >
      {fmt(number)}
    </div>
  );
}



function MonthlyYoYChart({ records, selectedYear }) {
  const current = records.filter(
    (row) => Number(row.year) === Number(selectedYear)
  );
  const previous = records.filter(
    (row) => Number(row.year) === Number(selectedYear) - 1
  );

  const values = Array.from({ length: 12 }, (_, index) => {
    const month = index + 1;
    const currentRow = current.find((row) => Number(row.month) === month);
    const previousRow = previous.find((row) => Number(row.month) === month);

    const currentTotal = n(currentRow?.total);
    const previousTotal = n(previousRow?.total);

    const yoy =
      currentTotal !== null && previousTotal !== null && previousTotal > 0
        ? ((currentTotal - previousTotal) / previousTotal) * 100
        : null;

    return {
      month,
      label: MONTHS[index],
      yoy,
      currentTotal,
      previousTotal,
    };
  });

  const available = values.filter((item) => Number.isFinite(item.yoy));

  if (!available.length) {
    return (
      <div className="qmi-delivery-chart-empty">
        No monthly YoY comparison available for {selectedYear}.
      </div>
    );
  }

  const maxAbs = Math.max(
    ...available.map((item) => Math.abs(item.yoy)),
    1
  );

  return (
    <div className="qmi-monthly-yoy-wrap">
      <div className="qmi-monthly-yoy-grid">
        {values.map((item) => {
          const availableValue = Number.isFinite(item.yoy);
          const positive = availableValue ? item.yoy >= 0 : true;
          const magnitude = availableValue
            ? Math.max(10, (Math.abs(item.yoy) / maxAbs) * 100)
            : 0;

          return (
            <div className="qmi-monthly-yoy-col" key={item.month}>
              <div className="qmi-monthly-yoy-value">
                {availableValue
                  ? `${item.yoy >= 0 ? "+" : ""}${item.yoy.toFixed(1)}%`
                  : "—"}
              </div>

              <div className="qmi-monthly-yoy-track">
                {availableValue ? (
                  <div
                    className={`qmi-monthly-yoy-bar ${
                      positive ? "is-positive" : "is-negative"
                    }`}
                    style={{ height: `${magnitude}%` }}
                    title={`${selectedYear} ${item.label}: ${fmt(
                      item.currentTotal
                    )} vs ${selectedYear - 1}: ${fmt(item.previousTotal)}`}
                  />
                ) : (
                  <div className="qmi-monthly-yoy-empty">—</div>
                )}
              </div>

              <div className="qmi-monthly-yoy-label">{item.label}</div>
            </div>
          );
        })}
      </div>

      <div className="qmi-monthly-yoy-scale">
        <span>Negative</span>
        <div className="qmi-monthly-yoy-scale-bar" />
        <span>Positive</span>
      </div>
    </div>
  );
}

function AnnualVariationChart({ records }) {
  const annual = [...new Set(
    records.map((row) => Number(row.year)).filter(Number.isFinite)
  )]
    .sort((a, b) => a - b)
    .map((year) => {
      const rows = records.filter((row) => Number(row.year) === year);
      const total = rows.reduce((sum, row) => sum + Number(row.total || 0), 0);
      return { year, total };
    })
    .filter((item) => item.total > 0);

  const values = annual.slice(1).map((item, index) => {
    const previous = annual[index];
    const yoy =
      previous?.total > 0
        ? ((item.total - previous.total) / previous.total) * 100
        : null;
    return { ...item, previousYear: previous?.year, yoy };
  }).filter((item) => Number.isFinite(item.yoy));

  if (!values.length) {
    return <div className="qmi-delivery-chart-empty">Insufficient annual history.</div>;
  }

  const maxAbs = Math.max(...values.map((item) => Math.abs(item.yoy)), 1);

  return (
    <div className="qmi-yoy-chart">
      <div className="qmi-yoy-zero-line" />
      {values.map((item) => {
        const positive = item.yoy >= 0;
        const magnitude = Math.max(12, (Math.abs(item.yoy) / maxAbs) * 100);
        return (
          <div className="qmi-yoy-column" key={item.year}>
            <div className="qmi-yoy-value">
              {item.yoy >= 0 ? "+" : ""}{item.yoy.toFixed(1)}%
            </div>
            <div className="qmi-yoy-track">
              <div
                className={`qmi-yoy-bar ${positive ? "is-positive" : "is-negative"}`}
                style={{ height: `${magnitude}%` }}
                title={`${item.previousYear} → ${item.year}: ${item.yoy.toFixed(1)}%`}
              />
            </div>
            <div className="qmi-yoy-year">{item.year}</div>
          </div>
        );
      })}
    </div>
  );
}

function TrendChart({ records }) {
  const values = records
    .filter((row) => n(row.total) !== null)
    .slice(-36);

  if (values.length < 2) {
    return <div className="qmi-delivery-chart-empty">Insufficient history.</div>;
  }

  const width = 1000;
  const height = 250;
  const padX = 26;
  const padY = 22;
  const max = Math.max(...values.map((row) => Number(row.total)), 1);
  const min = Math.min(...values.map((row) => Number(row.total)), 0);
  const range = Math.max(max - min, 1);

  const points = values.map((row, index) => {
    const x =
      padX +
      (index / Math.max(values.length - 1, 1)) * (width - padX * 2);
    const y =
      height -
      padY -
      ((Number(row.total) - min) / range) * (height - padY * 2);
    return { x, y, row };
  });

  const line = points.map((point) => `${point.x},${point.y}`).join(" ");
  const area =
    `${padX},${height - padY} ` +
    line +
    ` ${width - padX},${height - padY}`;

  return (
    <div className="qmi-delivery-chart-wrap">
      <svg
        className="qmi-delivery-chart"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        role="img"
        aria-label="NIO monthly deliveries trend"
      >
        {[0.25, 0.5, 0.75].map((ratio) => (
          <line
            key={ratio}
            x1={padX}
            x2={width - padX}
            y1={padY + ratio * (height - padY * 2)}
            y2={padY + ratio * (height - padY * 2)}
            stroke="rgba(148,163,184,.10)"
            strokeWidth="1"
          />
        ))}
        <polygon
          points={area}
          fill="rgba(139,92,246,.12)"
        />
        <polyline
          points={line}
          fill="none"
          stroke="#a78bfa"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {points.map((point, index) => (
          <circle
            key={`${point.row.period}-${index}`}
            cx={point.x}
            cy={point.y}
            r="3"
            fill="#c4b5fd"
          />
        ))}
      </svg>

      <div className="qmi-delivery-chart-labels">
        <span>{values[0]?.period}</span>
        <span>{values[Math.floor(values.length / 2)]?.period}</span>
        <span>{values[values.length - 1]?.period}</span>
      </div>
    </div>
  );
}

export default function Deliveries({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedYear, setSelectedYear] = useState(null);
  const [tab, setTab] = useState("deliveries");

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      setLoading(true);
      setError("");

      try {
        const result = await getNioDeliveries({
          token,
          signal: controller.signal,
        });
        setData(result);

        const years = (result?.monthly || [])
          .map((row) => Number(row.year))
          .filter(Number.isFinite);

        if (years.length) {
          setSelectedYear(Math.max(...years));
        }
      } catch (requestError) {
        if (requestError?.name !== "AbortError") {
          console.error("Unable to load NIO deliveries:", requestError);
          setError(
            requestError?.message || "Unable to load NIO Delivery Intelligence"
          );
          setData(null);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    load();
    return () => controller.abort();
  }, [token]);

  const monthly = useMemo(
    () =>
      Array.isArray(data?.monthly)
        ? [...data.monthly].sort(
            (a, b) => Number(a.year) - Number(b.year) || Number(a.month) - Number(b.month)
          )
        : [],
    [data]
  );

  const years = useMemo(
    () =>
      [...new Set(monthly.map((row) => Number(row.year)).filter(Number.isFinite))]
        .sort((a, b) => b - a),
    [monthly]
  );

  const selectedRecords = useMemo(
    () => monthly.filter((row) => Number(row.year) === Number(selectedYear)),
    [monthly, selectedYear]
  );

  const models = useMemo(() => {
    const set = new Set();
    selectedRecords.forEach((row) => {
      Object.keys(row.models || {}).forEach((model) => set.add(model));
    });

    const preferredOrder = [
      "ES8", "ES9", "ES7", "ES6",
      "EC7", "EC6",
      "ET9", "ET7", "ET5", "ET5 Touring", "ET5T",
      "L90", "L80", "L60",
      "Firefly", "FIREFLY",
    ];

    return [...set].sort((a, b) => {
      const ai = preferredOrder.indexOf(a);
      const bi = preferredOrder.indexOf(b);
      if (ai === -1 && bi === -1) return a.localeCompare(b);
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }, [selectedRecords]);

  const matrixRows = useMemo(() => {
    const rows = [];

    models.forEach((model) => {
      rows.push({
        type: "model",
        label: model,
        getter: (row) => modelValue(row, model),
      });
    });

    rows.push(
      {
        type: "subtotal",
        label: "Total NIO",
        getter: (row) => brandValue(row, "NIO"),
      },
      {
        type: "subtotal",
        label: "Total ONVO",
        getter: (row) => brandValue(row, "ONVO"),
      },
      {
        type: "subtotal",
        label: "Total FIREFLY",
        getter: (row) => brandValue(row, "FIREFLY"),
      },
      {
        type: "grand",
        label: "TOTAL",
        getter: (row) => row.total,
      }
    );

    return rows;
  }, [models]);

  const snapshot = data?.snapshot || {};
  const intelligence = data?.intelligence || {};
  const aspIntelligence = data?.asp_intelligence || {};
  const aspQuarterly = Array.isArray(aspIntelligence?.quarterly)
    ? aspIntelligence.quarterly
    : [];

  const latestAspQuarter =
    aspQuarterly.length > 0 ? aspQuarterly[aspQuarterly.length - 1] : null;

  const latestEffectiveAsp =
    n(latestAspQuarter?.reported_asp_rmb) ??
    n(latestAspQuarter?.forecast_asp_rmb);

  const latestAspRevenue =
    n(latestAspQuarter?.forecast_vehicle_revenue_rmb) ??
    (n(latestAspQuarter?.reported_asp_rmb) !== null &&
    n(latestAspQuarter?.deliveries) !== null
      ? Number(latestAspQuarter.reported_asp_rmb) *
        Number(latestAspQuarter.deliveries)
      : null);

  const latestCoverage = n(latestAspQuarter?.price_coverage_pct);
  const latestAspQoq = n(latestAspQuarter?.asp_qoq_pct);

  const deliveryMomentum = data?.delivery_momentum || {};
  const momentumComponents = deliveryMomentum?.components || {};
  const deliveryMomentumScore = n(deliveryMomentum?.score);
  const businessMomentumScore = n(deliveryMomentum?.business_momentum_score);
  const aspMomentumScore = n(momentumComponents?.asp_momentum?.score);
  const revenueMomentumScore = n(momentumComponents?.revenue_momentum?.score);
  const revenueMomentumQoq = n(momentumComponents?.revenue_momentum?.qoq_pct);
  const revenueMomentumComparison =
    momentumComponents?.revenue_momentum?.comparison || "—";

  const allTotals = monthly
    .map((row) => n(row.total))
    .filter((value) => value !== null);

  const maxMonthly = allTotals.length ? Math.max(...allTotals) : 1;

  const historicalTotal = allTotals.reduce((sum, value) => sum + value, 0);
  const recordRow = monthly.reduce(
    (best, row) =>
      !best || Number(row.total || 0) > Number(best.total || 0) ? row : best,
    null
  );

  const activeModels = new Set();
  monthly.slice(-12).forEach((row) => {
    Object.entries(row.models || {}).forEach(([model, payload]) => {
      const value =
        typeof payload === "number" ? payload : payload?.deliveries;
      if (Number(value || 0) > 0) activeModels.add(model);
    });
  });

  const selectedYearTotal = yearTotal(selectedRecords, (row) => row.total);

  return (
    <div className="qmi-delivery-page">
      <style>{`
        .qmi-delivery-page {
          display: grid;
          gap: 14px;
          color: #e5edf7;
        }

        .qmi-delivery-page * { box-sizing: border-box; }

        .qmi-delivery-panel {
          border: 1px solid rgba(148,163,184,.10);
          border-radius: 14px;
          background:
            linear-gradient(180deg, rgba(16,28,46,.96), rgba(8,15,27,.98));
          box-shadow:
            inset 0 1px 0 rgba(255,255,255,.018),
            0 18px 42px rgba(0,0,0,.10);
        }

        .qmi-delivery-command {
          padding: 18px 20px 0;
          overflow: hidden;
        }

        .qmi-delivery-command-head {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 20px;
        }

        .qmi-delivery-kicker {
          display: block;
          margin-bottom: 5px;
          color: #7c9cff;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: .09em;
          text-transform: uppercase;
        }

        .qmi-delivery-command h2,
        .qmi-delivery-section-title h2 {
          margin: 0;
          color: #f8fafc;
          font-size: 26px;
          font-weight: 950;
          letter-spacing: -.035em;
        }

        .qmi-delivery-command p {
          margin: 5px 0 0;
          color: #7f8da3;
          font-size: 12px;
          line-height: 1.45;
        }

        .qmi-delivery-status {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          min-height: 36px;
          padding: 0 11px;
          border: 1px solid rgba(34,197,94,.18);
          border-radius: 9px;
          background: rgba(6,95,70,.08);
          color: #6ee7b7;
          font-size: 10px;
          font-weight: 850;
          white-space: nowrap;
        }

        .qmi-delivery-status.is-loading {
          border-color: rgba(96,165,250,.20);
          background: rgba(59,130,246,.07);
          color: #93c5fd;
        }

        .qmi-delivery-status.is-error {
          border-color: rgba(244,63,94,.22);
          background: rgba(127,29,29,.08);
          color: #fda4af;
        }

        .qmi-delivery-spin { animation: qmi-delivery-spin 1s linear infinite; }
        @keyframes qmi-delivery-spin { to { transform: rotate(360deg); } }

        .qmi-delivery-tabs {
          display: flex;
          gap: 4px;
          margin-top: 17px;
          border-bottom: 1px solid rgba(148,163,184,.09);
        }

        .qmi-delivery-tabs button {
          position: relative;
          padding: 11px 14px;
          border: 0;
          background: transparent;
          color: #8896a9;
          font-size: 10px;
          font-weight: 850;
          cursor: pointer;
        }

        .qmi-delivery-tabs button.is-active { color: #c4b5fd; }

        .qmi-delivery-tabs button.is-active::after {
          content: "";
          position: absolute;
          left: 11px;
          right: 11px;
          bottom: -1px;
          height: 2px;
          border-radius: 999px;
          background: linear-gradient(90deg,#8b5cf6,#d946ef);
        }

        .qmi-delivery-alert {
          margin: 12px 0 16px;
          padding: 13px 14px;
          border: 1px solid rgba(244,63,94,.22);
          border-radius: 10px;
          background: rgba(127,29,29,.08);
          color: #fecdd3;
          font-size: 11px;
          font-weight: 750;
        }

        .qmi-delivery-kpis {
          display: grid;
          grid-template-columns: repeat(5,minmax(0,1fr));
          gap: 10px;
        }

        .qmi-delivery-kpi {
          position: relative;
          min-height: 112px;
          padding: 15px 16px;
          overflow: hidden;
          border-color: rgba(99,102,241,.11);
          background:
            radial-gradient(circle at 100% 0%, rgba(99,102,241,.10), transparent 35%),
            linear-gradient(180deg, rgba(18,30,49,.96), rgba(10,18,31,.98));
        }

        .qmi-delivery-kpi span {
          display: block;
          margin-bottom: 8px;
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .06em;
          text-transform: uppercase;
        }

        .qmi-delivery-kpi strong {
          display: block;
          color: #f8fafc;
          font-size: 27px;
          line-height: 1;
          font-weight: 950;
          letter-spacing: -.03em;
        }

        .qmi-delivery-kpi small {
          display: block;
          margin-top: 8px;
          color: #8190a4;
          font-size: 9.5px;
          font-weight: 720;
        }

        .qmi-delivery-kpi.is-positive strong { color: #4ade80; }
        .qmi-delivery-kpi.is-accent strong { color: #e8edff; }
        .qmi-delivery-kpi.is-purple strong { color: #f5f3ff; }

        .qmi-delivery-section { padding: 12px; }

        .qmi-delivery-section-head {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 14px;
          margin-bottom: 10px;
          padding: 2px 2px 0;
        }

        .qmi-delivery-section-title {
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .qmi-delivery-icon {
          display: grid;
          width: 31px;
          height: 31px;
          place-items: center;
          border: 1px solid rgba(129,140,248,.17);
          border-radius: 9px;
          background: rgba(99,102,241,.06);
          color: #8b5cf6;
        }

        .qmi-delivery-section-title h2 {
          font-size: 15px;
          text-transform: uppercase;
          letter-spacing: .01em;
        }

        .qmi-delivery-year-select {
          min-width: 96px;
          height: 34px;
          padding: 0 10px;
          border: 1px solid rgba(148,163,184,.12);
          border-radius: 8px;
          outline: 0;
          background: rgba(7,14,25,.80);
          color: #cbd5e1;
          font-size: 10px;
          font-weight: 800;
        }


        .qmi-delivery-main-grid {
          display: grid;
          grid-template-columns: minmax(0, 4.35fr) minmax(250px, 1fr);
          gap: 10px;
          align-items: stretch;
        }

        .qmi-delivery-matrix-panel {
          min-width: 0;
        }

        .qmi-delivery-overview-panel {
          display: grid;
          grid-template-rows: auto repeat(5, minmax(0, 1fr));
          gap: 10px;
          padding: 12px;
          min-width: 0;
        }

        .qmi-delivery-overview-head {
          display: flex;
          align-items: center;
          gap: 10px;
          min-height: 42px;
          padding: 2px 2px 6px;
        }

        .qmi-delivery-overview-head h2 {
          margin: 0;
          color: #f8fafc;
          font-size: 14px;
          font-weight: 950;
          letter-spacing: -.01em;
          text-transform: uppercase;
        }

        .qmi-delivery-overview-card {
          position: relative;
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: center;
          gap: 10px;
          min-height: 96px;
          padding: 12px 13px;
          overflow: hidden;
          border: 1px solid rgba(148,163,184,.09);
          border-radius: 11px;
          background:
            radial-gradient(circle at 100% 0%, rgba(99,102,241,.10), transparent 42%),
            linear-gradient(180deg, rgba(18,30,49,.96), rgba(10,18,31,.98));
        }

        .qmi-delivery-overview-card::after {
          content: "";
          position: absolute;
          right: -30px;
          bottom: -38px;
          width: 120px;
          height: 120px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(139,92,246,.08), transparent 70%);
          pointer-events: none;
        }

        .qmi-delivery-overview-copy {
          min-width: 0;
        }

        .qmi-delivery-overview-copy span {
          display: block;
          color: #8190a5;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-delivery-overview-copy strong {
          display: block;
          margin-top: 7px;
          color: #f8fafc;
          font-size: 22px;
          line-height: 1;
          font-weight: 950;
          letter-spacing: -.025em;
        }

        .qmi-delivery-overview-copy small {
          display: block;
          margin-top: 7px;
          color: #7f8da3;
          font-size: 9px;
          line-height: 1.35;
          font-weight: 720;
        }

        .qmi-delivery-overview-copy strong.is-positive {
          color: #4ade80;
        }

        .qmi-delivery-overview-icon {
          display: grid;
          width: 42px;
          height: 42px;
          place-items: center;
          border: 1px solid rgba(139,92,246,.20);
          border-radius: 10px;
          color: #c084fc;
          background: rgba(109,40,217,.16);
          box-shadow: 0 0 20px rgba(139,92,246,.06);
        }

        .qmi-delivery-overview-icon.is-green {
          color: #4ade80;
          border-color: rgba(34,197,94,.20);
          background: rgba(22,163,74,.12);
        }

        .qmi-delivery-overview-icon.is-blue {
          color: #60a5fa;
          border-color: rgba(59,130,246,.20);
          background: rgba(37,99,235,.12);
        }

        .qmi-delivery-overview-icon.is-amber {
          color: #f59e0b;
          border-color: rgba(245,158,11,.22);
          background: rgba(180,83,9,.12);
        }

        .qmi-delivery-overview-icon.is-cyan {
          color: #22d3ee;
          border-color: rgba(34,211,238,.22);
          background: rgba(8,145,178,.11);
        }

        .qmi-delivery-mini-bars {
          display: flex;
          align-items: end;
          gap: 2px;
          width: 58px;
          height: 30px;
          opacity: .90;
        }

        .qmi-delivery-mini-bars i {
          flex: 1;
          min-width: 2px;
          border-radius: 2px 2px 0 0;
          background: linear-gradient(180deg, #60a5fa, #2563eb);
        }

        .qmi-delivery-mini-bars.is-green i {
          background: linear-gradient(180deg, #4ade80, #16a34a);
        }

        .qmi-delivery-mini-bars.is-purple i {
          background: linear-gradient(180deg, #e879f9, #9333ea);
        }

        .qmi-delivery-mini-bars.is-amber i {
          background: linear-gradient(180deg, #fbbf24, #d97706);
        }

        .qmi-delivery-table-wrap {
          overflow: auto;
          border: 1px solid rgba(148,163,184,.075);
          border-radius: 10px;
          background: rgba(2,8,16,.25);
        }

        .qmi-delivery-table {
          width: 100%;
          min-width: 0;
          table-layout: fixed;
          border-collapse: collapse;
        }

        .qmi-delivery-table th,
        .qmi-delivery-table td {
          height: 34px;
          padding: 6px 7px;
          border-right: 1px solid rgba(148,163,184,.055);
          border-bottom: 1px solid rgba(148,163,184,.055);
          text-align: right;
          color: #cbd5e1;
          font-size: 10px;
          white-space: nowrap;
        }

        .qmi-delivery-table th {
          color: #7f8da3;
          background: rgba(9,18,31,.92);
          font-size: 9px;
          font-weight: 900;
          letter-spacing: .035em;
          text-transform: uppercase;
        }

        .qmi-delivery-table th:first-child,
        .qmi-delivery-table td:first-child {
          position: sticky;
          left: 0;
          z-index: 2;
          width: 150px;
          min-width: 150px;
          text-align: left;
          background: #0b1524;
        }

        .qmi-delivery-table tr.is-subtotal td {
          color: #f8fafc;
          font-size: 10.8px;
          font-weight: 950;
          background: rgba(37,99,235,.17);
        }

        .qmi-delivery-table tr.is-grand td {
          color: #f5f3ff;
          font-size: 11.2px;
          font-weight: 950;
          background: rgba(109,40,217,.24);
        }

        .qmi-delivery-table td.is-quarter,
        .qmi-delivery-table th.is-quarter {
          background: rgba(99,102,241,.055);
          width: 60px;
        }

        .qmi-delivery-table th:last-child,
        .qmi-delivery-table td:last-child {
          width: 72px;
        }

        .qmi-delivery-heat-grid {
          display: grid;
          grid-template-columns: 72px repeat(12,minmax(58px,1fr));
          gap: 4px;
          overflow-x: auto;
          padding-bottom: 4px;
        }

        .qmi-delivery-heat-label,
        .qmi-delivery-heat-year {
          display: grid;
          min-height: 32px;
          place-items: center;
          color: #7f8da3;
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .qmi-delivery-heat-year {
          color: #cbd5e1;
          justify-content: start;
        }

        .qmi-delivery-heat-cell {
          display: grid;
          min-height: 38px;
          place-items: center;
          border: 1px solid rgba(94,234,212,.13);
          border-radius: 4px;
          color: #f8fafc;
          font-size: 10.5px;
          font-weight: 900;
        }

        .qmi-delivery-heat-cell.is-empty {
          background: rgba(148,163,184,.018);
          border-color: rgba(148,163,184,.05);
          color: #334155;
        }

        .qmi-delivery-chart-wrap { width: 100%; }

        .qmi-delivery-chart {
          width: 100%;
          height: 275px;
          display: block;
          filter: drop-shadow(0 0 12px rgba(217,70,239,.08));
        }

        .qmi-delivery-chart-labels {
          display: flex;
          justify-content: space-between;
          color: #64748b;
          font-size: 9.5px;
          font-weight: 800;
        }



        .qmi-monthly-yoy-wrap {
          display: grid;
          gap: 10px;
        }

        .qmi-monthly-yoy-grid {
          display: grid;
          grid-template-columns: repeat(12, minmax(0, 1fr));
          gap: 7px;
          min-height: 265px;
          padding: 18px 14px 10px;
          overflow-x: auto;
          border: 1px solid rgba(148,163,184,.07);
          border-radius: 12px;
          background:
            radial-gradient(circle at 50% 0%, rgba(99,102,241,.06), transparent 42%),
            linear-gradient(180deg, rgba(8,15,27,.48), rgba(4,10,19,.24));
        }

        .qmi-monthly-yoy-col {
          display: grid;
          grid-template-rows: 26px 185px 22px;
          gap: 3px;
          min-width: 54px;
          align-items: end;
          text-align: center;
        }

        .qmi-monthly-yoy-value {
          align-self: center;
          color: #e5edf7;
          font-size: 9.5px;
          font-weight: 950;
        }

        .qmi-monthly-yoy-track {
          display: flex;
          align-items: end;
          justify-content: center;
          height: 185px;
          padding: 0 5px;
          border-bottom: 1px solid rgba(148,163,184,.13);
        }

        .qmi-monthly-yoy-bar {
          width: min(34px, 76%);
          min-height: 10px;
          border-radius: 6px 6px 2px 2px;
          box-shadow: 0 10px 24px rgba(0,0,0,.15);
          transition: transform .18s ease, filter .18s ease;
        }

        .qmi-monthly-yoy-bar:hover {
          transform: translateY(-2px);
          filter: brightness(1.12);
        }

        .qmi-monthly-yoy-bar.is-positive {
          background: linear-gradient(
            180deg,
            #67e8f9 0%,
            #22c55e 34%,
            #84cc16 64%,
            #facc15 100%
          );
        }

        .qmi-monthly-yoy-bar.is-negative {
          background: linear-gradient(
            180deg,
            #f59e0b 0%,
            #f97316 48%,
            #ef4444 100%
          );
        }

        .qmi-monthly-yoy-empty {
          display: grid;
          place-items: end center;
          width: 100%;
          height: 100%;
          padding-bottom: 6px;
          color: #475569;
          font-size: 10px;
          font-weight: 900;
        }

        .qmi-monthly-yoy-label {
          color: #718096;
          font-size: 8.5px;
          font-weight: 900;
          letter-spacing: .05em;
          text-transform: uppercase;
        }

        .qmi-monthly-yoy-scale {
          display: grid;
          grid-template-columns: auto 1fr auto;
          gap: 9px;
          align-items: center;
          color: #64748b;
          font-size: 8px;
          font-weight: 800;
        }

        .qmi-monthly-yoy-scale-bar {
          height: 7px;
          border-radius: 999px;
          background: linear-gradient(
            90deg,
            #ef4444 0%,
            #f97316 20%,
            #facc15 43%,
            #84cc16 64%,
            #22c55e 82%,
            #67e8f9 100%
          );
        }

        .qmi-yoy-chart {
          position: relative;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(74px, 1fr));
          gap: 12px;
          align-items: end;
          min-height: 285px;
          padding: 24px 20px 14px;
          overflow: hidden;
          border: 1px solid rgba(148,163,184,.07);
          border-radius: 12px;
          background:
            radial-gradient(circle at 50% 0%, rgba(99,102,241,.07), transparent 42%),
            linear-gradient(180deg, rgba(8,15,27,.50), rgba(4,10,19,.28));
        }

        .qmi-yoy-chart::before,
        .qmi-yoy-chart::after {
          content: "";
          position: absolute;
          left: 18px;
          right: 18px;
          height: 1px;
          background: rgba(148,163,184,.08);
          pointer-events: none;
        }

        .qmi-yoy-chart::before { top: 34%; }
        .qmi-yoy-chart::after { top: 66%; }

        .qmi-yoy-zero-line {
          position: absolute;
          left: 18px;
          right: 18px;
          bottom: 43px;
          height: 1px;
          background: rgba(148,163,184,.16);
          pointer-events: none;
        }

        .qmi-yoy-column {
          position: relative;
          z-index: 1;
          display: grid;
          grid-template-rows: 26px 190px 24px;
          gap: 4px;
          min-width: 0;
          align-items: end;
          text-align: center;
        }

        .qmi-yoy-value {
          align-self: center;
          color: #e5edf7;
          font-size: 10px;
          font-weight: 950;
          letter-spacing: .02em;
        }

        .qmi-yoy-track {
          display: flex;
          align-items: end;
          justify-content: center;
          height: 190px;
          padding: 0 9px;
        }

        .qmi-yoy-bar {
          position: relative;
          width: min(46px, 72%);
          min-height: 10px;
          border-radius: 7px 7px 3px 3px;
          box-shadow: 0 10px 28px rgba(0,0,0,.18);
          transition: transform .18s ease, filter .18s ease;
        }

        .qmi-yoy-bar:hover {
          transform: translateY(-2px);
          filter: brightness(1.12);
        }

        .qmi-yoy-bar.is-positive {
          background: linear-gradient(
            180deg,
            #67e8f9 0%,
            #22c55e 34%,
            #84cc16 64%,
            #facc15 100%
          );
          box-shadow:
            0 0 22px rgba(34,197,94,.12),
            0 10px 28px rgba(0,0,0,.18);
        }

        .qmi-yoy-bar.is-negative {
          background: linear-gradient(
            180deg,
            #f59e0b 0%,
            #f97316 48%,
            #ef4444 100%
          );
          box-shadow:
            0 0 22px rgba(239,68,68,.10),
            0 10px 28px rgba(0,0,0,.18);
        }

        .qmi-yoy-year {
          align-self: end;
          color: #718096;
          font-size: 9px;
          font-weight: 900;
          letter-spacing: .055em;
        }

        .qmi-delivery-chart-empty {
          padding: 50px;
          text-align: center;
          color: #64748b;
          font-size: 11px;
        }

        .qmi-delivery-intel-grid {
          display: grid;
          grid-template-columns: repeat(4,minmax(0,1fr));
          gap: 10px;
        }

        .qmi-delivery-intel-card {
          min-height: 110px;
          padding: 15px;
          border: 1px solid rgba(148,163,184,.09);
          border-radius: 11px;
          background:
            linear-gradient(180deg, rgba(18,30,49,.94), rgba(10,18,31,.97));
        }

        .qmi-delivery-intel-card span {
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-delivery-intel-card strong {
          display: block;
          margin-top: 9px;
          color: #f8fafc;
          font-size: 22px;
          font-weight: 950;
        }



        .qmi-momentum-score-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-momentum-score-card {
          position: relative;
          min-height: 126px;
          padding: 16px;
          overflow: hidden;
          border: 1px solid rgba(148,163,184,.09);
          border-radius: 12px;
          background:
            radial-gradient(circle at 100% 0%, rgba(99,102,241,.13), transparent 42%),
            linear-gradient(180deg, rgba(18,30,49,.97), rgba(9,17,29,.98));
        }

        .qmi-momentum-score-card::after {
          content: "";
          position: absolute;
          right: -28px;
          bottom: -48px;
          width: 135px;
          height: 135px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(139,92,246,.10), transparent 68%);
          pointer-events: none;
        }

        .qmi-momentum-score-card-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
        }

        .qmi-momentum-score-card-head span {
          color: #8796aa;
          font-size: 9.5px;
          font-weight: 900;
          letter-spacing: .055em;
          text-transform: uppercase;
        }

        .qmi-momentum-score-card strong {
          display: block;
          margin-top: 10px;
          color: #f8fafc;
          font-size: 29px;
          line-height: 1;
          font-weight: 950;
          letter-spacing: -.035em;
        }

        .qmi-momentum-score-card strong.is-strong {
          color: #4ade80;
        }

        .qmi-momentum-score-card strong.is-positive {
          color: #67e8f9;
        }

        .qmi-momentum-score-card strong.is-neutral {
          color: #fbbf24;
        }

        .qmi-momentum-score-card strong.is-weak {
          color: #fb7185;
        }

        .qmi-momentum-score-meta {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 8px;
          margin-top: 9px;
          color: #738197;
          font-size: 8.5px;
          font-weight: 780;
        }

        .qmi-momentum-score-bar {
          position: relative;
          height: 5px;
          margin-top: 12px;
          overflow: hidden;
          border-radius: 999px;
          background: rgba(100,116,139,.16);
        }

        .qmi-momentum-score-fill {
          height: 100%;
          border-radius: inherit;
          background: linear-gradient(90deg, #ef4444 0%, #f59e0b 28%, #84cc16 62%, #22c55e 82%, #67e8f9 100%);
        }

        .qmi-momentum-score-section {
          padding: 14px;
        }

        .qmi-momentum-score-section .qmi-delivery-section-head {
          margin-bottom: 12px;
        }

        .qmi-asp-grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 10px;
        }

        .qmi-asp-card {
          min-height: 118px;
          padding: 15px 16px;
          border: 1px solid rgba(148,163,184,.09);
          border-radius: 12px;
          background:
            radial-gradient(circle at 100% 0%, rgba(217,70,239,.10), transparent 38%),
            linear-gradient(180deg, rgba(18,30,49,.96), rgba(10,18,31,.98));
        }

        .qmi-asp-card-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
        }

        .qmi-asp-card-label {
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .06em;
          text-transform: uppercase;
        }

        .qmi-asp-card-icon {
          display: grid;
          width: 29px;
          height: 29px;
          place-items: center;
          border: 1px solid rgba(196,181,253,.16);
          border-radius: 9px;
          color: #c4b5fd;
          background: rgba(139,92,246,.07);
        }

        .qmi-asp-card strong {
          display: block;
          margin-top: 9px;
          color: #f8fafc;
          font-size: 26px;
          font-weight: 950;
          letter-spacing: -.025em;
        }

        .qmi-asp-card small {
          display: block;
          margin-top: 6px;
          color: #7f8da3;
          font-size: 10.5px;
          line-height: 1.35;
          font-weight: 720;
        }

        .qmi-asp-card .positive { color: #4ade80; }
        .qmi-asp-card .negative { color: #fb7185; }
        .qmi-asp-card .accent { color: #60a5fa; }
        .qmi-asp-card .purple { color: #e879f9; }

        .qmi-asp-layout {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) minmax(330px, .75fr);
          gap: 12px;
        }

        .qmi-asp-chart-panel,
        .qmi-asp-side-panel {
          padding: 14px;
        }

        .qmi-asp-chart-wrap { width: 100%; }

        .qmi-asp-chart {
          display: block;
          width: 100%;
          height: 278px;
        }

        .qmi-asp-chart-legend {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
          margin-bottom: 8px;
          color: #7f8da3;
          font-size: 10px;
          font-weight: 800;
        }

        .qmi-asp-chart-legend span {
          display: inline-flex;
          align-items: center;
          gap: 6px;
        }

        .qmi-asp-chart-legend i {
          display: inline-block;
          width: 15px;
          height: 2px;
          border-radius: 999px;
        }

        .qmi-asp-chart-legend i.reported { background: #60a5fa; }
        .qmi-asp-chart-legend i.forecast { background: #d946ef; }
        .qmi-asp-chart-legend i.mix { background: #64748b; }

        .qmi-asp-chart-labels {
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          gap: 3px;
          color: #64748b;
          font-size: 9px;
          font-weight: 800;
          text-align: center;
        }

        .qmi-asp-chart-empty {
          min-height: 260px;
          display: grid;
          place-items: center;
          color: #64748b;
          font-size: 10px;
        }

        .qmi-asp-state {
          display: grid;
          gap: 9px;
        }

        .qmi-asp-state-row {
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 12px;
          align-items: center;
          padding: 11px 12px;
          border: 1px solid rgba(148,163,184,.075);
          border-radius: 9px;
          background: rgba(2,8,16,.24);
        }

        .qmi-asp-state-row span {
          color: #8190a5;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .045em;
          text-transform: uppercase;
        }

        .qmi-asp-state-row strong {
          color: #f8fafc;
          font-size: 12.5px;
          font-weight: 900;
          text-align: right;
        }

        .qmi-asp-quarter-table-wrap {
          overflow: auto;
          border: 1px solid rgba(148,163,184,.075);
          border-radius: 10px;
          background: rgba(2,8,16,.22);
        }

        .qmi-asp-quarter-table {
          width: 100%;
          min-width: 980px;
          border-collapse: collapse;
        }

        .qmi-asp-quarter-table th,
        .qmi-asp-quarter-table td {
          height: 36px;
          padding: 8px 10px;
          border-right: 1px solid rgba(148,163,184,.055);
          border-bottom: 1px solid rgba(148,163,184,.055);
          color: #cbd5e1;
          font-size: 10.5px;
          text-align: right;
          white-space: nowrap;
        }

        .qmi-asp-quarter-table th {
          color: #7f8da3;
          background: rgba(9,18,31,.92);
          font-size: 9.5px;
          font-weight: 900;
          letter-spacing: .04em;
          text-transform: uppercase;
        }

        .qmi-asp-quarter-table th:first-child,
        .qmi-asp-quarter-table td:first-child {
          text-align: left;
        }

        .qmi-asp-quarter-table tr.is-latest td {
          background: rgba(139,92,246,.07);
          color: #f5f3ff;
          font-weight: 850;
        }

        .qmi-asp-badge {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 4px 7px;
          border: 1px solid rgba(139,92,246,.20);
          border-radius: 999px;
          background: rgba(139,92,246,.07);
          color: #c4b5fd;
          font-size: 7.5px;
          font-weight: 900;
          letter-spacing: .04em;
          text-transform: uppercase;
        }

        @media (max-width: 1200px) {
          .qmi-delivery-main-grid {
            grid-template-columns: 1fr;
          }

          .qmi-momentum-score-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .qmi-delivery-overview-panel {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            grid-template-rows: auto;
          }

          .qmi-delivery-overview-head {
            grid-column: 1 / -1;
          }

          .qmi-delivery-kpis,
          .qmi-asp-grid {
            grid-template-columns: repeat(2,minmax(0,1fr));
          }

          .qmi-asp-layout {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 760px) {
          .qmi-delivery-command-head,
          .qmi-delivery-section-head {
            flex-direction: column;
            align-items: stretch;
          }

          .qmi-delivery-overview-panel,
          .qmi-delivery-kpis,
          .qmi-delivery-intel-grid,
          .qmi-asp-grid,
          .qmi-momentum-score-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <section className="qmi-delivery-panel qmi-delivery-command">
        <div className="qmi-delivery-command-head">
          <div>
            <span className="qmi-delivery-kicker">
              DE-CI-NIO-001.0 · COMPANY INTELLIGENCE
            </span>
            <h2>NIO Deliveries Intelligence</h2>
            <p>
              Análisis completo de entregas por modelo y marca, evolución histórica y momentum operativo.
            </p>
          </div>

          <div
            className={`qmi-delivery-status ${
              loading ? "is-loading" : error ? "is-error" : ""
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="qmi-delivery-spin" size={14} />
                Loading deliveries
              </>
            ) : error ? (
              <>
                <AlertTriangle size={14} />
                Engine unavailable
              </>
            ) : (
              <>
                <CheckCircle2 size={14} />
                Delivery engine online
              </>
            )}
          </div>
        </div>

        <div className="qmi-delivery-tabs">
          {[
            ["deliveries", "Deliveries"],
            ["asp", "ASP & Revenue"],
            ["trends", "Trends"],
            ["comparison", "Comparison"],
            ["info", "Information"],
          ].map(([id, label]) => (
            <button
              key={id}
              type="button"
              className={tab === id ? "is-active" : ""}
              onClick={() => setTab(id)}
            >
              {label}
            </button>
          ))}
        </div>

        {error ? <div className="qmi-delivery-alert">{error}</div> : null}
      </section>

      {!loading && data ? (
        <>
          {tab !== "deliveries" ? (
            <section className="qmi-delivery-kpis">
            <div className="qmi-delivery-kpi is-accent">
              <span>Cumulative Deliveries</span>
              <strong>{fmt(historicalTotal)}</strong>
              <small>Dataset history</small>
            </div>
            <div className="qmi-delivery-kpi is-positive">
              <span>YTD {snapshot?.latest_period?.slice?.(0, 4) || ""}</span>
              <strong>{fmt(snapshot?.ytd_total)}</strong>
              <small>{pct(snapshot?.yoy_pct)} latest-month YoY</small>
            </div>
            <div className="qmi-delivery-kpi is-purple">
              <span>Record Month</span>
              <strong>{fmt(recordRow?.total)}</strong>
              <small>{recordRow?.period || "—"}</small>
            </div>
            <div className="qmi-delivery-kpi">
              <span>3M Run Rate</span>
              <strong>{fmt(snapshot?.annualized_run_rate)}</strong>
              <small>Annualized from recent average</small>
            </div>
            <div className="qmi-delivery-kpi">
              <span>Active Models</span>
              <strong>{activeModels.size || "—"}</strong>
              <small>{pretty(intelligence?.delivery_regime)}</small>
            </div>
            </section>
          ) : null}

          {tab === "deliveries" ? (
            <>
              <div className="qmi-delivery-main-grid">
                <section className="qmi-delivery-panel qmi-delivery-section qmi-delivery-matrix-panel">
                  <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <CalendarDays size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">
                        MONTHLY MODEL MATRIX
                      </span>
                      <h2>Deliveries by Model</h2>
                    </div>
                  </div>

                  <select
                    className="qmi-delivery-year-select"
                    value={selectedYear || ""}
                    onChange={(event) => setSelectedYear(Number(event.target.value))}
                  >
                    {years.map((year) => (
                      <option key={year} value={year}>{year}</option>
                    ))}
                  </select>
                </div>

                <div className="qmi-delivery-table-wrap">
                  <table className="qmi-delivery-table">
                    <thead>
                      <tr>
                        <th>Model / Brand</th>
                        {MONTHS.map((month) => <th key={month}>{month}</th>)}
                        {QUARTERS.map((quarter) => (
                          <th className="is-quarter" key={quarter.label}>
                            {quarter.label}
                          </th>
                        ))}
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matrixRows.map((item) => (
                        <tr
                          key={item.label}
                          className={
                            item.type === "grand"
                              ? "is-grand"
                              : item.type === "subtotal"
                                ? "is-subtotal"
                                : ""
                          }
                        >
                          <td>{item.label}</td>
                          {Array.from({ length: 12 }, (_, index) => {
                            const row = selectedRecords.find(
                              (record) => record.month === index + 1
                            );
                            return <td key={index}>{fmt(row ? item.getter(row) : null)}</td>;
                          })}
                          {QUARTERS.map((quarter) => (
                            <td className="is-quarter" key={quarter.label}>
                              {fmt(
                                quarterTotal(
                                  selectedRecords,
                                  quarter.months,
                                  item.getter
                                )
                              )}
                            </td>
                          ))}
                          <td>{fmt(yearTotal(selectedRecords, item.getter))}</td>
                        </tr>
                      ))}

                      <tr className="is-grand">
                        <td>{selectedYear} TOTAL</td>
                        {Array.from({ length: 12 }, (_, index) => {
                          const row = selectedRecords.find(
                            (record) => record.month === index + 1
                          );
                          return <td key={index}>{fmt(row?.total)}</td>;
                        })}
                        {QUARTERS.map((quarter) => (
                          <td className="is-quarter" key={quarter.label}>
                            {fmt(
                              quarterTotal(
                                selectedRecords,
                                quarter.months,
                                (row) => row.total
                              )
                            )}
                          </td>
                        ))}
                        <td>{fmt(selectedYearTotal)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                </section>

                <aside className="qmi-delivery-panel qmi-delivery-overview-panel">
                  <div className="qmi-delivery-overview-head">
                    <div className="qmi-delivery-icon">
                      <BarChart3 size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">DELIVERIES OVERVIEW</span>
                      <h2>Performance Snapshot</h2>
                    </div>
                  </div>

                  <div className="qmi-delivery-overview-card">
                    <div className="qmi-delivery-overview-copy">
                      <span>Cumulative Deliveries</span>
                      <strong>{fmt(historicalTotal)}</strong>
                      <small>Dataset history</small>
                    </div>
                    <div className="qmi-delivery-overview-icon">
                      <TrendingUp size={21} />
                    </div>
                  </div>

                  <div className="qmi-delivery-overview-card">
                    <div className="qmi-delivery-overview-copy">
                      <span>YTD {snapshot?.latest_period?.slice?.(0, 4) || ""}</span>
                      <strong className="is-positive">{fmt(snapshot?.ytd_total)}</strong>
                      <small>{pct(snapshot?.yoy_pct)} latest-month YoY</small>
                    </div>
                    <div className="qmi-delivery-overview-icon is-green">
                      <CalendarDays size={21} />
                    </div>
                  </div>

                  <div className="qmi-delivery-overview-card">
                    <div className="qmi-delivery-overview-copy">
                      <span>Record Month</span>
                      <strong>{fmt(recordRow?.total)}</strong>
                      <small>{recordRow?.period || "—"}</small>
                    </div>
                    <div className="qmi-delivery-overview-icon is-blue">
                      <Sparkles size={21} />
                    </div>
                  </div>

                  <div className="qmi-delivery-overview-card">
                    <div className="qmi-delivery-overview-copy">
                      <span>3M Run Rate</span>
                      <strong>{fmt(snapshot?.annualized_run_rate)}</strong>
                      <small>Annualized from recent average</small>
                    </div>
                    <div className="qmi-delivery-overview-icon is-amber">
                      <TrendingUp size={21} />
                    </div>
                  </div>

                  <div className="qmi-delivery-overview-card">
                    <div className="qmi-delivery-overview-copy">
                      <span>Active Models</span>
                      <strong>{activeModels.size || "—"}</strong>
                      <small>{pretty(intelligence?.delivery_regime)}</small>
                    </div>
                    <div className="qmi-delivery-overview-icon is-cyan">
                      <BarChart3 size={21} />
                    </div>
                  </div>
                </aside>
              </div>

              <section className="qmi-delivery-panel qmi-delivery-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <BarChart3 size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">HEATMAP</span>
                      <h2>Monthly Delivery Intensity</h2>
                    </div>
                  </div>
                </div>

                <div className="qmi-delivery-heat-grid">
                  <div />
                  {MONTHS.map((month) => (
                    <div key={month} className="qmi-delivery-heat-label">
                      {month}
                    </div>
                  ))}

                  {[...years].reverse().map((year) => {
                    const yearRows = monthly.filter(
                      (row) => Number(row.year) === Number(year)
                    );

                    return (
                      <>
                        <div className="qmi-delivery-heat-year" key={`${year}-label`}>
                          {year}
                        </div>
                        {Array.from({ length: 12 }, (_, index) => {
                          const row = yearRows.find(
                            (record) => Number(record.month) === index + 1
                          );
                          return (
                            <HeatCell
                              key={`${year}-${index + 1}`}
                              value={row?.total}
                              max={maxMonthly}
                            />
                          );
                        })}
                      </>
                    );
                  })}
                </div>
              </section>

              <section className="qmi-delivery-panel qmi-delivery-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <BarChart3 size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">MONTHLY MOMENTUM</span>
                      <h2>Monthly YoY Growth · {selectedYear}</h2>
                    </div>
                  </div>

                  <select
                    className="qmi-delivery-year-select"
                    value={selectedYear || ""}
                    onChange={(event) =>
                      setSelectedYear(Number(event.target.value))
                    }
                  >
                    {years.map((year) => (
                      <option key={year} value={year}>
                        {year}
                      </option>
                    ))}
                  </select>
                </div>

                <MonthlyYoYChart
                  records={monthly}
                  selectedYear={selectedYear}
                />
              </section>

              <section className="qmi-delivery-panel qmi-delivery-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <TrendingUp size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">ANNUAL MOMENTUM</span>
                      <h2>Year-over-Year Delivery Growth</h2>
                    </div>
                  </div>
                </div>
                <AnnualVariationChart records={monthly} />
              </section>

              <section className="qmi-delivery-panel qmi-delivery-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <TrendingUp size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">HISTORICAL TREND</span>
                      <h2>Monthly Deliveries Evolution</h2>
                    </div>
                  </div>
                </div>
                <TrendChart records={monthly} />
              </section>
            </>
          ) : null}

          {tab === "asp" ? (
            <>
              <section className="qmi-delivery-panel qmi-momentum-score-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <TrendingUp size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">
                        DE-NIO-DM-001.1 · BUSINESS MOMENTUM
                      </span>
                      <h2>Momentum Intelligence</h2>
                    </div>
                  </div>

                  <span className="qmi-asp-badge">
                    {deliveryMomentum?.regime
                      ? pretty(deliveryMomentum.regime)
                      : "Awaiting Engine"}
                  </span>
                </div>

                <div className="qmi-momentum-score-grid">
                  {[
                    {
                      label: "Delivery Momentum",
                      value: deliveryMomentumScore,
                      detail: deliveryMomentum?.trend
                        ? pretty(deliveryMomentum.trend)
                        : "Volume momentum",
                    },
                    {
                      label: "ASP Momentum",
                      value: aspMomentumScore,
                      detail:
                        momentumComponents?.asp_momentum?.qoq_pct !== undefined &&
                        momentumComponents?.asp_momentum?.qoq_pct !== null
                          ? `${pct(momentumComponents.asp_momentum.qoq_pct)} QoQ`
                          : "Pricing momentum",
                    },
                    {
                      label: "Revenue Momentum",
                      value: revenueMomentumScore,
                      detail:
                        revenueMomentumQoq !== null
                          ? `${pct(revenueMomentumQoq)} · ${
                              revenueMomentumComparison === "like_for_like_partial_quarter"
                                ? "Like-for-like"
                                : pretty(revenueMomentumComparison)
                            }`
                          : "Revenue momentum",
                    },
                    {
                      label: "Business Momentum",
                      value: businessMomentumScore,
                      detail: deliveryMomentum?.confidence
                        ? `${deliveryMomentum.confidence} confidence`
                        : "Composite business score",
                    },
                  ].map((item) => {
                    const score = item.value;
                    const tone =
                      score === null
                        ? "is-neutral"
                        : score >= 75
                        ? "is-strong"
                        : score >= 60
                        ? "is-positive"
                        : score >= 45
                        ? "is-neutral"
                        : "is-weak";

                    return (
                      <div className="qmi-momentum-score-card" key={item.label}>
                        <div className="qmi-momentum-score-card-head">
                          <span>{item.label}</span>
                          <TrendingUp size={15} />
                        </div>

                        <strong className={tone}>
                          {score !== null ? score.toFixed(1) : "—"}
                        </strong>

                        <div className="qmi-momentum-score-meta">
                          <span>{item.detail}</span>
                          <span>/100</span>
                        </div>

                        <div className="qmi-momentum-score-bar">
                          <div
                            className="qmi-momentum-score-fill"
                            style={{
                              width: `${Math.max(
                                0,
                                Math.min(100, score ?? 0)
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="qmi-asp-grid">
                <div className="qmi-delivery-panel qmi-asp-card">
                  <div className="qmi-asp-card-head">
                    <span className="qmi-asp-card-label">Latest ASP</span>
                    <div className="qmi-asp-card-icon">
                      <CircleDollarSign size={16} />
                    </div>
                  </div>
                  <strong className="purple">
                    {fmtCnyK(latestEffectiveAsp)}
                  </strong>
                  <small>
                    {latestAspQuarter?.reported_asp_rmb
                      ? `${latestAspQuarter?.quarter} reported`
                      : `${latestAspQuarter?.quarter || "—"} QMI forecast`}
                  </small>
                </div>

                <div className="qmi-delivery-panel qmi-asp-card">
                  <div className="qmi-asp-card-head">
                    <span className="qmi-asp-card-label">Model-Mix ASP</span>
                    <div className="qmi-asp-card-icon">
                      <BarChart3 size={16} />
                    </div>
                  </div>
                  <strong>{fmtCnyK(latestAspQuarter?.model_mix_asp_rmb)}</strong>
                  <small>Delivery-weighted MSRP proxy</small>
                </div>

                <div className="qmi-delivery-panel qmi-asp-card">
                  <div className="qmi-asp-card-head">
                    <span className="qmi-asp-card-label">Vehicle Revenue</span>
                    <div className="qmi-asp-card-icon">
                      <TrendingUp size={16} />
                    </div>
                  </div>
                  <strong className="accent">
                    {fmtCnyB(latestAspRevenue)}
                  </strong>
                  <small>
                    {latestAspQuarter?.is_forecast
                      ? "Estimated from QMI ASP"
                      : "Derived from reported ASP"}
                  </small>
                </div>

                <div className="qmi-delivery-panel qmi-asp-card">
                  <div className="qmi-asp-card-head">
                    <span className="qmi-asp-card-label">ASP QoQ</span>
                    <div className="qmi-asp-card-icon">
                      <Sparkles size={16} />
                    </div>
                  </div>
                  <strong className={aspTone(latestAspQoq)}>
                    {pct(latestAspQoq)}
                  </strong>
                  <small>{pretty(aspIntelligence?.premiumization_state)}</small>
                </div>

                <div className="qmi-delivery-panel qmi-asp-card">
                  <div className="qmi-asp-card-head">
                    <span className="qmi-asp-card-label">Price Coverage</span>
                    <div className="qmi-asp-card-icon">
                      <ShieldCheck size={16} />
                    </div>
                  </div>
                  <strong className={latestCoverage >= 90 ? "positive" : ""}>
                    {latestCoverage !== null ? `${latestCoverage.toFixed(1)}%` : "—"}
                  </strong>
                  <small>{aspIntelligence?.confidence || "—"} confidence</small>
                </div>
              </section>

              <section className="qmi-asp-layout">
                <div className="qmi-delivery-panel qmi-asp-chart-panel">
                  <div className="qmi-delivery-section-head">
                    <div className="qmi-delivery-section-title">
                      <div className="qmi-delivery-icon">
                        <TrendingUp size={17} />
                      </div>
                      <div>
                        <span className="qmi-delivery-kicker">
                          DE-NIO-ASP-001.0 · QUARTERLY ASP
                        </span>
                        <h2>ASP & Revenue Intelligence</h2>
                      </div>
                    </div>

                    <span className="qmi-asp-badge">
                      {latestAspQuarter?.is_forecast ? "Forecast Active" : "Reported"}
                    </span>
                  </div>

                  <AspTrendChart rows={aspQuarterly} />
                </div>

                <div className="qmi-delivery-panel qmi-asp-side-panel">
                  <div className="qmi-delivery-section-head">
                    <div className="qmi-delivery-section-title">
                      <div className="qmi-delivery-icon">
                        <ShieldCheck size={17} />
                      </div>
                      <div>
                        <span className="qmi-delivery-kicker">
                          ENGINE STATE
                        </span>
                        <h2>ASP Diagnostics</h2>
                      </div>
                    </div>
                  </div>

                  <div className="qmi-asp-state">
                    <div className="qmi-asp-state-row">
                      <span>ASP Trend</span>
                      <strong>{pretty(aspIntelligence?.asp_trend)}</strong>
                    </div>
                    <div className="qmi-asp-state-row">
                      <span>Premiumization</span>
                      <strong>{pretty(aspIntelligence?.premiumization_state)}</strong>
                    </div>
                    <div className="qmi-asp-state-row">
                      <span>Calibration Factor</span>
                      <strong>
                        {n(aspIntelligence?.calibration_factor) !== null
                          ? Number(aspIntelligence.calibration_factor).toFixed(4)
                          : "—"}
                      </strong>
                    </div>
                    <div className="qmi-asp-state-row">
                      <span>Price Coverage</span>
                      <strong>
                        {latestCoverage !== null
                          ? `${latestCoverage.toFixed(1)}%`
                          : "—"}
                      </strong>
                    </div>
                    <div className="qmi-asp-state-row">
                      <span>Confidence</span>
                      <strong>{aspIntelligence?.confidence || "—"}</strong>
                    </div>
                    <div className="qmi-asp-state-row">
                      <span>Latest Quarter</span>
                      <strong>{aspIntelligence?.latest_quarter || "—"}</strong>
                    </div>
                  </div>
                </div>
              </section>

              <section className="qmi-delivery-panel qmi-delivery-section">
                <div className="qmi-delivery-section-head">
                  <div className="qmi-delivery-section-title">
                    <div className="qmi-delivery-icon">
                      <CircleDollarSign size={17} />
                    </div>
                    <div>
                      <span className="qmi-delivery-kicker">
                        QUARTERLY HISTORY
                      </span>
                      <h2>ASP Calibration & Revenue</h2>
                    </div>
                  </div>
                </div>

                <div className="qmi-asp-quarter-table-wrap">
                  <table className="qmi-asp-quarter-table">
                    <thead>
                      <tr>
                        <th>Quarter</th>
                        <th>Deliveries</th>
                        <th>Coverage</th>
                        <th>Model-Mix ASP</th>
                        <th>Reported ASP</th>
                        <th>Forecast ASP</th>
                        <th>ASP QoQ</th>
                        <th>Calibration</th>
                        <th>Vehicle Revenue</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {aspQuarterly
                        .filter((row) => Number(row.year) >= 2025)
                        .map((row) => {
                          const revenue =
                            n(row.forecast_vehicle_revenue_rmb) ??
                            (n(row.reported_asp_rmb) !== null
                              ? Number(row.reported_asp_rmb) *
                                Number(row.deliveries)
                              : null);

                          return (
                            <tr
                              key={row.quarter}
                              className={
                                row.quarter === aspIntelligence?.latest_quarter
                                  ? "is-latest"
                                  : ""
                              }
                            >
                              <td>{row.quarter}</td>
                              <td>{fmt(row.deliveries)}</td>
                              <td>{pct(row.price_coverage_pct, 1).replace("+", "")}</td>
                              <td>{fmtCnyK(row.model_mix_asp_rmb)}</td>
                              <td>{fmtCnyK(row.reported_asp_rmb)}</td>
                              <td>{fmtCnyK(row.forecast_asp_rmb)}</td>
                              <td className={`is-${aspTone(row.asp_qoq_pct)}`}>
                                {pct(row.asp_qoq_pct)}
                              </td>
                              <td>
                                {n(row.calibration_factor) !== null
                                  ? Number(row.calibration_factor).toFixed(4)
                                  : "—"}
                              </td>
                              <td>{fmtCnyB(revenue)}</td>
                              <td>
                                <span className="qmi-asp-badge">
                                  {row.is_forecast ? "Forecast" : "Reported"}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          ) : null}

          {tab === "trends" ? (
            <section className="qmi-delivery-panel qmi-delivery-section">
              <div className="qmi-delivery-intel-grid">
                <div className="qmi-delivery-intel-card">
                  <span>Delivery Score</span>
                  <strong>{fmt(intelligence?.delivery_score)}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>Momentum</span>
                  <strong>{pretty(intelligence?.momentum_state)}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>3M Trend</span>
                  <strong>{pretty(intelligence?.trend_3m)}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>Brand Diversification</span>
                  <strong>{pretty(intelligence?.brand_diversification)}</strong>
                </div>
              </div>
            </section>
          ) : null}

          {tab === "comparison" ? (
            <section className="qmi-delivery-panel qmi-delivery-section">
              <div className="qmi-delivery-section-title">
                <div className="qmi-delivery-icon">
                  <BarChart3 size={17} />
                </div>
                <div>
                  <span className="qmi-delivery-kicker">YEAR COMPARISON</span>
                  <h2>Annual Delivery Totals</h2>
                </div>
              </div>

              <div className="qmi-delivery-kpis" style={{ marginTop: 14 }}>
                {years.map((year) => {
                  const rows = monthly.filter((row) => Number(row.year) === year);
                  return (
                    <div className="qmi-delivery-kpi" key={year}>
                      <span>{year}</span>
                      <strong>{fmt(yearTotal(rows, (row) => row.total))}</strong>
                      <small>{rows.length} reported months</small>
                    </div>
                  );
                })}
              </div>
            </section>
          ) : null}

          {tab === "info" ? (
            <section className="qmi-delivery-panel qmi-delivery-section">
              <div className="qmi-delivery-intel-grid">
                <div className="qmi-delivery-intel-card">
                  <span>Dataset Source</span>
                  <strong>{data?.dataset_source || "Deliveries.xlsx"}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>Engine</span>
                  <strong>{data?.engine_id || "DE-CI-NIO-001.0"}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>Latest Period</span>
                  <strong>{snapshot?.latest_period || "—"}</strong>
                </div>
                <div className="qmi-delivery-intel-card">
                  <span>Confidence</span>
                  <strong>{intelligence?.confidence || "—"}</strong>
                </div>
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

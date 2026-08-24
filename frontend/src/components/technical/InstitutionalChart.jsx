import { useMemo, useState } from "react";

function n(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizePoint(point) {
  const open = n(point?.open ?? point?.Open);
  const high = n(point?.high ?? point?.High);
  const low = n(point?.low ?? point?.Low);
  const close = n(point?.close ?? point?.Close);

  if (
    open === null ||
    high === null ||
    low === null ||
    close === null
  ) {
    return null;
  }

  return {
    date: String(point?.date ?? point?.Date ?? ""),
    open,
    high,
    low,
    close,
  };
}

function priceLabel(value) {
  return Number(value).toFixed(2);
}

function eventLabel(type) {
  if (!type) return "";
  return String(type)
    .replaceAll("_", " ")
    .replace("BULLISH ", "")
    .replace("BEARISH ", "");
}

export default function InstitutionalChart({
  history = [],
  marketStructure = null,
  supportResistance = null,
  liquidity = null,
  maxBars = 120,
}) {
  const [viewBars, setViewBars] = useState(maxBars);
  const [layers, setLayers] = useState({
    zones: true,
    swings: true,
    events: true,
    protected: true,
    liquidity: true,
    sweeps: true,
    clusters: true,
  });
  const model = useMemo(() => {
    const rows = (Array.isArray(history) ? history : [])
      .map(normalizePoint)
      .filter(Boolean)
      .slice(-viewBars);

    if (rows.length < 10) {
      return null;
    }

    const zones = Array.isArray(supportResistance?.zones)
      ? supportResistance.zones
      : [];

    const liquidityPools = Array.isArray(liquidity?.pools)
      ? liquidity.pools
      : [];

    // DE-UI-007.5
    // Render only institutionally validated sweeps when the DE-TA-007.3
    // stream is available. Fall back to raw sweeps only for older backends.
    const hasInstitutionalSweepStream = Array.isArray(
      liquidity?.institutional_sweeps
    );

    const liquiditySweeps = hasInstitutionalSweepStream
      ? liquidity.institutional_sweeps
      : Array.isArray(liquidity?.sweeps)
        ? liquidity.sweeps
        : [];

    const sweepClusters = Array.isArray(liquidity?.sweep_clusters)
      ? liquidity.sweep_clusters
      : [];

    const swings = Array.isArray(marketStructure?.swings)
      ? marketStructure.swings
      : [];

    const events = Array.isArray(marketStructure?.events)
      ? marketStructure.events
      : [];

    const protectedHigh =
      marketStructure?.protected_levels?.protected_high ?? null;
    const protectedLow =
      marketStructure?.protected_levels?.protected_low ?? null;

    const dates = new Map(
      rows.map((row, index) => [row.date, index])
    );

    const visibleSwings = swings
      .filter((swing) => dates.has(String(swing?.date ?? "")))
      .map((swing) => ({
        ...swing,
        visibleIndex: dates.get(String(swing.date)),
      }));

    const visibleEvents = events
      .filter((event) => dates.has(String(event?.date ?? "")))
      .map((event) => ({
        ...event,
        visibleIndex: dates.get(String(event.date)),
      }));

    const visibleSweeps = liquiditySweeps
      .filter((sweep) => dates.has(String(sweep?.date ?? "")))
      .map((sweep) => ({
        ...sweep,
        visibleIndex: dates.get(String(sweep.date)),
      }))
      .sort(
        (a, b) =>
          Number(a?.display_priority || 0) -
          Number(b?.display_priority || 0)
      );

    const visibleClusters = sweepClusters
      .filter((cluster) =>
        dates.has(String(cluster?.last_event_date ?? ""))
      )
      .map((cluster) => ({
        ...cluster,
        visibleIndex: dates.get(
          String(cluster.last_event_date)
        ),
      }));

    const priceCandidates = rows.flatMap((row) => [
      row.high,
      row.low,
    ]);

    zones.forEach((zone) => {
      const lower = n(zone?.lower);
      const upper = n(zone?.upper);
      if (lower !== null) priceCandidates.push(lower);
      if (upper !== null) priceCandidates.push(upper);
    });

    liquidityPools.forEach((pool) => {
      [pool?.lower, pool?.upper, pool?.center].forEach((value) => {
        const price = n(value);
        if (price !== null) priceCandidates.push(price);
      });
    });

    visibleClusters.forEach((cluster) => {
      [cluster?.lower, cluster?.upper, cluster?.center].forEach((value) => {
        const price = n(value);
        if (price !== null) priceCandidates.push(price);
      });
    });

    [protectedHigh, protectedLow].forEach((level) => {
      const price = n(level?.price);
      if (price !== null) priceCandidates.push(price);
    });

    let minPrice = Math.min(...priceCandidates);
    let maxPrice = Math.max(...priceCandidates);
    const range = maxPrice - minPrice || Math.max(maxPrice * 0.03, 1);

    minPrice -= range * 0.08;
    maxPrice += range * 0.08;

    return {
      rows,
      zones,
      liquidityPools,
      visibleSwings,
      visibleEvents,
      visibleSweeps,
      visibleClusters,
      protectedHigh,
      protectedLow,
      minPrice,
      maxPrice,
    };
  }, [history, marketStructure, supportResistance, liquidity, viewBars]);

  if (!model) {
    return (
      <div className="qmi-ichart-empty">
        Waiting for enough OHLC history to render the institutional chart.
      </div>
    );
  }

  const {
    rows,
    zones,
    liquidityPools,
    visibleSwings,
    visibleEvents,
    visibleSweeps,
    visibleClusters,
    protectedHigh,
    protectedLow,
    minPrice,
    maxPrice,
  } = model;

  const latestEvent =
    visibleEvents.length > 0
      ? visibleEvents[visibleEvents.length - 1]
      : null;

  const latestSweep =
    visibleSweeps.length > 0
      ? visibleSweeps[visibleSweeps.length - 1]
      : null;

  const latestCluster =
    visibleClusters.length > 0
      ? visibleClusters[visibleClusters.length - 1]
      : null;

  const rankedZones = [...zones]
    .sort((a, b) => Number(b?.strength || 0) - Number(a?.strength || 0))
    .slice(0, 5);

  const recentSwingCutoff = Math.max(0, rows.length - 45);

  const toggleLayer = (key) => {
    setLayers((current) => ({
      ...current,
      [key]: !current[key],
    }));
  };

  const width = 1400;
  const height = 620;
  const pad = {
    top: 24,
    right: 78,
    bottom: 44,
    left: 18,
  };

  const innerWidth = width - pad.left - pad.right;
  const innerHeight = height - pad.top - pad.bottom;
  const step = innerWidth / rows.length;
  const candleWidth = Math.max(2.5, Math.min(8, step * 0.58));

  const xAt = (index) =>
    pad.left + step * index + step / 2;

  const yAt = (price) =>
    pad.top +
    ((maxPrice - price) / (maxPrice - minPrice)) *
      innerHeight;

  const last = rows[rows.length - 1];
  const gridPrices = Array.from({ length: 6 }, (_, index) => {
    const ratio = index / 5;
    return maxPrice - (maxPrice - minPrice) * ratio;
  });

  const labelIndexes = [
    0,
    Math.round((rows.length - 1) * 0.25),
    Math.round((rows.length - 1) * 0.5),
    Math.round((rows.length - 1) * 0.75),
    rows.length - 1,
  ];

  return (
    <div className="qmi-ichart">
      <div className="qmi-ichart__header">
        <div>
          <span>INSTITUTIONAL PRICE MAP</span>
          <strong>{rows.length} visible sessions</strong>
        </div>

        <div className="qmi-ichart__right">
          <div className="qmi-ichart__ohlc">
            <span>O {priceLabel(last.open)}</span>
            <span>H {priceLabel(last.high)}</span>
            <span>L {priceLabel(last.low)}</span>
            <span>C {priceLabel(last.close)}</span>
          </div>

          <div className="qmi-ichart__controls">
            <div className="qmi-ichart__range">
              {[
                { label: "3M", bars: 65 },
                { label: "6M", bars: 130 },
                { label: "1Y", bars: 252 },
              ].map((item) => (
                <button
                  type="button"
                  key={item.label}
                  className={viewBars === item.bars ? "is-active" : ""}
                  onClick={() => setViewBars(item.bars)}
                >
                  {item.label}
                </button>
              ))}
            </div>

            <div className="qmi-ichart__layers">
              {[
                ["zones", "Zones"],
                ["swings", "Structure"],
                ["events", "BOS/CHoCH"],
                ["protected", "Protected"],
                ["liquidity", "Liquidity"],
                ["sweeps", "Sweeps"],
                ["clusters", "Clusters"],
              ].map(([key, label]) => (
                <button
                  type="button"
                  key={key}
                  className={layers[key] ? "is-active" : ""}
                  onClick={() => toggleLayer(key)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="qmi-ichart__viewport">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="QMI institutional candlestick chart"
        >
          <rect
            x="0"
            y="0"
            width={width}
            height={height}
            className="qmi-ichart__background"
          />

          {gridPrices.map((price) => {
            const y = yAt(price);

            return (
              <g key={`grid-${price}`}>
                <line
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={y}
                  y2={y}
                  className="qmi-ichart__grid"
                />
                <text
                  x={width - pad.right + 10}
                  y={y + 4}
                  className="qmi-ichart__axis-label"
                >
                  {priceLabel(price)}
                </text>
              </g>
            );
          })}

          {layers.zones && rankedZones.map((zone, index) => {
            const lower = n(zone?.lower);
            const upper = n(zone?.upper);

            if (lower === null || upper === null) {
              return null;
            }

            const yTop = yAt(upper);
            const yBottom = yAt(lower);
            const zoneClass =
              zone.type === "SUPPORT"
                ? "is-support"
                : "is-resistance";

            return (
              <g key={`zone-${index}`}>
                <rect
                  x={pad.left}
                  y={yTop}
                  width={innerWidth}
                  height={Math.max(2, yBottom - yTop)}
                  className={`qmi-ichart__zone ${zoneClass}`}
                  style={{
                    opacity: Math.max(
                      0.35,
                      Math.min(0.95, Number(zone?.strength || 50) / 100)
                    )
                  }}
                >
                  <title>
                    {`${zone.type} ${priceLabel(lower)}–${priceLabel(upper)} · strength ${Number(zone?.strength || 0).toFixed(1)}/100 · ${zone?.touches || 0} touches`}
                  </title>
                </rect>
                <text
                  x={pad.left + 8}
                  y={yTop + 14}
                  className={`qmi-ichart__zone-label ${zoneClass}`}
                >
                  {zone.type} {priceLabel(lower)}–{priceLabel(upper)}
                </text>
              </g>
            );
          })}

          {layers.liquidity && liquidityPools.map((pool, index) => {
            const lower = n(pool?.lower);
            const upper = n(pool?.upper);
            const center = n(pool?.center);
            if (lower === null || upper === null || center === null) return null;

            const yTop = yAt(upper);
            const yBottom = yAt(lower);
            const yCenter = yAt(center);
            const isBsl = pool?.type === "BSL";
            const active = pool?.status === "ACTIVE";
            const score = Math.max(0, Math.min(100, Number(pool?.score || 0)));
            const opacity = active ? 0.22 + score / 500 : 0.10;

            return (
              <g
                key={`liquidity-${pool?.type}-${center}-${index}`}
                className={`qmi-ichart__liquidity ${
                  isBsl ? "is-bsl" : "is-ssl"
                } ${active ? "is-active" : "is-traversed"}`}
              >
                <rect
                  x={pad.left}
                  y={yTop}
                  width={innerWidth}
                  height={Math.max(3, yBottom - yTop)}
                  className="qmi-ichart__liquidity-band"
                  style={{ opacity }}
                />
                <line
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={yCenter}
                  y2={yCenter}
                  className="qmi-ichart__liquidity-line"
                />
                <text
                  x={width - pad.right - 8}
                  y={yCenter - 6}
                  textAnchor="end"
                  className="qmi-ichart__liquidity-label"
                >
                  {pool.type} · {priceLabel(center)} · {score.toFixed(0)}
                </text>
                <title>
                  {`${pool.side || pool.type} · ${pool.status || "--"} · ${priceLabel(lower)}–${priceLabel(upper)} · center ${priceLabel(center)} · score ${score.toFixed(1)}/100 · ${pool.touches || 0} touches · distance ${Number(pool.distance_pct || 0).toFixed(2)}%`}
                </title>
              </g>
            );
          })}

          {rows.map((row, index) => {
            const x = xAt(index);
            const yOpen = yAt(row.open);
            const yClose = yAt(row.close);
            const yHigh = yAt(row.high);
            const yLow = yAt(row.low);
            const bullish = row.close >= row.open;
            const bodyY = Math.min(yOpen, yClose);
            const bodyHeight = Math.max(
              1.8,
              Math.abs(yClose - yOpen)
            );

            return (
              <g
                key={`${row.date}-${index}`}
                className={
                  bullish
                    ? "qmi-ichart__candle is-up"
                    : "qmi-ichart__candle is-down"
                }
              >
                <title>
                  {`${row.date} · O ${priceLabel(row.open)} · H ${priceLabel(row.high)} · L ${priceLabel(row.low)} · C ${priceLabel(row.close)}`}
                </title>
                <line
                  x1={x}
                  x2={x}
                  y1={yHigh}
                  y2={yLow}
                  className="qmi-ichart__wick"
                />
                <rect
                  x={x - candleWidth / 2}
                  y={bodyY}
                  width={candleWidth}
                  height={bodyHeight}
                  rx="0.7"
                  className="qmi-ichart__body"
                />
              </g>
            );
          })}

          {layers.clusters && visibleClusters.map((cluster, index) => {
            const lower = n(cluster?.lower);
            const upper = n(cluster?.upper);
            const center = n(cluster?.center);

            if (
              lower === null ||
              upper === null ||
              center === null
            ) {
              return null;
            }

            const yTop = yAt(upper);
            const yBottom = yAt(lower);
            const yCenter = yAt(center);
            const x = xAt(cluster.visibleIndex);
            const isBsl = cluster?.type === "BSL";
            const score = Math.max(
              0,
              Math.min(
                100,
                Number(cluster?.cluster_score || 0)
              )
            );
            const highQuality =
              cluster?.cluster_quality === "VERY_HIGH" ||
              cluster?.cluster_quality === "HIGH";

            return (
              <g
                key={`cluster-${cluster.cluster_id || index}`}
                className={`qmi-ichart__cluster ${
                  isBsl ? "is-bsl" : "is-ssl"
                } ${highQuality ? "is-strong" : ""}`}
              >
                <rect
                  x={pad.left}
                  y={yTop}
                  width={innerWidth}
                  height={Math.max(4, yBottom - yTop)}
                  className="qmi-ichart__cluster-band"
                  style={{
                    opacity: 0.08 + score / 800,
                  }}
                />
                <line
                  x1={Math.max(pad.left, x - step * 5)}
                  x2={width - pad.right}
                  y1={yCenter}
                  y2={yCenter}
                  className="qmi-ichart__cluster-line"
                />
                <circle
                  cx={x}
                  cy={yCenter}
                  r={highQuality ? 5.5 : 4}
                  className="qmi-ichart__cluster-node"
                />
                <text
                  x={width - pad.right - 8}
                  y={yCenter - 7}
                  textAnchor="end"
                  className="qmi-ichart__cluster-label"
                >
                  {cluster.type} CLUSTER · {cluster.event_count}× · {score.toFixed(0)}
                </text>
                <title>
                  {`${cluster.type} cluster · ${cluster.first_event_date} → ${cluster.last_event_date} · ${priceLabel(lower)}–${priceLabel(upper)} · ${cluster.event_count} events · ${cluster.high_conviction_count || 0} high conviction · score ${score.toFixed(1)}/100 · ${cluster.cluster_quality} · ${cluster.directional_implication} implication`}
                </title>
              </g>
            );
          })}

          {layers.sweeps && visibleSweeps.map((sweep, index) => {
            const extreme = n(sweep?.extreme_price);
            if (extreme === null) return null;

            const x = xAt(sweep.visibleIndex);
            const y = yAt(extreme);
            const bullish =
              sweep?.directional_implication === "BULLISH";
            const isLatest =
              latestSweep &&
              latestSweep.date === sweep.date &&
              latestSweep.type === sweep.type &&
              Number(latestSweep.pool_center) === Number(sweep.pool_center);

            const rawScore = Math.max(
              0,
              Math.min(100, Number(sweep?.score || 0))
            );
            const institutionalScore = Math.max(
              0,
              Math.min(
                100,
                Number(sweep?.institutional_score ?? rawScore)
              )
            );
            const institutionalStatus = String(
              sweep?.institutional_status || "LEGACY"
            );
            const highConviction =
              institutionalStatus === "HIGH_CONVICTION";

            return (
              <g
                key={`sweep-${sweep.type}-${sweep.date}-${index}`}
                className={`qmi-ichart__sweep ${
                  bullish ? "is-bullish" : "is-bearish"
                } ${isLatest ? "is-latest" : ""} ${
                  highConviction ? "is-high-conviction" : "is-confirmed"
                }`}
                style={{
                  opacity: highConviction ? 1 : 0.78,
                }}
              >
                <circle
                  cx={x}
                  cy={y}
                  r={isLatest ? 6.5 : highConviction ? 5.5 : 4}
                  className="qmi-ichart__sweep-halo"
                />
                <path
                  d={
                    bullish
                      ? `M ${x - 5} ${y + 10} L ${x} ${y + 3} L ${x + 5} ${y + 10}`
                      : `M ${x - 5} ${y - 10} L ${x} ${y - 3} L ${x + 5} ${y - 10}`
                  }
                  className="qmi-ichart__sweep-arrow"
                />
                <text
                  x={x}
                  y={bullish ? y + 24 : y - 17}
                  textAnchor="middle"
                  className="qmi-ichart__sweep-label"
                >
                  {highConviction ? "★ " : ""}
                  {sweep.pool_type} · {institutionalScore.toFixed(0)}
                </text>
                <title>
                  {`${sweep.type} · ${sweep.date} · ${institutionalStatus} · institutional ${institutionalScore.toFixed(1)}/100 · raw ${rawScore.toFixed(1)}/100 · ${sweep.directional_implication} implication · pool ${priceLabel(sweep.pool_center)} · extreme ${priceLabel(sweep.extreme_price)} · close ${priceLabel(sweep.close_price)} · penetration ${Number(sweep.penetration_pct || 0).toFixed(2)}% · rejection ${Number(sweep.rejection_pct || 0).toFixed(2)}%`}
                </title>
              </g>
            );
          })}

          {layers.swings && visibleSwings.map((swing, index) => {
            const price = n(swing?.price);
            if (price === null) return null;

            const x = xAt(swing.visibleIndex);
            const y = yAt(price);
            const isHigh = swing.kind === "SWING_HIGH";

            return (
              <g key={`swing-${index}`}>
                <circle
                  cx={x}
                  cy={y}
                  r="3"
                  className={`qmi-ichart__swing-dot ${
                    isHigh ? "is-high" : "is-low"
                  }`}
                />
                {swing.visibleIndex >= recentSwingCutoff && (
                  <text
                    x={x}
                    y={isHigh ? y - 9 : y + 17}
                    textAnchor="middle"
                    className={`qmi-ichart__swing-label ${
                      isHigh ? "is-high" : "is-low"
                    }`}
                  >
                    {swing.label || ""}
                  </text>
                )}
                <title>
                  {`${swing.date} · ${swing.label || swing.kind} · ${priceLabel(price)}`}
                </title>
              </g>
            );
          })}

          {layers.events && visibleEvents.map((event, index) => {
            const x = xAt(event.visibleIndex);
            const level = n(event?.broken_level);
            if (level === null) return null;

            const y = yAt(level);
            const bullish = event.direction === "BULLISH";
            const isLatest =
              latestEvent &&
              latestEvent.date === event.date &&
              latestEvent.type === event.type;

            return (
              <g
                key={`event-${index}`}
                className={isLatest ? "is-latest-event" : ""}
              >
                <title>
                  {`${event.date} · ${event.type} · broken ${priceLabel(level)} · close ${priceLabel(event.confirmation_price)}`}
                </title>
                <line
                  x1={Math.max(pad.left, x - step * 3)}
                  x2={Math.min(width - pad.right, x + step * 1.5)}
                  y1={y}
                  y2={y}
                  className={`qmi-ichart__event-line ${
                    bullish ? "is-bullish" : "is-bearish"
                  } ${isLatest ? "is-latest" : ""}`}
                />
                <text
                  x={x}
                  y={y - 7}
                  textAnchor="middle"
                  className={`qmi-ichart__event-label ${
                    bullish ? "is-bullish" : "is-bearish"
                  } ${isLatest ? "is-latest" : ""}`}
                >
                  {bullish ? "▲" : "▼"} {eventLabel(event.type)}
                </text>
              </g>
            );
          })}

          {layers.protected && [
            {
              data: protectedHigh,
              label: "PROTECTED HIGH",
              className: "is-high",
            },
            {
              data: protectedLow,
              label: "PROTECTED LOW",
              className: "is-low",
            },
          ].map(({ data, label, className }) => {
            const price = n(data?.price);
            if (price === null) return null;
            const y = yAt(price);

            return (
              <g key={label}>
                <line
                  x1={pad.left}
                  x2={width - pad.right}
                  y1={y}
                  y2={y}
                  className={`qmi-ichart__protected ${className}`}
                />
                <text
                  x={width - pad.right - 8}
                  y={y - 6}
                  textAnchor="end"
                  className={`qmi-ichart__protected-label ${className}`}
                >
                  {label} · {priceLabel(price)}
                </text>
              </g>
            );
          })}

          <line
            x1={pad.left}
            x2={width - pad.right}
            y1={yAt(last.close)}
            y2={yAt(last.close)}
            className="qmi-ichart__last-price"
          />

          <text
            x={width - pad.right + 10}
            y={yAt(last.close) + 4}
            className="qmi-ichart__last-price-label"
          >
            {priceLabel(last.close)}
          </text>

          {labelIndexes.map((index) => (
            <text
              key={`date-${index}`}
              x={xAt(index)}
              y={height - 14}
              textAnchor="middle"
              className="qmi-ichart__date-label"
            >
              {String(rows[index]?.date ?? "").slice(5)}
            </text>
          ))}
        </svg>
      </div>

      {latestCluster && (
        <div
          className={`qmi-ichart__latest-cluster ${
            latestCluster.directional_implication === "BULLISH"
              ? "is-bullish"
              : "is-bearish"
          }`}
        >
          <span>Latest liquidity cluster</span>
          <strong>
            {latestCluster.type} · {latestCluster.event_count} events
          </strong>
          <small>
            {latestCluster.first_event_date} → {latestCluster.last_event_date} ·
            {" "}range {priceLabel(latestCluster.lower)}–{priceLabel(latestCluster.upper)} ·
            {" "}score {Number(latestCluster.cluster_score || 0).toFixed(1)}/100 ·
            {" "}{latestCluster.cluster_quality}
          </small>
        </div>
      )}

      {latestSweep && (
        <div
          className={`qmi-ichart__latest-sweep ${
            latestSweep.directional_implication === "BULLISH"
              ? "is-bullish"
              : "is-bearish"
          }`}
        >
          <span>Latest institutional sweep</span>
          <strong>
            {latestSweep.institutional_status === "HIGH_CONVICTION" ? "★ " : ""}
            {latestSweep.pool_type} SWEEP
          </strong>
          <small>
            {latestSweep.date} · pool {priceLabel(latestSweep.pool_center)} ·
            {" "}institutional {Number(
              latestSweep.institutional_score ?? latestSweep.score ?? 0
            ).toFixed(1)}/100 ·
            {" "}{latestSweep.institutional_status || "CONFIRMED"} ·
            {" "}{latestSweep.directional_implication} implication
          </small>
        </div>
      )}

      {latestEvent && (
        <div
          className={`qmi-ichart__latest-event ${
            latestEvent.direction === "BULLISH"
              ? "is-bullish"
              : "is-bearish"
          }`}
        >
          <span>Latest structural event</span>
          <strong>{eventLabel(latestEvent.type)}</strong>
          <small>
            {latestEvent.date} · broken {priceLabel(latestEvent.broken_level)}
          </small>
        </div>
      )}

      <div className="qmi-ichart__legend">
        <span><i className="is-support" /> Support zone</span>
        <span><i className="is-resistance" /> Resistance zone</span>
        <span><i className="is-protected" /> Protected structure</span>
        <span><i className="is-bsl" /> BSL liquidity</span>
        <span><i className="is-ssl" /> SSL liquidity</span>
        <span><i className="is-sweep" /> Institutional sweep</span>
        <span><i className="is-cluster" /> Sweep cluster</span>
        <span>HH/HL/LH/LL = confirmed swings</span>
        <span>BOS/CHoCH = close-confirmed events</span>
      </div>
    </div>
  );
}

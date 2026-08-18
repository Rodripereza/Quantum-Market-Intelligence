import { apiRequest } from "./api";

/* =========================================================
   QMI — PORTFOLIO SERVICE
   Backend contract adapter
   Sprint 008
   ========================================================= */

function toNumber(value, fallback = 0) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : fallback;
}

function normalizePosition(position) {
  const shares = toNumber(
    position?.shares ?? position?.quantity
  );

  const averagePrice = toNumber(
    position?.average_price
  );

  /*
   * El backend actual todavía no persiste current_price.
   * Hasta conectar Portfolio con Market Data Engine,
   * utilizamos average_price como precio operativo.
   */
  const currentPrice = toNumber(
    position?.current_price ??
      position?.price ??
      averagePrice
  );

  const value = shares * currentPrice;
  const cost = shares * averagePrice;
  const pl = value - cost;

  const plPct =
    cost > 0
      ? (pl / cost) * 100
      : 0;

  return {
    ...position,

    /*
     * Compatibilidad con el frontend actual.
     */
    quantity: shares,
    shares,

    average_price: averagePrice,
    current_price: currentPrice,

    value,
    cost,
    pl,
    pl_pct: plPct,

    sector:
      position?.sector ||
      "Unclassified",

    company:
      position?.company ||
      position?.ticker ||
      "",

    currency:
      position?.currency ||
      "USD",

    notes:
      position?.notes ||
      "",
  };
}

function normalizePortfolio(response) {
  const rawPositions = Array.isArray(response)
    ? response
    : response?.positions || [];

  const basePositions =
    rawPositions.map(normalizePosition);

  const totalValue =
    basePositions.reduce(
      (sum, position) =>
        sum + position.value,
      0
    );

  const totalCost =
    basePositions.reduce(
      (sum, position) =>
        sum + position.cost,
      0
    );

  const totalPl =
    totalValue - totalCost;

  const totalPlPct =
    totalCost > 0
      ? (totalPl / totalCost) * 100
      : 0;

  const positions =
    basePositions.map((position) => ({
      ...position,

      weight:
        totalValue > 0
          ? (position.value / totalValue) * 100
          : 0,
    }));

  const sectorMap = new Map();

  positions.forEach((position) => {
    const sector =
      position.sector ||
      "Unclassified";

    const previous =
      sectorMap.get(sector) || 0;

    sectorMap.set(
      sector,
      previous + position.value
    );
  });

  const sectorAllocation =
    Array.from(
      sectorMap.entries()
    ).map(([sector, value]) => ({
      sector,
      value,

      weight:
        totalValue > 0
          ? (value / totalValue) * 100
          : 0,
    }));

  const largestPositionWeight =
    positions.length > 0
      ? Math.max(
          ...positions.map(
            (position) => position.weight
          )
        )
      : 0;

  return {
    positions,

    total_value: totalValue,
    total_cost: totalCost,

    total_pl: totalPl,
    total_pl_pct: totalPlPct,

    largest_position_weight:
      largestPositionWeight,

    sector_allocation:
      sectorAllocation,
  };
}

function buildBackendPayload(position) {
  return {
    ticker:
      String(position?.ticker || "")
        .trim()
        .toUpperCase(),

    company:
      String(
        position?.company ||
          position?.ticker ||
          ""
      ).trim(),

    /*
     * El frontend todavía llama al campo "quantity".
     * El backend actual utiliza "shares".
     */
    shares: toNumber(
      position?.shares ??
        position?.quantity
    ),

    average_price: toNumber(
      position?.average_price
    ),

    currency:
      position?.currency ||
      "USD",

    sector:
      position?.sector ||
      "Unclassified",

    notes:
      position?.notes ||
      "",
  };
}

/* =========================================================
   READ
   ========================================================= */

export async function getPortfolio(token) {
  const response =
    await apiRequest(
      "/api/portfolio/",
      {
        token,
      }
    );

  return normalizePortfolio(response);
}

/* =========================================================
   CREATE
   ========================================================= */

export async function createPosition(
  token,
  position
) {
  await apiRequest(
    "/api/portfolio/",
    {
      method: "POST",
      token,
      body: buildBackendPayload(position),
    }
  );

  /*
   * Volvemos a consultar Portfolio para mantener
   * sincronizado el frontend con SQLite.
   */
  const portfolio =
    await getPortfolio(token);

  return {
    portfolio,
  };
}

/* =========================================================
   UPDATE
   ========================================================= */

export async function updatePosition(
  token,
  positionId,
  position
) {
  await apiRequest(
    `/api/portfolio/${positionId}`,
    {
      method: "PUT",
      token,
      body: buildBackendPayload(position),
    }
  );

  const portfolio =
    await getPortfolio(token);

  return {
    portfolio,
  };
}

/* =========================================================
   DELETE
   ========================================================= */

export async function deletePosition(
  token,
  positionId
) {
  await apiRequest(
    `/api/portfolio/${positionId}`,
    {
      method: "DELETE",
      token,
    }
  );

  const portfolio =
    await getPortfolio(token);

  return {
    portfolio,
  };
}
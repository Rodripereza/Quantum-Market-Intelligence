import { apiRequest } from "./api";

/* =========================================================
   QMI — PORTFOLIO SERVICE
   Sprint 008 · Live Valuation + Historical Performance
   ========================================================= */

function toNumber(value, fallback = 0) {
  const number = Number(value);

  return Number.isFinite(number)
    ? number
    : fallback;
}

function normalizePosition(position, totalValue = 0) {
  const shares = toNumber(
    position?.shares ?? position?.quantity
  );

  const averagePrice = toNumber(
    position?.average_price
  );

  const currentPrice = toNumber(
    position?.current_price ??
      position?.price ??
      averagePrice
  );

  const costBasis = toNumber(
    position?.cost_basis,
    shares * averagePrice
  );

  const marketValue = toNumber(
    position?.market_value ??
      position?.value,
    shares * currentPrice
  );

  const unrealizedPl = toNumber(
    position?.unrealized_pl ??
      position?.pl,
    marketValue - costBasis
  );

  const unrealizedPlPct =
    position?.unrealized_pl_pct !== undefined
      ? toNumber(position.unrealized_pl_pct)
      : position?.pl_pct !== undefined
        ? toNumber(position.pl_pct)
        : costBasis > 0
          ? (unrealizedPl / costBasis) * 100
          : 0;

  const weight =
    position?.weight !== undefined
      ? toNumber(position.weight)
      : totalValue > 0
        ? (marketValue / totalValue) * 100
        : 0;

  return {
    ...position,

    quantity: shares,
    shares,

    average_price: averagePrice,
    current_price: currentPrice,

    cost_basis: costBasis,
    cost: costBasis,

    market_value: marketValue,
    value: marketValue,

    unrealized_pl: unrealizedPl,
    pl: unrealizedPl,

    unrealized_pl_pct: unrealizedPlPct,
    pl_pct: unrealizedPlPct,

    weight,

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

function normalizeSectorAllocation(
  allocation,
  totalValue
) {
  if (!Array.isArray(allocation)) {
    return [];
  }

  return allocation.map((item) => {
    const value = toNumber(item?.value);

    const weight =
      item?.weight !== undefined
        ? toNumber(item.weight)
        : totalValue > 0
          ? (value / totalValue) * 100
          : 0;

    return {
      ...item,
      sector:
        item?.sector ||
        item?.label ||
        "Unclassified",
      value,
      weight,
    };
  });
}

function normalizePortfolio(response) {
  if (
    response &&
    !Array.isArray(response) &&
    Array.isArray(response.positions)
  ) {
    const totalValue = toNumber(
      response.total_value
    );

    const positions =
      response.positions.map((position) =>
        normalizePosition(
          position,
          totalValue
        )
      );

    const totalCost = toNumber(
      response.total_cost,
      positions.reduce(
        (sum, position) =>
          sum + position.cost_basis,
        0
      )
    );

    const totalPl = toNumber(
      response.total_pl,
      totalValue - totalCost
    );

    const totalPlPct =
      response.total_pl_pct !== undefined
        ? toNumber(response.total_pl_pct)
        : totalCost > 0
          ? (totalPl / totalCost) * 100
          : 0;

    const largestPositionWeight =
      response.largest_position_weight !== undefined
        ? toNumber(
            response.largest_position_weight
          )
        : positions.length > 0
          ? Math.max(
              ...positions.map(
                (position) =>
                  position.weight
              )
            )
          : 0;

    return {
      ...response,

      positions,

      total_value: totalValue,
      total_cost: totalCost,

      total_pl: totalPl,
      total_pl_pct: totalPlPct,

      largest_position_weight:
        largestPositionWeight,

      sector_allocation:
        normalizeSectorAllocation(
          response.sector_allocation,
          totalValue
        ),
    };
  }

  const rawPositions = Array.isArray(response)
    ? response
    : [];

  const preliminaryPositions =
    rawPositions.map((position) =>
      normalizePosition(position)
    );

  const totalValue =
    preliminaryPositions.reduce(
      (sum, position) =>
        sum + position.market_value,
      0
    );

  const positions =
    preliminaryPositions.map((position) => ({
      ...position,
      weight:
        totalValue > 0
          ? (
              position.market_value /
              totalValue
            ) * 100
          : 0,
    }));

  const totalCost =
    positions.reduce(
      (sum, position) =>
        sum + position.cost_basis,
      0
    );

  const totalPl =
    totalValue - totalCost;

  const totalPlPct =
    totalCost > 0
      ? (totalPl / totalCost) * 100
      : 0;

  const sectorMap = new Map();

  positions.forEach((position) => {
    const sector =
      position.sector ||
      "Unclassified";

    sectorMap.set(
      sector,
      (sectorMap.get(sector) || 0) +
        position.market_value
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

  return {
    positions,

    total_value: totalValue,
    total_cost: totalCost,

    total_pl: totalPl,
    total_pl_pct: totalPlPct,

    largest_position_weight:
      positions.length > 0
        ? Math.max(
            ...positions.map(
              (position) =>
                position.weight
            )
          )
        : 0,

    sector_allocation:
      sectorAllocation,
  };
}

function normalizeHistory(response) {
  if (!response) {
    return {
      period: "",
      interval: "",
      currency: "USD",
      positions: 0,
      history: [],
      summary: {
        start_value: 0,
        end_value: 0,
        absolute_return: 0,
        return_pct: 0,
        max_value: 0,
        min_value: 0,
        observations: 0,
      },
    };
  }

  const history = Array.isArray(response.history)
    ? response.history.map((point) => ({
        date: point?.date ?? "",
        market_value: toNumber(
          point?.market_value
        ),
        cost_basis: toNumber(
          point?.cost_basis
        ),
        profit_loss: toNumber(
          point?.profit_loss
        ),
        return_pct: toNumber(
          point?.return_pct
        ),
      }))
    : [];

  const summary = response.summary ?? {};

  return {
    ...response,

    currency:
      response.currency ||
      "USD",

    positions:
      toNumber(response.positions),

    history,

    summary: {
      start_value: toNumber(
        summary.start_value
      ),
      end_value: toNumber(
        summary.end_value
      ),
      absolute_return: toNumber(
        summary.absolute_return
      ),
      return_pct: toNumber(
        summary.return_pct
      ),
      max_value: toNumber(
        summary.max_value
      ),
      min_value: toNumber(
        summary.min_value
      ),
      observations: toNumber(
        summary.observations
      ),
    },
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
   PORTFOLIO SNAPSHOT
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
   PORTFOLIO HISTORY
   ========================================================= */

export async function getPortfolioHistory(
  token,
  period = "1y",
  interval = "1d"
) {
  const normalizedPeriod =
    encodeURIComponent(period);

  const normalizedInterval =
    encodeURIComponent(interval);

  const response =
    await apiRequest(
      `/api/portfolio/history?period=${normalizedPeriod}&interval=${normalizedInterval}`,
      {
        token,
      }
    );

  return normalizeHistory(response);
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
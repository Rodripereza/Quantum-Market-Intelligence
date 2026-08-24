import { apiRequest } from "./api";

export async function getTechnicalAnalysis(
  symbol,
  {
    period = "1y",
    interval = "1d",
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval
  });

  return apiRequest(
    `/api/technical/${encodeURIComponent(normalizedSymbol)}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}

export default getTechnicalAnalysis;

export async function getMarketStructure(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    maxSwings = 20,
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval,
    pivot_window: String(pivotWindow),
    max_swings: String(maxSwings)
  });

  return apiRequest(
    `/api/technical/market-structure/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}

export async function getSupportResistance(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    minTouches = 2,
    maxZones = 6,
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval,
    pivot_window: String(pivotWindow),
    min_touches: String(minTouches),
    max_zones: String(maxZones)
  });

  return apiRequest(
    `/api/technical/support-resistance/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}

export async function getTechnicalMarketHistory(
  symbol,
  {
    period = "1y",
    interval = "1d",
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval
  });

  return apiRequest(
    `/api/market/history/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}


export async function getLiquidity(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    tolerancePct = 0.6,
    minTouches = 2,
    maxPools = 8,
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval,
    pivot_window: String(pivotWindow),
    tolerance_pct: String(tolerancePct),
    min_touches: String(minTouches),
    max_pools: String(maxPools)
  });

  return apiRequest(
    `/api/technical/liquidity/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}


export async function getTechnicalConfluence(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval,
    pivot_window: String(pivotWindow)
  });

  return apiRequest(
    `/api/technical/confluence/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}


export async function getTechnicalDecision(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    token = "",
    signal
  } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  const query = new URLSearchParams({
    period,
    interval,
    pivot_window: String(pivotWindow)
  });

  return apiRequest(
    `/api/technical/decision/${encodeURIComponent(
      normalizedSymbol
    )}?${query.toString()}`,
    {
      token,
      signal
    }
  );
}

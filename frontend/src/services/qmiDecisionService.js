import { apiRequest } from "./api";

export async function getQMIDecision(
  symbol,
  {
    period = "1y",
    interval = "1d",
    pivotWindow = 3,
    historyLimit = 500,
    token = "",
    signal,
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
    history_limit: String(historyLimit),
  });

  return apiRequest(
    `/api/qmi/decision/${encodeURIComponent(normalizedSymbol)}?${query.toString()}`,
    {
      token,
      signal,
    }
  );
}

export default getQMIDecision;
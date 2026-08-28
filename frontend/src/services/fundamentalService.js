import { apiRequest } from "./api";

export async function getFundamental(
  symbol,
  { token = "", signal } = {}
) {
  const normalizedSymbol = String(symbol || "")
    .trim()
    .toUpperCase();

  if (!normalizedSymbol) {
    throw new Error("A ticker symbol is required");
  }

  return apiRequest(
    `/api/fundamental/${encodeURIComponent(normalizedSymbol)}`,
    {
      token,
      signal,
    }
  );
}
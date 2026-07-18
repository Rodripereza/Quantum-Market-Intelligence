import { apiRequest } from "./api";

export async function getMarket(token) {
  return apiRequest("/api/market", {
    token
  });
}
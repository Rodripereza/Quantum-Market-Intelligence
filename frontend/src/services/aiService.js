import { apiRequest } from "./api";

export async function getAIStatus(token) {
  return apiRequest("/api/ai/status", {
    token
  });
}
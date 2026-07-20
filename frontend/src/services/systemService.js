import { apiRequest } from "./api";

export async function getHealth() {
  return apiRequest("/health");
}
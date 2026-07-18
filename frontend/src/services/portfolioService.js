import { apiRequest } from "./api";

export async function getPortfolio(token) {
  return apiRequest("/api/portfolio", {
    token
  });
}

export async function createPosition(token, position) {
  return apiRequest("/api/portfolio/positions", {
    method: "POST",
    token,
    body: position
  });
}

export async function updatePosition(
  token,
  positionId,
  position
) {
  return apiRequest(
    `/api/portfolio/positions/${positionId}`,
    {
      method: "PUT",
      token,
      body: position
    }
  );
}

export async function deletePosition(token, positionId) {
  return apiRequest(
    `/api/portfolio/positions/${positionId}`,
    {
      method: "DELETE",
      token
    }
  );
}
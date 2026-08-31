import { apiRequest } from "./api";

export async function getNioDeliveries(
  { token = "", signal } = {}
) {
  return apiRequest(
    "/api/company-intelligence/nio/deliveries",
    {
      token,
      signal,
    }
  );
}

export default getNioDeliveries;
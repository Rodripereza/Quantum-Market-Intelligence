const API_BASE_URL = "http://127.0.0.1:8000";

function buildHeaders(token, customHeaders = {}) {
  const headers = {
    ...customHeaders
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

async function parseResponse(response) {
  // 204 No Content (por ejemplo DELETE correcto) no tiene cuerpo.
  // No debemos intentar ejecutar response.json() sobre una respuesta vacía.
  if (response.status === 204) {
    return null;
  }

  const contentType = response.headers.get("content-type") || "";
  const rawText = await response.text();

  let data = null;

  if (rawText) {
    if (contentType.includes("application/json")) {
      try {
        data = JSON.parse(rawText);
      } catch {
        data = rawText;
      }
    } else {
      data = rawText;
    }
  }

  if (!response.ok) {
    const error = new Error(
      data?.detail ||
        data?.message ||
        `Request failed with status ${response.status}`
    );

    error.status = response.status;
    error.data = data;

    throw error;
  }

  return data;
}

export async function apiRequest(
  endpoint,
  {
    method = "GET",
    token = "",
    body,
    headers = {},
    signal
  } = {}
) {
  const requestHeaders = buildHeaders(token, headers);

  const requestOptions = {
    method,
    headers: requestHeaders,
    signal
  };

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
    requestOptions.body = JSON.stringify(body);
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    requestOptions
  );

  return parseResponse(response);
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export default apiRequest;
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
  const contentType = response.headers.get("content-type") || "";

  let data = null;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = text || null;
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
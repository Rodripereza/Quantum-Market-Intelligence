import { apiRequest } from "./api";

export async function login(email, password) {
  return apiRequest("/api/auth/login", {
    method: "POST",
    body: {
      email,
      password
    }
  });
}

export async function logout(token) {
  return apiRequest("/api/auth/logout", {
    method: "POST",
    token
  });
}

export async function getUser(token) {
  return apiRequest("/api/user", {
    token
  });
}
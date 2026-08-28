import { createContext, useContext } from "react";

const API = "http://127.0.0.1:8001";

export const AuthContext = createContext(null);

export function apiFetch(path, options = {}) {
  const token = sessionStorage.getItem("atmograph_token");
  return fetch(`${API}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}

export function useAuth() {
  return useContext(AuthContext);
}

export { API };

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";

const AuthContext = createContext(null);

const TOKEN_KEY = "rag_token";
const USER_KEY = "rag_user";

const envUrl = import.meta.env.VITE_API_URL;
const API_URL = (envUrl && envUrl !== "undefined") ? envUrl.replace(/\/+$/, "") : "";

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem(USER_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  // Verify token on mount
  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    fetch(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Invalid token");
        return res.json();
      })
      .then((data) => {
        setUser(data);
        localStorage.setItem(USER_KEY, JSON.stringify(data));
      })
      .catch(() => {
        // Token expired or invalid
        setToken(null);
        setUser(null);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
      })
      .finally(() => setLoading(false));
  }, [token]);

  const login = useCallback(async (email, password) => {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed.");
    }
    const data = await res.json().catch(() => {
      throw new Error("Received malformed response from the server.");
    });
    setToken(data.access_token);
    setUser({ username: data.username, email: data.email });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(
      USER_KEY,
      JSON.stringify({ username: data.username, email: data.email }),
    );
    return data;
  }, []);

  const register = useCallback(async (username, email, password) => {
    const res = await fetch(`${API_URL}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Registration failed.");
    }
    const data = await res.json().catch(() => {
      throw new Error("Received malformed response from the server.");
    });
    setToken(data.access_token);
    setUser({ username: data.username, email: data.email });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(
      USER_KEY,
      JSON.stringify({ username: data.username, email: data.email }),
    );
    return data;
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }, []);

  // Helper to get auth headers for API calls
  const authFetch = useCallback(
    async (url, options = {}) => {
      const headers = {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      };
      const res = await fetch(`${API_URL}${url}`, { ...options, headers });
      if (res.status === 401) {
        logout();
        throw new Error("Session expired. Please log in again.");
      }
      return res;
    },
    [token, logout],
  );

  return (
    <AuthContext.Provider
      value={{ token, user, loading, login, register, logout, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchCurrentUser, loginRequest } from "../api/auth";
import { getStoredToken, setStoredToken, setUnauthorizedHandler } from "../api/client";
import type { User } from "../types";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [loading, setLoading] = useState(() => Boolean(getStoredToken()));

  const logout = useCallback(() => {
    setStoredToken(null);
    setToken(null);
    setUser(null);
    setLoading(false);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

  useEffect(() => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    fetchCurrentUser()
      .then((me) => {
        if (!cancelled) {
          setUser(me);
        }
      })
      .catch(() => {
        if (!cancelled) {
          logout();
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token, logout]);

  const login = useCallback(async (email: string, password: string) => {
    const result = await loginRequest(email, password);
    setStoredToken(result.access_token);
    setToken(result.access_token);
    setUser(result.user);
  }, []);

  const value = useMemo(
    () => ({ user, token, loading, login, logout }),
    [user, token, loading, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

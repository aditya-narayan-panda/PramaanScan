import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { adminLogin, getMe, institutionLogin } from "@/api/auth";
import { AUTH_EXPIRED_EVENT, REFRESH_TOKEN_STORAGE_KEY, TOKEN_STORAGE_KEY, apiClient } from "@/api/client";
import type { User, UserRole } from "@/api/types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, role: UserRole) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_STORAGE_KEY)
  );
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const logout = useCallback(async () => {
    // Try server-side refresh token revocation before clearing local state
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
    try {
      if (refreshToken) {
        // Fire-and-forget: send refresh_token so backend can revoke its JTI
        await apiClient.post("/auth/logout", { refresh_token: refreshToken }).catch(() => {});
      } else {
        await apiClient.post("/auth/logout").catch(() => {});
      }
    } catch {
      // Ignore — still log out locally even if backend is unreachable
    }
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(REFRESH_TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function hydrate() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      setIsLoading(true);
      try {
        const me = await getMe();
        if (!cancelled) setUser(me);
      } catch {
        if (!cancelled) {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    hydrate();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    const handleExpired = () => logout();
    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired);
  }, [logout]);

  const login = useCallback(async (email: string, password: string, role: UserRole) => {
    const { access_token, refresh_token } = await (role === "ADMIN"
      ? adminLogin({ email, password })
      : institutionLogin({ email, password }));
    localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refresh_token);
    setToken(access_token);
    const me = await getMe();
    setUser(me);
    return me;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      logout,
    }),
    [user, token, isLoading, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

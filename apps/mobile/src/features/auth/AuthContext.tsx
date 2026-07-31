import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  apiRequest,
  ApiError,
  type AuthResponse,
  type TokenPair,
  type User,
} from "@/services/api";
import {
  clearSession,
  readSession,
  type StoredSession,
  writeSession,
} from "@/services/session-storage";

type RegisterInput = {
  email: string;
  password: string;
  full_name: string;
};

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login(email: string, password: string): Promise<void>;
  register(input: RegisterInput): Promise<void>;
  logout(): Promise<void>;
  authenticatedRequest<T>(path: string, options?: RequestInit): Promise<T>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, setSession] = useState<StoredSession | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    readSession()
      .then(setSession)
      .finally(() => setIsLoading(false));
  }, []);

  const persist = useCallback(async (auth: AuthResponse) => {
    const next = { user: auth.user, tokens: auth.tokens };
    await writeSession(next);
    setSession(next);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const auth = await apiRequest<AuthResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
          device_name: "Aplicación móvil",
        }),
      });
      await persist(auth);
    },
    [persist],
  );

  const register = useCallback(
    async (input: RegisterInput) => {
      const auth = await apiRequest<AuthResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          ...input,
          country_code: "CO",
          timezone: "America/Bogota",
          default_currency: "COP",
          device_name: "Aplicación móvil",
        }),
      });
      await persist(auth);
    },
    [persist],
  );

  const logout = useCallback(async () => {
    const current = session;
    try {
      if (current) {
        await apiRequest<void>("/auth/logout", {
          method: "POST",
          body: JSON.stringify({ refresh_token: current.tokens.refresh_token }),
        });
      }
    } finally {
      await clearSession();
      setSession(null);
    }
  }, [session]);

  const authenticatedRequest = useCallback(
    async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
      if (!session) throw new ApiError("Authentication required", 401);
      try {
        return await apiRequest<T>(path, options, session.tokens.access_token);
      } catch (reason) {
        if (!(reason instanceof ApiError) || reason.status !== 401) throw reason;
      }

      try {
        const tokens = await apiRequest<TokenPair>("/auth/refresh", {
          method: "POST",
          body: JSON.stringify({ refresh_token: session.tokens.refresh_token }),
        });
        const next = { user: session.user, tokens };
        await writeSession(next);
        setSession(next);
        return await apiRequest<T>(path, options, tokens.access_token);
      } catch (reason) {
        await clearSession();
        setSession(null);
        throw reason;
      }
    },
    [session],
  );

  const value = useMemo(
    () => ({
      user: session?.user ?? null,
      isLoading,
      login,
      register,
      logout,
      authenticatedRequest,
    }),
    [authenticatedRequest, isLoading, login, logout, register, session?.user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}

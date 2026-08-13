import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { apiFetch, clearTokens, getAccessToken, login as apiLogin } from '../lib/api';

interface CurrentUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  roles: string[];
}

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadUser() {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await apiFetch<CurrentUser>('/auth/me');
      setUser(me);
    } catch {
      clearTokens();
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email: string, password: string) {
    await apiLogin(email, password);
    await loadUser();
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  function hasRole(...roles: string[]) {
    if (!user) return false;
    return user.roles.some((r) => roles.includes(r));
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
}

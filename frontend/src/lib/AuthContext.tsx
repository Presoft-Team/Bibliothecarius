import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { meApi } from "./resources";
import type { CurrentUser } from "./types";

interface AuthContextValue {
  currentUser: CurrentUser | null;
  loading: boolean;
}

const AuthContext = createContext<AuthContextValue>({ currentUser: null, loading: true });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    meApi
      .get()
      .then(setCurrentUser)
      .catch(() => setCurrentUser(null))
      .finally(() => setLoading(false));
  }, []);

  return <AuthContext.Provider value={{ currentUser, loading }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

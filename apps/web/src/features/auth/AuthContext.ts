import { createContext } from "react";

import type { AuthSession } from "./types";

export interface AuthContextValue {
  isLoading: boolean;
  session: AuthSession;
  hasCapability: (capabilityKey: string) => boolean;
  reloadSession: () => Promise<void>;
  startSignIn: (email: string, returnTo?: string | null) => Promise<void>;
  signOut: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

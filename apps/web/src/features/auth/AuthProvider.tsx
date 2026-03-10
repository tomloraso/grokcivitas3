import { useEffect, useRef, useState, type ReactNode } from "react";

import {
  getSession,
  resetApiRequestCache,
  setApiAccessEpoch,
  signOut as signOutRequest,
  startSignIn as startSignInRequest,
} from "../../api/client";
import { AuthContext } from "./AuthContext";
import { ANONYMOUS_SESSION, mapSessionResponse, type AuthSession } from "./types";

interface AuthProviderProps {
  children: ReactNode;
  autoLoad?: boolean;
  initialSession?: AuthSession;
}

export function AuthProvider({
  children,
  autoLoad = true,
  initialSession = ANONYMOUS_SESSION,
}: AuthProviderProps): JSX.Element {
  const [session, setSession] = useState<AuthSession>(initialSession);
  const [isLoading, setIsLoading] = useState(autoLoad);
  const sessionRef = useRef<AuthSession>(initialSession);

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  function applySession(nextSession: AuthSession): void {
    setApiAccessEpoch(nextSession.accessEpoch);
    if (!areSessionsEqual(sessionRef.current, nextSession)) {
      resetApiRequestCache();
    }
    sessionRef.current = nextSession;
    setSession(nextSession);
  }

  useEffect(() => {
    if (!autoLoad) {
      return;
    }

    let isCancelled = false;

    const loadSession = async (): Promise<void> => {
      setIsLoading(true);
      try {
        const nextSession = mapSessionResponse(await getSession());
        if (!isCancelled) {
          applySession(nextSession);
        }
      } catch {
        if (!isCancelled) {
          applySession(ANONYMOUS_SESSION);
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadSession();

    return () => {
      isCancelled = true;
    };
  }, [autoLoad]);

  async function reloadSession(): Promise<void> {
    setIsLoading(true);
    try {
      applySession(mapSessionResponse(await getSession()));
    } catch {
      applySession(ANONYMOUS_SESSION);
    } finally {
      setIsLoading(false);
    }
  }

  async function startSignIn(email: string, returnTo?: string | null): Promise<void> {
    setIsLoading(true);
    try {
      const result = await startSignInRequest({
        email,
        returnTo: returnTo ?? undefined,
      });
      resetApiRequestCache();
      globalThis.location.assign(result.redirect_url);
    } finally {
      setIsLoading(false);
    }
  }

  async function signOut(): Promise<void> {
    setIsLoading(true);
    try {
      applySession(mapSessionResponse(await signOutRequest()));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        isLoading,
        session,
        hasCapability: (capabilityKey: string) =>
          session.capabilityKeys.includes(capabilityKey),
        reloadSession,
        startSignIn,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

function areSessionsEqual(left: AuthSession, right: AuthSession): boolean {
  return (
    left.state === right.state &&
    left.expiresAt === right.expiresAt &&
    left.anonymousReason === right.anonymousReason &&
    left.accessEpoch === right.accessEpoch &&
    left.user?.id === right.user?.id &&
    left.user?.email === right.user?.email
  );
}

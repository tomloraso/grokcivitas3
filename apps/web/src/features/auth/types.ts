import type { SessionResponse } from "../../api/types";

export interface AuthUser {
  id: string;
  email: string;
}

export interface AuthSession {
  state: SessionResponse["state"];
  user: AuthUser | null;
  expiresAt: string | null;
  anonymousReason: SessionResponse["anonymous_reason"];
}

export const ANONYMOUS_SESSION: AuthSession = {
  state: "anonymous",
  user: null,
  expiresAt: null,
  anonymousReason: "missing",
};

export function mapSessionResponse(session: SessionResponse): AuthSession {
  return {
    state: session.state,
    user: session.user
      ? {
          id: session.user.id,
          email: session.user.email,
        }
      : null,
    expiresAt: session.expires_at,
    anonymousReason: session.anonymous_reason,
  };
}

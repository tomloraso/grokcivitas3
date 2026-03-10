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
  accountAccessState: SessionResponse["account_access_state"];
  capabilityKeys: string[];
  accessEpoch: string;
}

export const ANONYMOUS_SESSION: AuthSession = {
  state: "anonymous",
  user: null,
  expiresAt: null,
  anonymousReason: "missing",
  accountAccessState: "anonymous",
  capabilityKeys: [],
  accessEpoch: "anonymous:none",
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
    accountAccessState: session.account_access_state,
    capabilityKeys: [...session.capability_keys],
    accessEpoch: session.access_epoch,
  };
}

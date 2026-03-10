import { useCallback, useEffect, useRef, useState } from "react";

import { getAccountAccess } from "../../../api/client";
import { useAuth } from "../../auth/useAuth";
import { mapAccountAccess } from "../mappers";
import type { AccountAccessVM } from "../types";

type AccountAccessStatus = "idle" | "loading" | "success" | "anonymous" | "error";

interface UseAccountAccessState {
  status: AccountAccessStatus;
  access: AccountAccessVM | null;
  errorMessage: string | null;
}

const INITIAL_STATE: UseAccountAccessState = {
  status: "idle",
  access: null,
  errorMessage: null,
};

export function useAccountAccess(): UseAccountAccessState & {
  reload: () => Promise<void>;
} {
  const { session } = useAuth();
  const accessEpoch = session.accessEpoch;
  const userId = session.user?.id ?? null;
  const [state, setState] = useState<UseAccountAccessState>(INITIAL_STATE);
  const loadedUserIdRef = useRef<string | null>(null);

  const load = useCallback(async () => {
    if (session.state !== "authenticated" || userId === null) {
      loadedUserIdRef.current = null;
      setState({
        status: "anonymous",
        access: null,
        errorMessage: null,
      });
      return;
    }

    setState((current) => ({
      status: "loading",
      access:
        loadedUserIdRef.current !== null && loadedUserIdRef.current === userId
          ? current.access
          : null,
      errorMessage: null,
    }));

    try {
      const access = mapAccountAccess(await getAccountAccess());
      loadedUserIdRef.current = userId;
      setState({
        status: "success",
        access,
        errorMessage: null,
      });
    } catch (error: unknown) {
      loadedUserIdRef.current = userId;
      setState({
        status: "error",
        access: null,
        errorMessage:
          error instanceof Error
            ? error.message
            : "Failed to load account access state.",
      });
    }
  }, [session.state, userId]);

  useEffect(() => {
    void load();
  }, [accessEpoch, load]);

  return {
    ...state,
    reload: load,
  };
}

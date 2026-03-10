import { useCallback, useEffect, useState } from "react";

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
  const [state, setState] = useState<UseAccountAccessState>(INITIAL_STATE);

  const load = useCallback(async () => {
    void accessEpoch;
    if (session.state !== "authenticated") {
      setState({
        status: "anonymous",
        access: null,
        errorMessage: null,
      });
      return;
    }

    setState((current) => ({
      status: "loading",
      access: current.access,
      errorMessage: null,
    }));

    try {
      const access = mapAccountAccess(await getAccountAccess());
      setState({
        status: "success",
        access,
        errorMessage: null,
      });
    } catch (error: unknown) {
      setState({
        status: "error",
        access: null,
        errorMessage:
          error instanceof Error
            ? error.message
            : "Failed to load account access state.",
      });
    }
  }, [accessEpoch, session.state]);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    ...state,
    reload: load,
  };
}

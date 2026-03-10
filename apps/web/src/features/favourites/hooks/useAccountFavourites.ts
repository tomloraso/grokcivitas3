import { useCallback, useEffect, useRef, useState } from "react";

import { getAccountFavourites } from "../../../api/client";
import { useAuth } from "../../auth/useAuth";
import { mapAccountFavourites } from "../mappers";
import type { AccountFavouritesVM } from "../types";

type AccountFavouritesStatus =
  | "idle"
  | "loading"
  | "success"
  | "anonymous"
  | "error";

interface UseAccountFavouritesState {
  status: AccountFavouritesStatus;
  favourites: AccountFavouritesVM | null;
  errorMessage: string | null;
}

const INITIAL_STATE: UseAccountFavouritesState = {
  status: "idle",
  favourites: null,
  errorMessage: null
};

export function useAccountFavourites(): UseAccountFavouritesState & {
  reload: () => Promise<void>;
} {
  const { session } = useAuth();
  const accessEpoch = session.accessEpoch;
  const userId = session.user?.id ?? null;
  const [state, setState] = useState<UseAccountFavouritesState>(INITIAL_STATE);
  const loadedUserIdRef = useRef<string | null>(null);

  const load = useCallback(async () => {
    if (session.state !== "authenticated" || userId === null) {
      loadedUserIdRef.current = null;
      setState({
        status: "anonymous",
        favourites: null,
        errorMessage: null
      });
      return;
    }

    setState((current) => ({
      status: "loading",
      favourites:
        loadedUserIdRef.current !== null && loadedUserIdRef.current === userId
          ? current.favourites
          : null,
      errorMessage: null
    }));

    try {
      const favourites = mapAccountFavourites(await getAccountFavourites());
      loadedUserIdRef.current = userId;
      setState({
        status: "success",
        favourites,
        errorMessage: null
      });
    } catch (error: unknown) {
      loadedUserIdRef.current = userId;
      setState({
        status: "error",
        favourites: null,
        errorMessage:
          error instanceof Error
            ? error.message
            : "Failed to load saved schools."
      });
    }
  }, [session.state, userId]);

  useEffect(() => {
    void load();
  }, [accessEpoch, load]);

  return {
    ...state,
    reload: load
  };
}

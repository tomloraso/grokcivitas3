import { useCallback, useEffect, useReducer, useRef } from "react";

import {
  ApiClientError,
  getSchoolProfile,
  getSchoolTrendDashboard,
  getSchoolTrends
} from "../../../api/client";
import { mapProfileToVM } from "../mappers/profileMapper";
import type { SchoolProfileVM } from "../types";

type Status = "idle" | "loading" | "success" | "error" | "not-found";

interface ProfileState {
  status: Status;
  profile: SchoolProfileVM | null;
  errorMessage: string | null;
}

type Action =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; profile: SchoolProfileVM }
  | { type: "FETCH_NOT_FOUND" }
  | { type: "FETCH_ERROR"; message: string };

function reducer(_state: ProfileState, action: Action): ProfileState {
  switch (action.type) {
    case "FETCH_START":
      return { status: "loading", profile: null, errorMessage: null };
    case "FETCH_SUCCESS":
      return { status: "success", profile: action.profile, errorMessage: null };
    case "FETCH_NOT_FOUND":
      return { status: "not-found", profile: null, errorMessage: null };
    case "FETCH_ERROR":
      return { status: "error", profile: null, errorMessage: action.message };
  }
}

const INITIAL_STATE: ProfileState = {
  status: "idle",
  profile: null,
  errorMessage: null
};

export function useSchoolProfile(urn: string | undefined) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);
  const requestSeqRef = useRef(0);

  const fetchProfile = useCallback(async () => {
    if (!urn) {
      return;
    }

    const requestId = ++requestSeqRef.current;
    dispatch({ type: "FETCH_START" });

    try {
      const profileRes = await getSchoolProfile(urn);

      if (requestId !== requestSeqRef.current) {
        return;
      }

      // Render core profile immediately; trends can hydrate after first paint.
      let trendsRes: Awaited<ReturnType<typeof getSchoolTrends>> | null = null;
      let dashboardRes: Awaited<ReturnType<typeof getSchoolTrendDashboard>> | null = null;

      const pushMappedProfile = () => {
        dispatch({
          type: "FETCH_SUCCESS",
          profile: mapProfileToVM(profileRes, trendsRes, dashboardRes)
        });
      };

      pushMappedProfile();

      void getSchoolTrends(urn)
        .then((resolvedTrends) => {
          if (requestId !== requestSeqRef.current) {
            return;
          }
          trendsRes = resolvedTrends;
          pushMappedProfile();
        })
        .catch(() => {
          // Trends are optional; keep core profile visible when trends fail.
        });

      void getSchoolTrendDashboard(urn)
        .then((resolvedDashboard) => {
          if (requestId !== requestSeqRef.current) {
            return;
          }
          dashboardRes = resolvedDashboard;
          pushMappedProfile();
        })
        .catch(() => {
          // Benchmark trends are optional; the latest benchmark snapshot still renders.
        });
    } catch (err: unknown) {
      if (requestId !== requestSeqRef.current) {
        return;
      }

      if (err instanceof ApiClientError && err.status === 404) {
        dispatch({ type: "FETCH_NOT_FOUND" });
        return;
      }

      dispatch({
        type: "FETCH_ERROR",
        message: err instanceof Error ? err.message : "Failed to load school profile"
      });
    }
  }, [urn]);

  useEffect(() => {
    void fetchProfile();

    return () => {
      requestSeqRef.current += 1;
    };
  }, [fetchProfile]);

  return {
    ...state,
    retry: fetchProfile
  };
}

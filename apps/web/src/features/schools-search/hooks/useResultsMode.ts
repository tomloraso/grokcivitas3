import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { ApiClientError, searchSchools } from "../../../api/client";
import type {
  SearchPhaseFilter,
  SearchSortMode,
} from "../../../shared/search/searchState";
import type { SchoolsSearchStatus, PostcodeSearchResult } from "../types";
import { postcodeResponseToUnified } from "../types";

interface ResultsModeState {
  status: SchoolsSearchStatus;
  result: PostcodeSearchResult | null;
  errorMessage: string | null;
}

export interface UseResultsModeOptions {
  baseResult: PostcodeSearchResult | null;
  isOpen: boolean;
  phases: readonly SearchPhaseFilter[];
  sort: SearchSortMode;
}

export interface UseResultsModeResult extends ResultsModeState {
  retry: () => Promise<void>;
}

const INITIAL_STATE: ResultsModeState = {
  status: "idle",
  result: null,
  errorMessage: null,
};

function getResultsModeErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 400) {
      return "These results options are not available for the current search.";
    }
    if (error.status === 404) {
      return "The current postcode search could not be restored.";
    }
    if (error.status === 503) {
      return "Results mode is temporarily unavailable. Please try again shortly.";
    }
  }

  return "Results mode is temporarily unavailable. Please retry.";
}

function queriesMatch(
  result: PostcodeSearchResult,
  phases: readonly SearchPhaseFilter[],
  sort: SearchSortMode,
): boolean {
  return (
    result.query.sort === sort &&
    result.query.phases.length === phases.length &&
    result.query.phases.every((phase, index) => phase === phases[index])
  );
}

function toStatus(result: PostcodeSearchResult): SchoolsSearchStatus {
  return result.schools.length === 0 ? "empty" : "success";
}

export function useResultsMode({
  baseResult,
  isOpen,
  phases,
  sort,
}: UseResultsModeOptions): UseResultsModeResult {
  const [state, setState] = useState<ResultsModeState>(INITIAL_STATE);
  const requestSeqRef = useRef(0);
  const phasesKey = phases.join("|");
  const phaseFilters = useMemo<SearchPhaseFilter[]>(
    () => (phasesKey.length > 0 ? (phasesKey.split("|") as SearchPhaseFilter[]) : []),
    [phasesKey],
  );

  const execute = useCallback(async (): Promise<void> => {
    if (!isOpen || !baseResult) {
      setState(INITIAL_STATE);
      return;
    }

    if (queriesMatch(baseResult, phaseFilters, sort)) {
      setState({
        status: toStatus(baseResult),
        result: baseResult,
        errorMessage: null,
      });
      return;
    }

    const requestId = ++requestSeqRef.current;
    setState((current) => ({
      status: "loading",
      result: current.result ?? baseResult,
      errorMessage: null,
    }));

    try {
      const response = await searchSchools({
        postcode: baseResult.query.postcode,
        radius: baseResult.query.radius_miles,
        phase: phaseFilters.length > 0 ? phaseFilters : undefined,
        sort,
      });
      if (requestId !== requestSeqRef.current) {
        return;
      }

      const unified = postcodeResponseToUnified(response);
      if (unified.mode !== "postcode") {
        throw new Error("Expected postcode results response.");
      }

      setState({
        status: toStatus(unified),
        result: unified,
        errorMessage: null,
      });
    } catch (error) {
      if (requestId !== requestSeqRef.current) {
        return;
      }

      setState((current) => ({
        status: "error",
        result: current.result ?? baseResult,
        errorMessage: getResultsModeErrorMessage(error),
      }));
    }
  }, [baseResult, isOpen, phaseFilters, sort]);

  useEffect(() => {
    void execute();
  }, [execute]);

  return {
    ...state,
    retry: execute,
  };
}

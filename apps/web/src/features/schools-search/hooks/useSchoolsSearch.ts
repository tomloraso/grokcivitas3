import { useCallback, useState } from "react";

import { ApiClientError, searchSchools } from "../../../api/client";
import type { SchoolsSearchResponse } from "../../../api/types";
import type { SchoolsSearchFormState, SchoolsSearchState } from "../types";

const DEFAULT_POSTCODE = "NW1 6XE";
const DEFAULT_RADIUS = "5";

function getErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError) {
    if (error.status === 404) {
      return "Postcode not found. Check the postcode and try again.";
    }
    if (error.status === 400) {
      return "Enter a valid UK postcode and radius, then try again.";
    }
    if (error.status === 503) {
      return "Postcode lookup is temporarily unavailable. Please try again shortly.";
    }
  }

  return "Search temporarily unavailable. Please retry.";
}

export interface UseSchoolsSearchResult {
  form: SchoolsSearchFormState;
  state: SchoolsSearchState;
  setPostcode: (value: string) => void;
  setRadius: (value: string) => void;
  submitSearch: () => Promise<void>;
}

export function useSchoolsSearch(): UseSchoolsSearchResult {
  const [form, setForm] = useState<SchoolsSearchFormState>({
    postcode: DEFAULT_POSTCODE,
    radius: DEFAULT_RADIUS,
    postcodeError: null
  });
  const [state, setState] = useState<SchoolsSearchState>({
    status: "idle",
    result: null,
    errorMessage: null
  });

  const setPostcode = useCallback((value: string): void => {
    setForm((current) => ({
      ...current,
      postcode: value,
      postcodeError: null
    }));
  }, []);

  const setRadius = useCallback((value: string): void => {
    setForm((current) => ({
      ...current,
      radius: value
    }));
  }, []);

  const submitSearch = useCallback(async (): Promise<void> => {
    const postcode = form.postcode.trim();
    if (!postcode) {
      setForm((current) => ({
        ...current,
        postcodeError: "Enter a UK postcode to search."
      }));
      return;
    }

    const radius = Number(form.radius);
    const radiusToSend = Number.isFinite(radius) && radius > 0 ? radius : 5;

    setState((current) => ({
      ...current,
      status: "loading",
      errorMessage: null
    }));

    try {
      const response: SchoolsSearchResponse = await searchSchools({
        postcode,
        radius: radiusToSend
      });

      setState({
        status: response.schools.length === 0 ? "empty" : "success",
        result: response,
        errorMessage: null
      });
      setForm((current) => ({
        ...current,
        postcode: response.query.postcode,
        postcodeError: null
      }));
    } catch (error) {
      setState((current) => ({
        status: "error",
        result: current.result,
        errorMessage: getErrorMessage(error)
      }));
    }
  }, [form.postcode, form.radius]);

  return {
    form,
    state,
    setPostcode,
    setRadius,
    submitSearch
  };
}

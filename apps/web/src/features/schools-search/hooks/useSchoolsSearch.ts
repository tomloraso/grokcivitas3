import { useCallback, useEffect, useRef, useState } from "react";

import { ApiClientError, searchSchools, searchSchoolsByName } from "../../../api/client";
import type { SchoolsSearchFormState, SchoolsSearchState, SearchMode } from "../types";
import { detectSearchMode, nameResponseToUnified, postcodeResponseToUnified } from "../types";

const DEFAULT_SEARCH_TEXT = "";
const DEFAULT_RADIUS = "5";
const DEBOUNCE_MS = 300;

function getErrorMessage(error: unknown, mode: SearchMode): string {
  if (error instanceof ApiClientError) {
    if (mode === "postcode") {
      if (error.status === 404) {
        return "Postcode not found. Check the postcode and try again.";
      }
      if (error.status === 400) {
        return "Enter a valid UK postcode and radius, then try again.";
      }
      if (error.status === 503) {
        return "Postcode lookup is temporarily unavailable. Please try again shortly.";
      }
    } else {
      if (error.status === 400) {
        return "Enter at least 3 characters to search by school name.";
      }
      if (error.status === 503) {
        return "School name search is temporarily unavailable. Please try again shortly.";
      }
      return "School name search failed. Please try again.";
    }
  }

  return "Search temporarily unavailable. Please retry.";
}

export interface UseSchoolsSearchOptions {
  /** Pre-fill form from navigation state (e.g. returning from school profile) */
  initialPostcode?: string;
  initialRadius?: number;
  /** Automatically submit on mount when initial values are provided */
  autoSubmit?: boolean;
}

export interface UseSchoolsSearchResult {
  form: SchoolsSearchFormState;
  state: SchoolsSearchState;
  searchMode: SearchMode;
  setSearchText: (value: string) => void;
  setRadius: (value: string) => void;
  submitSearch: () => Promise<void>;
}

export function useSchoolsSearch(options?: UseSchoolsSearchOptions): UseSchoolsSearchResult {
  const [form, setForm] = useState<SchoolsSearchFormState>({
    searchText: options?.initialPostcode ?? DEFAULT_SEARCH_TEXT,
    radius: options?.initialRadius != null ? String(options.initialRadius) : DEFAULT_RADIUS,
    searchError: null,
  });
  const [state, setState] = useState<SchoolsSearchState>({
    status: "idle",
    result: null,
    errorMessage: null,
  });

  const requestSeqRef = useRef(0);
  const searchMode = detectSearchMode(form.searchText);

  const setSearchText = useCallback((value: string): void => {
    requestSeqRef.current += 1;
    const nextMode = detectSearchMode(value);

    setForm((current) => ({
      ...current,
      searchText: value,
      searchError: null,
    }));

    setState((current) => {
      if (!value.trim()) {
        return {
          status: "idle",
          result: null,
          errorMessage: null,
        };
      }

      if (current.result && current.result.mode !== nextMode) {
        return {
          status: "idle",
          result: null,
          errorMessage: null,
        };
      }

      if (current.errorMessage) {
        return {
          ...current,
          errorMessage: null,
        };
      }

      return current;
    });
  }, []);

  const setRadius = useCallback((value: string): void => {
    requestSeqRef.current += 1;
    setForm((current) => ({
      ...current,
      radius: value,
    }));
  }, []);

  // Core search execution
  const executeSearch = useCallback(
    async (text: string, radiusStr: string): Promise<void> => {
      const trimmed = text.trim();
      if (!trimmed) {
        return;
      }

      const mode = detectSearchMode(trimmed);
      if (mode === "name" && trimmed.length < 3) {
        setForm((current) => ({
          ...current,
          searchError: "Type at least 3 characters to search by school name.",
        }));
        return;
      }

      const requestId = ++requestSeqRef.current;

      setState((current) => ({
        status: "loading",
        result: current.result && current.result.mode === mode ? current.result : null,
        errorMessage: null,
      }));

      try {
        if (mode === "postcode") {
          const radius = Number(radiusStr);
          const radiusToSend = Number.isFinite(radius) && radius > 0 ? radius : 5;
          const response = await searchSchools({ postcode: trimmed, radius: radiusToSend });

          if (requestId !== requestSeqRef.current) {
            return;
          }

          setState({
            status: response.schools.length === 0 ? "empty" : "success",
            result: postcodeResponseToUnified(response),
            errorMessage: null,
          });
          setForm((current) => ({
            ...current,
            searchText: response.query.postcode,
            searchError: null,
          }));
        } else {
          const response = await searchSchoolsByName(trimmed);

          if (requestId !== requestSeqRef.current) {
            return;
          }

          setState({
            status: response.schools.length === 0 ? "empty" : "success",
            result: nameResponseToUnified(response, trimmed),
            errorMessage: null,
          });
          setForm((current) => ({
            ...current,
            searchError: null,
          }));
        }
      } catch (error) {
        if (requestId !== requestSeqRef.current) {
          return;
        }

        setState((current) => ({
          status: "error",
          result: current.result && current.result.mode === mode ? current.result : null,
          errorMessage: getErrorMessage(error, mode),
        }));
      }
    },
    []
  );

  // Submit search (for form submission / postcode search)
  const submitSearch = useCallback(async (): Promise<void> => {
    const trimmed = form.searchText.trim();
    if (!trimmed) {
      setForm((current) => ({
        ...current,
        searchError: "Enter a UK postcode or school name to search.",
      }));
      return;
    }

    const mode = detectSearchMode(trimmed);
    if (mode === "name" && trimmed.length < 3) {
      setForm((current) => ({
        ...current,
        searchError: "Type at least 3 characters to search by school name.",
      }));
      return;
    }

    await executeSearch(trimmed, form.radius);
  }, [form.searchText, form.radius, executeSearch]);

  // Debounced name search
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestSearchText = useRef(form.searchText);
  latestSearchText.current = form.searchText;

  useEffect(() => {
    const trimmed = form.searchText.trim();
    const mode = detectSearchMode(trimmed);

    if (mode !== "name" || trimmed.length < 3) {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
      return;
    }

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      // Only fire if text hasn't changed
      if (latestSearchText.current.trim() === trimmed) {
        void executeSearch(trimmed, form.radius);
      }
    }, DEBOUNCE_MS);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [form.searchText, form.radius, executeSearch]);

  // Auto-submit on mount when restoring a previous search (e.g. breadcrumb back-nav)
  const didAutoSubmit = useRef(false);
  useEffect(() => {
    if (options?.autoSubmit && !didAutoSubmit.current) {
      didAutoSubmit.current = true;
      void submitSearch();
    }
    // Only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    form,
    state,
    searchMode,
    setSearchText,
    setRadius,
    submitSearch,
  };
}

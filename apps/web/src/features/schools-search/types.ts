import type { SchoolNameSearchResponse, SchoolSearchResultItem, SchoolsSearchResponse } from "../../api/types";

export type SchoolsSearchStatus = "idle" | "loading" | "success" | "empty" | "error";

export type SearchMode = "postcode" | "name";

/** Unified result that works for both postcode and name search. */
export interface UnifiedSearchResult {
  mode: SearchMode;
  schools: SchoolSearchListItem[];
  count: number;
  /** Present only for postcode search. */
  query?: { postcode: string; radius_miles: number };
  /** Present only for postcode search. */
  center?: { lat: number; lng: number };
  /** Present only for name search. */
  nameQuery?: string;
}

export interface SchoolsSearchState {
  status: SchoolsSearchStatus;
  result: UnifiedSearchResult | null;
  errorMessage: string | null;
}

export interface SchoolsSearchFormState {
  searchText: string;
  radius: string;
  searchError: string | null;
}

export type SchoolSearchListItem = SchoolSearchResultItem;

/** UK postcode regex for auto-detection. */
export const UK_POSTCODE_REGEX = /^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i;

export function detectSearchMode(input: string): SearchMode {
  return UK_POSTCODE_REGEX.test(input.trim()) ? "postcode" : "name";
}

export function postcodeResponseToUnified(response: SchoolsSearchResponse): UnifiedSearchResult {
  return {
    mode: "postcode",
    schools: response.schools,
    count: response.count,
    query: response.query,
    center: response.center,
  };
}

export function nameResponseToUnified(
  response: SchoolNameSearchResponse,
  nameQuery: string
): UnifiedSearchResult {
  return {
    mode: "name",
    schools: response.schools,
    count: response.count,
    nameQuery,
  };
}

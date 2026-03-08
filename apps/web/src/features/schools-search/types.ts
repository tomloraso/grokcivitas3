import type {
  PostcodeSchoolSearchResultItem,
  SchoolNameSearchResponse,
  SchoolNameSearchResultItem,
  SchoolsSearchResponse,
} from "../../api/types";
import {
  normalizeSearchPhaseFilters,
  normalizeSearchSortMode,
  type SearchPhaseFilter,
  type SearchSortMode,
} from "../../shared/search/searchState";

export type SchoolsSearchStatus = "idle" | "loading" | "success" | "empty" | "error";

export type SearchMode = "postcode" | "name";

export interface PostcodeSearchQuery {
  postcode: string;
  radius_miles: number;
  phases: SearchPhaseFilter[];
  sort: SearchSortMode;
}

export interface PostcodeSearchResult {
  mode: "postcode";
  schools: PostcodeSchoolSearchResultItem[];
  count: number;
  query: PostcodeSearchQuery;
  center: { lat: number; lng: number };
}

export interface NameSearchResult {
  mode: "name";
  schools: SchoolNameSearchResultItem[];
  count: number;
  nameQuery: string;
}

/** Unified result that works for both postcode and name search. */
export type UnifiedSearchResult = PostcodeSearchResult | NameSearchResult;

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

export type SchoolSearchListItem = PostcodeSchoolSearchResultItem | SchoolNameSearchResultItem;

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
    query: {
      postcode: response.query.postcode,
      radius_miles: response.query.radius_miles,
      phases: normalizeSearchPhaseFilters(response.query.phases),
      sort: normalizeSearchSortMode(response.query.sort),
    },
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

export function isPostcodeSearchResult(
  result: UnifiedSearchResult | null
): result is PostcodeSearchResult {
  return result?.mode === "postcode";
}

export function isPostcodeSearchListItem(
  school: SchoolSearchListItem
): school is PostcodeSchoolSearchResultItem {
  return "latest_ofsted" in school && "academic_metric" in school;
}

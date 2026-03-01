import type { SchoolSearchResultItem, SchoolsSearchResponse } from "../../api/types";

export type SchoolsSearchStatus = "idle" | "loading" | "success" | "empty" | "error";

export interface SchoolsSearchState {
  status: SchoolsSearchStatus;
  result: SchoolsSearchResponse | null;
  errorMessage: string | null;
}

export interface SchoolsSearchFormState {
  postcode: string;
  radius: string;
  postcodeError: string | null;
}

export type SchoolSearchListItem = SchoolSearchResultItem;

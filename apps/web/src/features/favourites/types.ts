import type { SectionAccessVM } from "../premium-access/types";

export type SavedSchoolStateStatus =
  | "saved"
  | "not_saved"
  | "requires_auth"
  | "locked";

export interface SavedSchoolStateVM {
  status: SavedSchoolStateStatus;
  savedAt: string | null;
  capabilityKey: string | null;
  reasonCode: SectionAccessVM["reasonCode"];
}

export interface FavouriteSummaryMetricVM {
  label: string | null;
  availability: string;
}

export interface FavouriteSummaryOfstedVM extends FavouriteSummaryMetricVM {
  sortRank: number | null;
}

export interface FavouriteSummaryAcademicMetricVM
  extends FavouriteSummaryMetricVM {
  metricKey: string | null;
  displayValue: string | null;
  sortValue: number | null;
}

export interface AccountFavouriteSchoolVM {
  urn: string;
  name: string;
  type: string | null;
  phase: string | null;
  postcode: string | null;
  pupilCount: number | null;
  latestOfsted: FavouriteSummaryOfstedVM;
  academicMetric: FavouriteSummaryAcademicMetricVM;
  savedAt: string;
}

export interface AccountFavouritesVM {
  access: SectionAccessVM;
  count: number;
  schools: AccountFavouriteSchoolVM[];
}

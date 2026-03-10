import type {
  AccountFavouritesResponse,
  SavedSchoolStateResponse
} from "../../api/types";
import { mapSectionAccess } from "../premium-access/mappers";
import type {
  AccountFavouritesVM,
  AccountFavouriteSchoolVM,
  SavedSchoolStateVM
} from "./types";

export function mapSavedSchoolState(
  savedState: SavedSchoolStateResponse
): SavedSchoolStateVM {
  return {
    status: savedState.status,
    savedAt: savedState.saved_at,
    capabilityKey: savedState.capability_key,
    reasonCode: savedState.reason_code
  };
}

function mapAccountFavouriteSchool(
  school: NonNullable<AccountFavouritesResponse["schools"]>[number]
): AccountFavouriteSchoolVM {
  return {
    urn: school.urn,
    name: school.name,
    type: school.type,
    phase: school.phase,
    postcode: school.postcode,
    pupilCount: school.pupil_count,
    latestOfsted: {
      label: school.latest_ofsted.label,
      sortRank: school.latest_ofsted.sort_rank,
      availability: school.latest_ofsted.availability
    },
    academicMetric: {
      metricKey: school.academic_metric.metric_key,
      label: school.academic_metric.label,
      displayValue: school.academic_metric.display_value,
      sortValue: school.academic_metric.sort_value,
      availability: school.academic_metric.availability
    },
    savedAt: school.saved_at
  };
}

export function mapAccountFavourites(
  response: AccountFavouritesResponse
): AccountFavouritesVM {
  return {
    access: mapSectionAccess(response.access),
    count: response.count,
    schools: (response.schools ?? []).map((school) =>
      mapAccountFavouriteSchool(school)
    )
  };
}

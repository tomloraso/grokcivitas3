export type CompletenessReasonCode =
  | "source_missing"
  | "insufficient_years_published"
  | "source_not_in_catalog"
  | "source_file_missing_for_year"
  | "source_schema_incompatible_for_year"
  | "partial_metric_coverage"
  | "source_not_provided"
  | "rejected_by_validation"
  | "not_joined_yet"
  | "pipeline_failed_recently"
  | "not_applicable"
  | "source_coverage_gap"
  | "stale_after_school_refresh"
  | "no_incidents_in_radius"
  | "unsupported_stage";

export type CompletenessMessageKey =
  | "missing"
  | "insufficientYearsPublished"
  | "sourceNotInCatalog"
  | "sourceFileMissingForYear"
  | "sourceSchemaIncompatibleForYear"
  | "partialMetricCoverage"
  | "notProvided"
  | "validationRejected"
  | "notJoinedYet"
  | "pipelineFailedRecently"
  | "notApplicable"
  | "sourceCoverageGap"
  | "staleAfterSchoolRefresh"
  | "noIncidentsInRadius"
  | "unsupportedStage";

const REASON_MESSAGE_KEYS: Record<
  CompletenessReasonCode,
  CompletenessMessageKey
> = {
  source_missing: "missing",
  insufficient_years_published: "insufficientYearsPublished",
  source_not_in_catalog: "sourceNotInCatalog",
  source_file_missing_for_year: "sourceFileMissingForYear",
  source_schema_incompatible_for_year: "sourceSchemaIncompatibleForYear",
  partial_metric_coverage: "partialMetricCoverage",
  source_not_provided: "notProvided",
  rejected_by_validation: "validationRejected",
  not_joined_yet: "notJoinedYet",
  pipeline_failed_recently: "pipelineFailedRecently",
  not_applicable: "notApplicable",
  source_coverage_gap: "sourceCoverageGap",
  stale_after_school_refresh: "staleAfterSchoolRefresh",
  no_incidents_in_radius: "noIncidentsInRadius",
  unsupported_stage: "unsupportedStage"
};

const REASON_COPY: Record<CompletenessMessageKey, string> = {
  missing: "This information hasn't been published by the data source yet.",
  insufficientYearsPublished:
    "We currently have limited published years for this school.",
  sourceNotInCatalog:
    "This source is not currently in our approved school-data catalog.",
  sourceFileMissingForYear:
    "A published file for this year is not yet available for this school.",
  sourceSchemaIncompatibleForYear:
    "This year's published file couldn't be used because the format changed.",
  partialMetricCoverage:
    "Some measures are available, but other parts of this section are still missing.",
  notProvided:
    "The data source only records some of this information for this school.",
  validationRejected:
    "Some information was excluded because it didn't pass our quality checks.",
  notJoinedYet:
    "We're still connecting this information to the school's location.",
  pipelineFailedRecently:
    "This information is temporarily unavailable while we update our records.",
  notApplicable: "This section doesn't apply to this type of school.",
  sourceCoverageGap:
    "The source currently has limited coverage for this information.",
  staleAfterSchoolRefresh:
    "This section will refresh after the next local-area data update.",
  noIncidentsInRadius:
    "No incidents were recorded in this area for the latest reporting window.",
  unsupportedStage:
    "Some published destination stages are not yet supported in this view."
};

export function mapCompletenessReasonToMessageKey(
  reasonCode: CompletenessReasonCode | null
): CompletenessMessageKey | null {
  if (!reasonCode) {
    return null;
  }

  return REASON_MESSAGE_KEYS[reasonCode];
}

export function formatCompletenessReasonCopy({
  reasonCode,
  yearsAvailable
}: {
  reasonCode: CompletenessReasonCode | null;
  yearsAvailable?: string[] | null;
}): string | null {
  const messageKey = mapCompletenessReasonToMessageKey(reasonCode);
  if (messageKey === null) {
    return null;
  }

  if (messageKey === "insufficientYearsPublished") {
    const publishedYears = yearsAvailable?.length ?? 0;
    if (publishedYears === 1) {
      return "We currently have one published year for this school.";
    }
    if (publishedYears > 1) {
      return `We currently have ${publishedYears} published years for this school.`;
    }
  }

  return REASON_COPY[messageKey];
}

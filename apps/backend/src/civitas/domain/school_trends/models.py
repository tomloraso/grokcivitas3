from dataclasses import dataclass


@dataclass(frozen=True)
class SchoolDemographicsYearlyRow:
    academic_year: str
    disadvantaged_pct: float | None
    sen_pct: float | None
    ehcp_pct: float | None
    eal_pct: float | None


@dataclass(frozen=True)
class SchoolDemographicsSeries:
    urn: str
    rows: tuple[SchoolDemographicsYearlyRow, ...]

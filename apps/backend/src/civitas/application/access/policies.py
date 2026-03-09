from civitas.application.access.errors import AccessRequirementNotFoundError
from civitas.domain.access.models import AccessRequirement

SCHOOL_PROFILE_OVERVIEW_REQUIREMENT = "school_profile.overview"
SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT = "school_profile.ai_analyst"
SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT = "school_profile.neighbourhood"
SCHOOL_COMPARE_CORE_REQUIREMENT = "school_compare.core"

PREMIUM_AI_ANALYST_CAPABILITY = "premium_ai_analyst"
PREMIUM_COMPARISON_CAPABILITY = "premium_comparison"
PREMIUM_NEIGHBOURHOOD_CAPABILITY = "premium_neighbourhood"

LAUNCH_CAPABILITY_KEYS: tuple[str, ...] = (
    PREMIUM_AI_ANALYST_CAPABILITY,
    PREMIUM_COMPARISON_CAPABILITY,
    PREMIUM_NEIGHBOURHOOD_CAPABILITY,
)

ACCESS_REQUIREMENTS: dict[str, AccessRequirement] = {
    SCHOOL_PROFILE_OVERVIEW_REQUIREMENT: AccessRequirement(
        key=SCHOOL_PROFILE_OVERVIEW_REQUIREMENT,
        capability_key=None,
    ),
    SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT: AccessRequirement(
        key=SCHOOL_PROFILE_AI_ANALYST_REQUIREMENT,
        capability_key=PREMIUM_AI_ANALYST_CAPABILITY,
    ),
    SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT: AccessRequirement(
        key=SCHOOL_PROFILE_NEIGHBOURHOOD_REQUIREMENT,
        capability_key=PREMIUM_NEIGHBOURHOOD_CAPABILITY,
    ),
    SCHOOL_COMPARE_CORE_REQUIREMENT: AccessRequirement(
        key=SCHOOL_COMPARE_CORE_REQUIREMENT,
        capability_key=PREMIUM_COMPARISON_CAPABILITY,
    ),
}


def get_access_requirement(requirement_key: str) -> AccessRequirement:
    normalized_key = requirement_key.strip().casefold()
    try:
        return ACCESS_REQUIREMENTS[normalized_key]
    except KeyError as exc:
        raise AccessRequirementNotFoundError(normalized_key) from exc

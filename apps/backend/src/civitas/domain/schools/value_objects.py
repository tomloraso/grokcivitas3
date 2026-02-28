import re


class InvalidPostcodeError(ValueError):
    pass


POSTCODE_PATTERN = re.compile(r"^(GIR 0AA|[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2})$")


def normalize_uk_postcode(raw_postcode: str) -> str:
    compact = "".join(raw_postcode.strip().upper().split())
    if not compact:
        raise InvalidPostcodeError("postcode must be a valid UK postcode.")
    if len(compact) < 5 or len(compact) > 7:
        raise InvalidPostcodeError("postcode must be a valid UK postcode.")

    normalized = f"{compact[:-3]} {compact[-3:]}"
    if not POSTCODE_PATTERN.fullmatch(normalized):
        raise InvalidPostcodeError("postcode must be a valid UK postcode.")

    return normalized

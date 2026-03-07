class InvalidSchoolCompareParametersError(ValueError):
    pass


class SchoolCompareNotFoundError(LookupError):
    def __init__(self, missing_urns: tuple[str, ...]) -> None:
        quoted_urns = ", ".join(f"'{urn}'" for urn in missing_urns)
        if len(missing_urns) == 1:
            message = f"School with URN {quoted_urns} was not found."
        else:
            message = f"Schools with URNs {quoted_urns} were not found."
        super().__init__(message)


class SchoolCompareDataUnavailableError(RuntimeError):
    pass

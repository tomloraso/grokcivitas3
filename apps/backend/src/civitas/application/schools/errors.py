class InvalidSchoolSearchParametersError(ValueError):
    pass


class PostcodeNotFoundError(LookupError):
    def __init__(self, postcode: str) -> None:
        super().__init__(f"Postcode '{postcode}' was not found.")


class PostcodeResolverUnavailableError(RuntimeError):
    pass

class SchoolProfileNotFoundError(LookupError):
    def __init__(self, urn: str) -> None:
        super().__init__(f"School with URN '{urn}' was not found.")


class SchoolProfileDataUnavailableError(RuntimeError):
    pass

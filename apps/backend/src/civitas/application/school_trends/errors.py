class SchoolTrendsNotFoundError(LookupError):
    def __init__(self, urn: str) -> None:
        super().__init__(f"School with URN '{urn}' was not found.")


class SchoolTrendsDataUnavailableError(RuntimeError):
    pass

class SavedSchoolNotFoundError(Exception):
    def __init__(self, school_urn: str) -> None:
        super().__init__(f"School with URN '{school_urn}' was not found.")
        self.school_urn = school_urn

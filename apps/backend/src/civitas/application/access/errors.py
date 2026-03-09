class AccessRequirementNotFoundError(KeyError):
    def __init__(self, requirement_key: str) -> None:
        super().__init__(f"Access requirement '{requirement_key}' is not registered.")

from typing import Protocol


class SchoolProfileCacheInvalidator(Protocol):
    def invalidate_school_profile_cache(self) -> None: ...

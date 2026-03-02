from typing import Protocol

from civitas.domain.school_profiles.models import SchoolProfile


class SchoolProfileRepository(Protocol):
    def get_school_profile(self, urn: str) -> SchoolProfile | None: ...

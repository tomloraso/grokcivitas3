from typing import Protocol

from civitas.domain.schools.models import PostcodeCoordinates


class PostcodeContextResolver(Protocol):
    def resolve(self, postcode: str) -> PostcodeCoordinates: ...

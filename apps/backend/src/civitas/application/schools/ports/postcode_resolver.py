from typing import Protocol

from civitas.domain.schools.models import PostcodeCoordinates


class PostcodeResolver(Protocol):
    def resolve(self, postcode: str) -> PostcodeCoordinates: ...

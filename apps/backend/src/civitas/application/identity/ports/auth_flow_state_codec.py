from __future__ import annotations

from typing import Protocol

from civitas.application.identity.dto import AuthFlowStateDto


class AuthFlowStateCodec(Protocol):
    def issue(self, *, attempt_id: str) -> str: ...

    def read(self, *, state: str) -> AuthFlowStateDto: ...

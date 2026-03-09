from typing import Protocol

from civitas.domain.access.models import PremiumProduct


class ProductRepository(Protocol):
    def get_product_by_code(self, *, code: str) -> PremiumProduct | None: ...

    def list_available_products(self) -> tuple[PremiumProduct, ...]: ...

    def list_products_for_capability(
        self,
        *,
        capability_key: str,
    ) -> tuple[PremiumProduct, ...]: ...

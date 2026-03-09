class BillingProductNotFoundError(KeyError):
    def __init__(self, product_code: str) -> None:
        super().__init__(f"Premium product '{product_code}' was not found.")


class BillingProductNotConfiguredError(RuntimeError):
    def __init__(self, product_code: str) -> None:
        super().__init__(f"Premium product '{product_code}' is not configured for billing.")


class CheckoutSessionNotFoundError(KeyError):
    def __init__(self, checkout_id: str) -> None:
        super().__init__(f"Checkout session '{checkout_id}' was not found.")


class BillingCustomerNotFoundError(KeyError):
    def __init__(self) -> None:
        super().__init__("No billing customer was found for the current account.")


class PaymentProviderUnavailableError(RuntimeError):
    pass


class PaymentEventVerificationError(ValueError):
    pass

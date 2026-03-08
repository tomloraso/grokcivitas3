class InvalidSignInEmailError(ValueError):
    """Raised when sign-in is started with an invalid email address."""


class InvalidAuthCallbackError(ValueError):
    """Raised when callback state or provider verification fails."""


class IdentityProviderUnavailableError(RuntimeError):
    """Raised when the configured identity provider cannot complete an operation."""

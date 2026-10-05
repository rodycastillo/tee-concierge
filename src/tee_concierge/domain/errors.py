class NotFoundError(Exception):
    """The requested entity does not exist."""


class ConflictError(Exception):
    """The change would violate a uniqueness rule (e.g. duplicate SKU)."""


class InvalidInputError(ValueError):
    """The input is well-formed but not acceptable (e.g. negative stock)."""

class CheckoutError(Exception):
    pass


class EmptyCartError(CheckoutError):
    pass


class InvalidCartError(CheckoutError):
    def __init__(self, errors):
        self.errors = errors
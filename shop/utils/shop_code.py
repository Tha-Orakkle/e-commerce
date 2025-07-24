from django.utils.crypto import get_random_string


def generate_shop_code():
    """
    Generates a code for a Shop instance.
    """
    return f"SH{get_random_string(5, allowed_chars='0123456789')}"
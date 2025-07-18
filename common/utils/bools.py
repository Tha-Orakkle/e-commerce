def parse_bool(value):
    """
    Helper function to help parse a boolean value.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'on']
    return False

def password_check(password):
    """Checks the strength of the password"""
    if not password:
        raise ValueError('Password field is required.')
    if len(password) < 8:
        raise ValueError('Password must be at least 8 characters long.')
    if not any(char.isdigit() for char in password):
        raise ValueError('Password must contain at least one digit.')
    if not any(char.isalpha() for char in password):
        raise ValueError('Password must contain at least one letter.')
    if not any(char.isupper() for char in password):
        raise ValueError('Password must contain at least one uppercase letter.')
    if not any(char.islower() for char in password):
        raise ValueError('Password must contain at least one lowercase letter.')
    if not any(char in ['@', '#', '$', '%', '^', '&', '*'] for char in password):
        raise ValueError('Password must contain at least one special character.')
    return True

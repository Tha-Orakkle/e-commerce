from rest_framework.exceptions import ValidationError

import re

def validate_password(password):
    """Checks the strength of the password"""
    errors = []
    if not password:
        raise ValidationError("This field is required.")
    if password and len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if password and not any(char.isdigit() for char in password):
        errors.append("Password must contain at least one digit.")
    if password and not any(char.isalpha() for char in password):
        errors.append("Password must contain at least one letter.")
    if password and not any(char.isupper() for char in password):
        errors.append("Password must contain at least one uppercase letter.")
    if password and not any(char.islower() for char in password):
        errors.append("Password must contain at least one lowercase letter.")
    if password and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character.")
    if errors:
        raise ValidationError(errors)
    return password

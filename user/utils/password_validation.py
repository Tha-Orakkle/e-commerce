from rest_framework.exceptions import ValidationError

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

def password_check_v2(password):
    """Checks the strength of the password"""
    error_list = []
    if not password:
        return ["This field is required."]
    if password and len(password) < 8:
        error_list.append("Password must be at least 8 characters long.")
    if password and not any(char.isdigit() for char in password):
        error_list.append("Password must contain at least one digit.")
    if password and not any(char.isalpha() for char in password):
        error_list.append("Password must contain at least one letter.")
    if password and not any(char.isupper() for char in password):
        error_list.append("Password must contain at least one uppercase letter.")
    if password and not any(char.islower() for char in password):
        error_list.append("Password must contain at least one lowercase letter.")
    if password and not any(char in ['@', '#', '$', '%', '^', '&', '*'] for char in password):
        error_list.append("Password must contain at least one special character.")
    if error_list:
        raise ValidationError(error_list)
    return error_list
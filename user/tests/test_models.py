"""
Test models for the user app.
These tests cover the User and UserProfile models.
"""


def test_user_creation(user):
    """
    Test the creation of a user.
    """
    assert user.id is not None
    assert type(user.id).__name__ == "UUID"
    assert user.is_active == True
    assert user.is_staff == False
    assert user.is_verified == False
    assert user.is_superuser == False
    assert user.email == "user@email.com"
    assert user.password != "Password123#"
    assert user.check_password("Password123#")


def test_user_str(user):
    """
    Test the string representation of a user.
    """
    assert str(user) == f"<User: {user.id}> {user.email}"


def test_user_profile_creation(user):
    """
    Test the creation of a user profile.
    """
    assert user.profile is not None
    assert user.profile.first_name == ""
    assert user.profile.last_name == ""
    assert user.profile.telephone == ""
    assert user.profile.user == user


def test_user_profile_str(user):
    """
    Test the string representation of a user profile.
    """
    assert str(user.profile) == f"<UserProfile: {user.profile.id}> {user.email}"
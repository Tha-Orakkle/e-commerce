from django.conf import settings
from django.utils.timezone import timedelta
from rest_framework.response import Response


def set_auth_cookie(
    response: Response,
    name: str,
    value: str,
    *,
    max_age: timedelta | int = None
) -> None:
    """
    Set refresh and access tokens for a response.
    """
    config = settings.SIMPLE_JWT

    if not max_age and name == "access_token":
        max_age = config.get("ACCESS_TOKEN_LIFETIME")
    elif not max_age and name == "refresh_token":
        max_age = config.get("REFRESH_TOKEN_LIFETIME")

    response.set_cookie(
        key=name,
        value=value,
        max_age=max_age,
        httponly=config["AUTH_COOKIE_HTTP_ONLY"],
        secure=config["AUTH_COOKIE_SECURE"],
        samesite=config["AUTH_COOKIE_SAMESITE"],
        path=config["AUTH_COOKIE_PATH"]
    )

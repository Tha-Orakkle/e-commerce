from django.contrib.auth import get_user_model
from django.core import signing

User = get_user_model()


def generate_email_verification_token(user_id):
    """
    Generate a token for email verification.
    """
    return signing.dumps({'user_id': user_id}, salt='email-verification')


def verify_email_verification_token(token):
    """
    Verify the email verification token.
    Returns the user ID if the token is valid.
    """
    try:
        data = signing.loads(token, salt='email-verification', max_age=3600)
        # max_age is set to 1 hour
        user_id = data.get('user_id')
    except signing.BadSignature:
        return None
    except signing.SignatureExpired:
        return None
    # check that the user ID exists in the database
    user = User.objects.filter(id=user_id).first()
    if not user:
        return None
    return user

    



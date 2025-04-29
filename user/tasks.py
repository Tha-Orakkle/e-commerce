from celery import shared_task

from user.utils.email_verification import generate_email_verification_token
from user.utils.send_email import send_verification_mail, send_password_reset_mail


@shared_task
def send_verification_mail_task(user_id, email):
    token = generate_email_verification_token(user_id)
    link = f'http://127.0.0.1/api/verify/?token={token}'
    send_verification_mail(email, link)


@shared_task
def send_password_reset_mail_task(email, link):
    send_password_reset_mail(email, link)
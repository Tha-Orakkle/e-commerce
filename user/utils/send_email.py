from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string 
from django.conf import settings

def send_verification_mail(email, link):
    """send verification mail to user. Mail will a
    contain link which will consist of the verification token
    Args:
        email (str): recipient email address
        link (str): verification link
    """
    subject = 'Verify Your Email'
    to = [email]
    _from = settings.DEFAULT_FROM_EMAIL
    text_content = f"Click the link to verify your email: {link}"
    context = {
        'user': email,
        'link': link,
    }
    html_content = render_to_string('user/email_verification.html', context) 
    email = EmailMultiAlternatives(subject, text_content, _from, to)
    email.attach_alternative(html_content, "text/html")
    email.send()

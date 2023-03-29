from django.core.mail import EmailMultiAlternatives
from django.dispatch import receiver
from django.template.loader import render_to_string

from django_rest_passwordreset.signals import reset_password_token_created


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token,
                                 *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    :param sender: View Class that sent the signal
    :param instance: View Instance that sent the signal
    :param reset_password_token: Token Model Object
    :param args:
    :param kwargs:
    :return:
    """
    # check the view instance for remote_host
    try:
        remote_host = instance.request.META['REMOTE_HOST']
        if len(remote_host) < 1:
            remote_host = "squac.pnsn.org"
    except KeyError:
        remote_host = "squac.pnsn.org"

    print(remote_host)

    context = {
        'user': reset_password_token.user,
        'username': reset_password_token.user.email,
        'email': reset_password_token.user.email,
        'remote_host': remote_host,
        'reset_password_url': "https://{}{}?token={}".format(
            remote_host, "/password_reset/confirm",
            reset_password_token.key)
    }

    # render email text
    email_html_message = render_to_string(
        'email/user_reset_password.html', context)
    email_plaintext_message = render_to_string(
        'email/user_reset_password.txt', context)

    msg = EmailMultiAlternatives(
        # title:
        "Password Reset for {title}".format(title="SQUAC"),
        # message:
        email_plaintext_message,
        # from:
        "pnsn_web@uw.org",
        # to:
        [reset_password_token.user.email]
    )
    msg.attach_alternative(email_html_message, "text/html")
    msg.send()

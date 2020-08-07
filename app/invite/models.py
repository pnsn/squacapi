import base64
import uuid
from django.db import models
from django.conf import settings
from django.core.mail import send_mail


class InviteToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (str(self.id).encode()).decode()

    def send_invite(self):
        token = base64.urlsafe_b64encode(str(self.id).encode()).decode()
        org_desc = self.user.organization.description
        send_mail("You've been invited to SQUAC",
                  f"You have been invited to the {org_desc} organization in"
                  f" SQUAC. Please visit: \n"
                  f"https://squac.pnsn.org/signup?token={token} \n"
                  f"to complete your registration.",
                  settings.EMAIL_NO_REPLY,
                  [self.user.email, ],
                  fail_silently=False,
                  )

    # override save rather then creating signal
    def save(self, *args, **kwargs):
        super(InviteToken, self).save(*args, **kwargs)
        self.send_invite()

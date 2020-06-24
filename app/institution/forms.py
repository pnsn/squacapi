# WARNING. The organization app migration must be ran before these classes
# are instantiated

from django import forms
# from django.conf import settings
# from django.contrib.sites.models import Site
from organizations.backends import invitation_backend
from institution.models import InstitutionUser


class InstitutionUserForm(forms.ModelForm):
    """
    Form class for editing AccountUsers *and* the linked user model.
    """
    firstname = forms.CharField(max_length=100)
    lastname = forms.CharField(max_length=100)
    email = forms.EmailField()
    is_admin = forms.BooleanField()

    class Meta:
        exclude = ('user', 'is_admin')
        model = InstitutionUser

    def __init__(self, *args, **kwargs):
        super(InstitutionUserForm, self).__init__(*args, **kwargs)
        if self.instance.pk is not None:
            self.fields['firstname'].initial = self.instance.user.firstname
            self.fields['lastname'].initial = self.instance.user.lastname
            self.fields['email'].initial = self.instance.user.email
            self.fields['is_admin'].initial = self.instance.is_admin

    def save(self, *args, **kwargs):
        """
        This method saves changes to the linked user model.
        """
        if self.instance.pk is None:
            # site = Site.objects.get(pk=settings.SITE_ID)
            self.instance.user = invitation_backend().invite_by_email(
                self.cleaned_data['email'],
                **{'firstname': self.cleaned_data['firstname'],
                    'lastname': self.cleaned_data['lastname'],
                    'organization': self.cleaned_data['organization']})
            # 'domain': site})
        self.instance.user.firstname = self.cleaned_data['firstname']
        self.instance.user.lastname = self.cleaned_data['lastname']
        self.instance.user.email = self.cleaned_data['email']
        self.instance.is_admin = self.cleaned_data['is_admin']
        self.instance.user.save()
        return super(InstitutionUserForm, self).save(*args, **kwargs)

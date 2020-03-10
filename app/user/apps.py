from django.apps import AppConfig


class UserConfig(AppConfig):
    name = 'user'

    # this is how we load the reciever
    def ready(self):
        from user import signals  # noqa

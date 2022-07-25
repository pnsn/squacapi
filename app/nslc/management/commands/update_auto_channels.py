from django.core.management.base import BaseCommand
from nslc.models import Group


class Command(BaseCommand):
    """
    Command to update any channel groups that have auto-update settings.
    Actually calls update_channels() for every group, but if a given group does
    not have auto-update information nothing will happen
    """

    def add_arguments(self, parser):
        parser.add_argument('--channel_groups', action='append',
                            help='List of groups to update',
                            default=[])

    def handle(self, *args, **options):
        '''method called by manager'''

        channel_groups = options['channel_groups']

        # Get all groups
        groups = Group.objects.all()

        # Filter for specific channel groups if they were selected
        if len(channel_groups) > 0:
            groups = groups.filter(id__in=channel_groups)

        # Update channels for each group, if applicable
        for group in groups:
            group.update_channels()

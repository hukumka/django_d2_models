from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-apps-only',
            type=bool,
            help='Determines if third-party app models are included. Default: True',
        )
        parser.add_argument(
            '--exclude-app',
            type=str,
            nargs='+',
        )

    def handle(self, *args, **options):
        print(options)

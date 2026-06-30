from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.migrations.exceptions import InconsistentMigrationHistory

class Command(BaseCommand):
    help = 'Migrate, faking accounts.0001_initial only if history is inconsistent'

    def handle(self, *args, **options):
        self.stdout.write('Running migrate...')
        try:
            call_command('migrate', verbosity=1)
        except InconsistentMigrationHistory:
            self.stdout.write('Inconsistent history — faking accounts.0001_initial')
            call_command('migrate', 'accounts', '0001_initial', fake=True, verbosity=1)
            call_command('migrate', verbosity=1)
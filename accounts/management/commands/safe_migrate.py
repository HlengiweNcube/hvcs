from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


class Command(BaseCommand):
    help = 'Migrate safely by faking already-applied migrations that are missing from the migration log'

    # Migrations whose tables already exist in production but may not be
    # recorded in django_migrations (e.g. after a custom user model swap).
    EXPECTED_APPLIED = [
        ('accounts', '0001_initial'),
        ('accounts', '0002_client'),
        ('accounts', '0003_caregiver'),
        ('accounts', '0004_align_client_to_erd'),
        ('accounts', '0005_visit'),
    ]

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        applied = {(m.app, m.name) for m in recorder.migration_qs}

        for app, name in self.EXPECTED_APPLIED:
            if (app, name) not in applied:
                recorder.record_applied(app, name)
                self.stdout.write(self.style.WARNING(f'Faked missing migration: {app}.{name}'))

        self.stdout.write('Running migrate...')
        call_command('migrate', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


def _table_exists(table):
    return table in connection.introspection.table_names()


def _column_exists(table, column):
    if not _table_exists(table):
        return False
    with connection.cursor() as cursor:
        cols = [c.name for c in connection.introspection.get_table_description(cursor, table)]
    return column in cols


class Command(BaseCommand):
    help = 'Migrate safely by faking already-applied migrations missing from the migration log'

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        applied = {(m.app, m.name) for m in recorder.migration_qs}

        # Migrations whose schema already exists in production but may not be
        # recorded in django_migrations (e.g. after a custom user model swap).
        to_fake = [
            ('accounts', '0001_initial'),
            ('accounts', '0002_client'),
            ('accounts', '0003_caregiver'),
            ('accounts', '0004_align_client_to_erd'),
            ('accounts', '0005_visit'),
        ]

        # Only fake 0006 if the GPS columns already exist in the DB.
        # On Render (production) they don't exist yet, so migrate will add them.
        if _column_exists('accounts_visit', 'check_in_lat'):
            to_fake.append(('accounts', '0006_visit_gps_checkin'))

        for app, name in to_fake:
            if (app, name) not in applied:
                recorder.record_applied(app, name)
                self.stdout.write(self.style.WARNING(f'Faked missing migration: {app}.{name}'))

        self.stdout.write('Running migrate...')
        call_command('migrate', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))

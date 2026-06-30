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

        # Each entry: (app, name, condition) — only fake if condition is True,
        # meaning the schema changes from that migration already exist in the DB.
        candidates = [
            ('accounts', '0001_initial',              _table_exists('accounts_user')),
            ('accounts', '0002_client',               _table_exists('accounts_client')),
            ('accounts', '0003_caregiver',            _table_exists('accounts_caregiver')),
            ('accounts', '0004_align_client_to_erd',  _column_exists('accounts_client', 'care_needs')),
            ('accounts', '0005_visit',                _table_exists('accounts_visit')),
            ('accounts', '0006_visit_gps_checkin',    _column_exists('accounts_visit', 'check_in_lat')),
        ]

        for app, name, already_exists in candidates:
            if already_exists and (app, name) not in applied:
                recorder.record_applied(app, name)
                self.stdout.write(self.style.WARNING(f'Faked missing migration: {app}.{name}'))

        self.stdout.write('Running migrate...')
        call_command('migrate', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))

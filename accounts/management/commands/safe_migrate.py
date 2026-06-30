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
    help = 'Migrate safely by fixing false migration records and faking already-applied ones'

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        applied = {(m.app, m.name) for m in recorder.migration_qs}

        # --- Step 1: Remove falsely recorded migrations ---
        # If a migration is recorded as applied but its schema changes don't
        # actually exist, remove the record so Django re-runs it.
        falsely_recorded = [
            ('accounts', '0005_visit',           not _table_exists('accounts_visit')),
            ('accounts', '0006_visit_gps_checkin', not _column_exists('accounts_visit', 'check_in_lat')),
        ]
        for app, name, should_remove in falsely_recorded:
            if should_remove and (app, name) in applied:
                recorder.record_unapplied(app, name)
                applied.discard((app, name))
                self.stdout.write(self.style.WARNING(f'Removed false record: {app}.{name}'))

        # --- Step 2: Fake migrations whose schema already exists but aren't recorded ---
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
                applied.add((app, name))
                self.stdout.write(self.style.WARNING(f'Faked missing migration: {app}.{name}'))

        # --- Step 3: Run migrate to apply any genuinely new migrations ---
        self.stdout.write('Running migrate...')
        call_command('migrate', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))

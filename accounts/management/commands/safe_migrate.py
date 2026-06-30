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
    help = 'Migrate safely, handling inconsistent migration history on shared databases'

    def handle(self, *args, **options):
        recorder = MigrationRecorder(connection)
        recorder.ensure_schema()
        applied = {(m.app, m.name) for m in recorder.migration_qs}

        # If accounts_user does not exist the whole accounts schema is missing.
        # We cannot use the migration executor (it errors because applied admin
        # migrations reference accounts.User before it exists in the state).
        # Instead, create all accounts tables directly from the current model
        # definitions, then fake every accounts migration so Django sees them as
        # applied and the consistency check passes.
        if not _table_exists('accounts_user'):
            self.stdout.write('Creating accounts tables from model definitions...')
            from accounts.models import User, Client, Caregiver, Visit
            with connection.schema_editor() as editor:
                editor.create_model(User)
                editor.create_model(Client)
                editor.create_model(Caregiver)
                editor.create_model(Visit)
            self.stdout.write(self.style.SUCCESS('Tables created.'))

            # Fake every accounts migration — the schema is now fully up to date.
            accounts_migrations = [
                '0001_initial',
                '0002_client',
                '0003_caregiver',
                '0004_align_client_to_erd',
                '0005_visit',
                '0006_visit_gps_checkin',
            ]
            for name in accounts_migrations:
                if ('accounts', name) not in applied:
                    recorder.record_applied('accounts', name)
                    applied.add(('accounts', name))
                    self.stdout.write(self.style.WARNING(f'Faked accounts.{name}'))

        else:
            # Tables exist — sync migration records with the actual schema.
            migrations = [
                ('accounts', '0001_initial',              _table_exists('accounts_user')),
                ('accounts', '0002_client',               _table_exists('accounts_client')),
                ('accounts', '0003_caregiver',            _table_exists('accounts_caregiver')),
                ('accounts', '0004_align_client_to_erd',  _column_exists('accounts_client', 'care_needs')),
                ('accounts', '0005_visit',                _table_exists('accounts_visit')),
                ('accounts', '0006_visit_gps_checkin',    _column_exists('accounts_visit', 'check_in_lat')),
            ]
            for app, name, schema_exists in migrations:
                if schema_exists and (app, name) not in applied:
                    recorder.record_applied(app, name)
                    applied.add((app, name))
                    self.stdout.write(self.style.WARNING(f'Faked missing migration: {app}.{name}'))
                elif not schema_exists and (app, name) in applied:
                    recorder.record_unapplied(app, name)
                    applied.discard((app, name))
                    self.stdout.write(self.style.WARNING(f'Removed false record: {app}.{name}'))

        # Run full migrate — consistency check now passes because accounts.0001_initial
        # is recorded. Any remaining unapplied migrations (other apps) run here.
        self.stdout.write('Running migrate...')
        call_command('migrate', verbosity=1)
        self.stdout.write(self.style.SUCCESS('Done.'))

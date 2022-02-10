import os
import sys

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand, call_command
from icecream import ic


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument('--app_prefix',
            action='store',
            dest='app_prefix',
            default=None,
            help='Import starts from line number',
            type=str
        )

    def handle(self, *args, **options):
        print('CLEANING MIGRATIONS')

        app_prefix = options.get('app_prefix', None)

        if app_prefix is None:
            exit('--app_prefix is required!')

        # check if all database migrations are applied already
        # if not is_database_synchronized():
        #     # Unapplied migrations found.
        #     # call_command('showmigrations')
        #     # call_command('migrate', '--check')
        #     print('Database is not synchronised! You should run "migrate" command at first!')
        #
        #     if input("Continue anyway? (Y)es/(N)o: ").lower() != 'y':
        #         exit('Canceled')

        # get all installed apps with the given prefix
        app_names = list(filter(lambda x: x.startswith(app_prefix), settings.INSTALLED_APPS))
        ic(app_names)

        if input("Confirm? (Y)es/(N)o: ").lower() != 'y':
            exit('Canceled')

        # get apps with migrations
        apps_with_migrations = self.get_apps_with_migrations(app_names)

        # prepare SQL delete statements
        self.sql_delete_statements(apps_with_migrations, dry_run=True)

        if input("Confirm? (Y)es/(N)o: ").lower() != 'y':
            exit('Canceled')

        self.sql_delete_statements(apps_with_migrations, dry_run=False)

        # delete app migration files
        self.migration_files(apps_with_migrations, dry_run=True)

        if input("Confirm? (Y)es/(N)o: ").lower() != 'y':
            exit('Canceled')

        self.migration_files(apps_with_migrations, dry_run=False)

        # prepare SQL statements
        self.make_migrations(apps_with_migrations, dry_run=True)

        if input("Confirm? (Y)es/(N)o: ").lower() != 'y':
            exit('Canceled')

        self.make_migrations(apps_with_migrations, dry_run=False)

        print('Done')

    def get_apps_with_migrations(self, app_names):
        apps_with_migrations = []

        for app_name in app_names:
            app = get_app_config_by_name(app_name)

            if app:
                # check if migrations folder exists
                if os.path.isdir(f'{path_to_app(app_name)}/migrations'):
                    apps_with_migrations.append(app)
                else:
                    print(f'Migrations for app "{app_name}" not available ({path_to_app(app_name)}/migrations)')
            else:
                print(f'App config for app "{app_name}" not found')

        return apps_with_migrations

    def sql_delete_statements(self, apps, dry_run):
        for app in apps:
            sql = f"delete from django_migrations where app = '{app.label}' and name != '0001_initial';"

            if dry_run:
                print(sql)
            else:
                execute_sql(sql)

    def make_migrations(self, apps, dry_run):
        for app in apps:
            if dry_run:
                print(f'makemigrations {app.label}')
            else:
                call_command('makemigrations', app.label)

    def migration_files(self, apps, dry_run):
        for app in apps:
            migrations_folder = f'{path_to_app(app.name)}/migrations'

            for filename in os.listdir(migrations_folder):
                if filename.startswith('__') or not filename.endswith('.py'):
                    continue

                file_path = os.path.join(migrations_folder, filename)

                if dry_run:
                    print(f'Remove file {file_path}')
                else:
                    try:
                        # os.unlink(file_path)
                        os.remove(file_path)
                    except Exception as e:
                        print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_app_config_by_name(name):
    for app_config in apps.get_app_configs():
        if app_config.name == name:
            return app_config

    return None


def path_to_app(app_name):
    root = sys.path[0]
    app_path = '/'.join(app_name.split('.'))
    return f'{root}/{app_path}'


from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS


def execute_sql(sql, database=DEFAULT_DB_ALIAS):
    connection = connections[database]

    with connection.cursor() as cursor:
        cursor.execute(sql)


def is_database_synchronized(database=DEFAULT_DB_ALIAS):
    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return not executor.migration_plan(targets)

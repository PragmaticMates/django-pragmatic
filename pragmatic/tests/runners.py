import better_exceptions
from unittest import TextTestResult, TextTestRunner

from django.db import connections, DEFAULT_DB_ALIAS
from django.test.runner import DiscoverRunner


class BetterTextTestResult(TextTestResult):
    def _exc_info_to_string(self, err, test):
        # better-exceptions format
        # https://github.com/Qix-/better-exceptions#use-with-unittest
        return "".join(better_exceptions.format_exception(*err))


class BetterTextTestRunner(TextTestRunner):
    resultclass = BetterTextTestResult


class ExtensionDiscoverRunner(DiscoverRunner):
    test_runner = BetterTextTestRunner

    DB_EXTENSIONS = []

    def setup_databases(self, **kwargs):
        # https://code.djangoproject.com/ticket/31221 when running tests on already existing db without migrating
        from django.contrib.postgres.signals import get_hstore_oids
        get_hstore_oids.cache_clear()

        result = super().setup_databases(**kwargs)

        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()

        for extension in self.DB_EXTENSIONS:
            cursor.execute(f'CREATE EXTENSION IF NOT EXISTS {extension}')

        return result


class TeamcityExtensionDiscoverRunner(ExtensionDiscoverRunner):
    def run_suite(self, suite, **kwargs):
        from teamcity.unittestpy import TeamcityTestRunner
        return TeamcityTestRunner().run(suite)

import better_exceptions
from unittest import TestResult

from django.db import connections, DEFAULT_DB_ALIAS
from django.test.runner import DiscoverRunner


class ExtensionDiscoverRunner(DiscoverRunner):
    DB_EXTENSIONS = []

    def setup_databases(self, **kwargs):
        result = super().setup_databases(**kwargs)

        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()

        for extension in self.DB_EXTENSIONS:
            cursor.execute(f'CREATE EXTENSION IF NOT EXISTS {extension}')

        return result

    def run_tests(self, *args, **kwargs):
        # Enable better-exceptions for better display of exceptions
        # https://github.com/Qix-/better-exceptions#use-with-unittest
        def exc_info_to_string(self, err, test):
            return "".join(better_exceptions.format_exception(*err))

        TestResult._exc_info_to_string = exc_info_to_string

        super().run_tests(*args, **kwargs)

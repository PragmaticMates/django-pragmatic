Management Commands
===================

clean_migrations
----------------

Squashes all migrations for a set of apps that share a common name prefix.
Performs the following steps interactively (with confirmation prompts at each
stage):

1. Deletes all ``django_migrations`` rows for the matched apps except
   ``0001_initial``.
2. Deletes all migration ``.py`` files from each app's ``migrations/``
   folder.
3. Runs ``makemigrations`` for each app to generate a single fresh
   ``0001_initial`` migration.

.. code-block:: bash

    python manage.py clean_migrations --app_prefix myproject

The ``--app_prefix`` argument filters ``INSTALLED_APPS`` — only apps whose
name starts with the given prefix are processed.

.. warning::

   This command is destructive. Run it only when all existing migrations are
   already applied to the target database, and ensure the database schema
   matches what Django would generate from scratch.

Requires ``icecream`` (``pip install icecream``) for debug output.

rqscheduler
-----------

Starts an RQ Scheduler worker. This is a thin wrapper around
``django-rq``'s scheduler command, available through the pragmatic package.

.. code-block:: bash

    python manage.py rqscheduler
    python manage.py rqscheduler --queue default --interval 60

Requires ``django-rq`` and ``rq-scheduler`` to be installed.

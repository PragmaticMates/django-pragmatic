Background Jobs
===============

All job-related code is in ``pragmatic.jobs``. Requires ``django-rq`` and
``rq`` to be installed.

send_mail_in_background
-----------------------

An RQ job that calls ``email.send()`` on a pre-built ``EmailMessage`` /
``EmailMultiAlternatives`` object. Dispatched automatically by
:meth:`EmailManager.send_mail` when ``MAILS_QUEUE`` is configured.

.. code-block:: python

    from pragmatic.jobs import send_mail_in_background

    send_mail_in_background.delay(email_message)

The queue used is ``settings.MAILS_QUEUE`` (defaults to ``'default'`` if
the setting is absent).

ConnectionClosingWorker
-----------------------

An RQ ``Worker`` subclass that closes the database connection before forking
each job. Prevents child processes from inheriting a stale or shared DB
connection.

.. code-block:: python

    # rqworker management command or Procfile
    from pragmatic.jobs import ConnectionClosingWorker

Use in your worker startup command:

.. code-block:: bash

    python manage.py rqworker --worker-class pragmatic.jobs.ConnectionClosingWorker default

ConnectionClosingSimpleWorker
-----------------------------

Same as ``ConnectionClosingWorker`` but extends RQ's ``SimpleWorker``
(single-process, no forking). Useful for environments where forking is
unavailable (e.g. Windows, some container setups).

.. code-block:: bash

    python manage.py rqworker --worker-class pragmatic.jobs.ConnectionClosingSimpleWorker default

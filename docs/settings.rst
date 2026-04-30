Settings Reference
==================

All settings are optional. Defaults are shown where applicable.

Core
----

.. setting:: PRAGMATIC_TRACK_DELETED_OBJECTS

``PRAGMATIC_TRACK_DELETED_OBJECTS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default: ``False``

When ``True``, :class:`DeleteObjectMixin` records every deleted object in the
``DeletedObject`` table, storing the content type, object id, string
representation, and the user who performed the deletion.

.. code-block:: python

    PRAGMATIC_TRACK_DELETED_OBJECTS = True

.. setting:: PRAGMATIC_TASK_DECORATOR

``PRAGMATIC_TASK_DECORATOR``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default: ``'django.tasks.task'``

Import path of the task decorator used by :func:`get_task_decorator`. Set this
to your background task backend of choice:

.. code-block:: python

    # Django 6.0+ built-in tasks
    PRAGMATIC_TASK_DECORATOR = 'django.tasks.task'

    # django-rq
    PRAGMATIC_TASK_DECORATOR = 'django_rq.job'

    # Celery
    PRAGMATIC_TASK_DECORATOR = 'celery.shared_task'

.. setting:: DEFAULT_PERMISSIONS

``DEFAULT_PERMISSIONS``
~~~~~~~~~~~~~~~~~~~~~~~

Default: ``('add', 'change', 'delete', 'view')``

Overrides the ``default_permissions`` Meta option on the ``DeletedObject``
model.

Maintenance Mode
----------------

.. setting:: MAINTENANCE_MODE

``MAINTENANCE_MODE``
~~~~~~~~~~~~~~~~~~~~

Default: ``False``

Set to ``True`` to activate :class:`MaintenanceModeMiddleware`. All requests
will receive a 503 response rendered from ``maintenance_mode.html``.

.. setting:: MAINTENANCE_MODE_BYPASS_USERS

``MAINTENANCE_MODE_BYPASS_USERS``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default: ``[]``

A list of user primary keys that are exempt from maintenance mode.

.. code-block:: python

    MAINTENANCE_MODE_BYPASS_USERS = [1, 42]

Email / Background Queue
------------------------

.. setting:: MAILS_QUEUE

``MAILS_QUEUE``
~~~~~~~~~~~~~~~

Default: ``None``

RQ queue name used by :meth:`EmailManager.send_mail`. When set, emails are
dispatched asynchronously via ``send_mail_in_background.delay()``. When
``None``, emails are sent synchronously.

.. code-block:: python

    MAILS_QUEUE = 'default'

PDF Generation
--------------

.. setting:: HTMLTOPDF_API_URL

``HTMLTOPDF_API_URL``
~~~~~~~~~~~~~~~~~~~~~

URL of an HTML-to-PDF conversion API endpoint, used by
:class:`PdfDetailMixin`. The mixin POSTs rendered HTML to this URL and
streams the PDF response back.

.. setting:: PRINTMYWEB_URL

``PRINTMYWEB_URL``
~~~~~~~~~~~~~~~~~~

Alternative HTML-to-PDF endpoint (takes precedence is superseded by
``HTMLTOPDF_API_URL`` if both are set — ``HTMLTOPDF_API_URL`` wins).

.. setting:: PRINTMYWEB_TOKEN

``PRINTMYWEB_TOKEN``
~~~~~~~~~~~~~~~~~~~~

API key sent as an ``api-key`` request header when calling the
``PRINTMYWEB_URL`` endpoint.

Context Processors
------------------

.. setting:: DATE_FORMAT_JS

``DATE_FORMAT_JS``
~~~~~~~~~~~~~~~~~~

JavaScript date format string exposed by the ``date_formats`` context
processor.

.. setting:: DATE_FORMAT_TAG

``DATE_FORMAT_TAG``
~~~~~~~~~~~~~~~~~~~

Django template date format tag string, exposed by ``date_formats``.

.. setting:: DATE_FORMAT_FULLMONTH_TAG

``DATE_FORMAT_FULLMONTH_TAG``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Full-month date format tag, exposed by ``date_formats``.

Signals / APM
-------------

.. setting:: APM_DEBUG

``APM_DEBUG``
~~~~~~~~~~~~~

Default: ``False``

When ``True``, prints APM context messages to stdout (useful during
development when ``elastic-apm`` is not installed).

.. setting:: TEST_PRINT_TASKS

``TEST_PRINT_TASKS``
~~~~~~~~~~~~~~~~~~~~

Default: ``True``

Controls whether ``SignalsHelper`` prints task debug output when
``settings.DEBUG`` is ``True``.

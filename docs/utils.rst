Utilities
=========

All utilities are in ``pragmatic.utils``.

build_absolute_uri
------------------

Builds an absolute URI, gracefully handling the case where no request is
available by falling back to ``django.contrib.sites``.

.. code-block:: python

    from pragmatic.utils import build_absolute_uri

    # With a request (delegates to request.build_absolute_uri)
    url = build_absolute_uri(request, '/path/to/page/')

    # Without a request (requires django.contrib.sites)
    url = build_absolute_uri(None, '/path/to/page/')
    url = build_absolute_uri(None, '/path/to/page/', protocol='https')

When ``request`` is ``None``:

- ``django.contrib.sites`` must be in ``INSTALLED_APPS``
- Protocol defaults to ``'http'`` in DEBUG mode, ``'https'`` in production
- The domain is read from the current ``Site`` object

This function is also available as the ``{% uri %}`` template tag:

.. code-block:: django

    {% load pragmatic_tags %}
    {% uri '/path/to/page/' %}

get_task_decorator
------------------

Returns the task decorator configured by ``PRAGMATIC_TASK_DECORATOR``.
Abstracts away the differences between Django's built-in tasks, django-rq,
and Celery.

.. code-block:: python

    from pragmatic.utils import get_task_decorator

    task = get_task_decorator()

    @task
    def my_background_task(arg):
        ...

    # With a named RQ queue
    job = get_task_decorator(queue='high')

    @job
    def priority_task():
        ...

The ``queue`` parameter is only used when ``PRAGMATIC_TASK_DECORATOR`` is
``'django_rq.job'``.

Raises ``ImportError`` if the configured decorator's module is not installed.

compress
--------

Creates an in-memory ZIP file from a list of ``{'name': ..., 'content': ...}``
dicts.

.. code-block:: python

    from pragmatic.utils import compress

    files = [
        {'name': 'report.csv', 'content': csv_bytes},
        {'name': 'summary.txt', 'content': 'Summary text'},
    ]
    zip_buffer = compress(files)

    # In a Django view
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="export.zip"'
    return response

Returns a ``BytesIO`` object seeked to position 0.

import_name
-----------

Dynamically imports a name from a dotted module path string.

.. code-block:: python

    from pragmatic.utils import import_name

    MyClass = import_name('myapp.models.MyClass')
    instance = MyClass()

Context Processors
==================

All context processors are in ``pragmatic.context_processors``.

date_formats
------------

Exposes date format strings from settings to every template.

.. code-block:: python

    # settings.py
    TEMPLATES = [{
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'pragmatic.context_processors.date_formats',
            ],
        },
    }]

    DATE_FORMAT_JS = 'DD/MM/YYYY'
    DATE_FORMAT_TAG = 'd/m/Y'
    DATE_FORMAT_FULLMONTH_TAG = 'j F Y'

Adds to context: ``DATE_FORMAT_JS``, ``DATE_FORMAT_TAG``,
``DATE_FORMAT_FULLMONTH_TAG``.

installed_apps
--------------

Adds the ``INSTALLED_APPS`` list to every template context.

.. code-block:: python

    'pragmatic.context_processors.installed_apps',

Adds to context: ``INSTALLED_APPS``.

Use case: conditionally showing UI elements based on which apps are installed.

.. code-block:: django

    {% if 'billing' in INSTALLED_APPS %}
        <a href="{% url 'billing:dashboard' %}">Billing</a>
    {% endif %}

url_identifier
--------------

Adds URL name and namespace information to every template context.

.. code-block:: python

    'pragmatic.context_processors.url_identifier',

Adds to context:

- ``url_name`` — the resolved URL name (e.g. ``'article-detail'``)
- ``url_namespaces`` — list of namespaces (e.g. ``['blog']``)
- ``url_id`` — colon-joined full identifier (e.g. ``'blog:article-detail'``)

Use case: applying active CSS classes to navigation links.

.. code-block:: django

    <a class="{% if url_id == 'blog:article-list' %}active{% endif %}"
       href="{% url 'blog:article-list' %}">Articles</a>

settings
--------

Exposes the entire Django ``settings`` module to templates.

.. code-block:: python

    'pragmatic.context_processors.settings',

Adds to context: ``settings``.

.. warning::

   This makes all settings (including sensitive values) available in
   templates. Use only in trusted, internal projects.

Installation
============

Requirements
------------

- Python 3.8+
- Django 3.2+
- `django-filter <https://django-filter.readthedocs.io/>`_
- `python-pragmatic <https://github.com/PragmaticMates/python-pragmatic>`_

Optional dependencies (required only for the modules that use them):

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Package
     - Used by
   * - ``djangorestframework``
     - ``serializers``, ``routers``, ``authentication``
   * - ``django-rq``
     - ``jobs``, ``managers`` (background email), ``rqscheduler`` command
   * - ``fpdf2``
     - ``FPDFMixin``
   * - ``requests``, ``PyPDF2``
     - ``PdfDetailMixin``
   * - ``django-select2``
     - ``AutoSlugResponseView``
   * - ``django-map-widgets``
     - ``AutocompleteGooglePointFieldWidget``, ``AutocompleteCityWidget``
   * - ``django-debug-toolbar``
     - ``SQLPanel``
   * - ``elastic-apm``
     - ``apm_custom_context`` (optional, gracefully absent)
   * - ``icecream``
     - ``clean_migrations`` management command
   * - ``python-dateutil``
     - ``add_months`` template filter

Install
-------

.. code-block:: bash

    pip install django-pragmatic

Add ``pragmatic`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        ...
        'pragmatic',
    ]

Run migrations to create the ``DeletedObject`` table (only needed if you use
:ref:`deleted-object-tracking`):

.. code-block:: bash

    python manage.py migrate pragmatic

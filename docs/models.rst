Models
======

.. _deleted-object-tracking:

DeletedObject
-------------

``pragmatic.models.DeletedObject``

Stores an audit record whenever a model instance is deleted through
:class:`DeleteObjectMixin`. Requires ``PRAGMATIC_TRACK_DELETED_OBJECTS = True``
in your settings.

.. code-block:: python

    from pragmatic.models import DeletedObject

Fields:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Field
     - Description
   * - ``content_type``
     - FK to ``ContentType`` (the model class that was deleted)
   * - ``object_id``
     - The primary key of the deleted instance
   * - ``object_str``
     - ``str(instance)`` captured before deletion (max 300 chars)
   * - ``user``
     - FK to the user who triggered the deletion; ``NULL`` for unauthenticated
   * - ``datetime``
     - Timestamp of deletion (auto-set, db-indexed)

The model uses ``get_latest_by = 'datetime'`` and orders by ``datetime``
ascending.

Setup
~~~~~

1. Enable tracking in settings:

   .. code-block:: python

       PRAGMATIC_TRACK_DELETED_OBJECTS = True

2. Run migrations:

   .. code-block:: bash

       python manage.py migrate pragmatic

3. Use :class:`DeleteObjectMixin` (or :class:`CheckProtectedDeleteObjectMixin`)
   on your delete views — records are created automatically.

REST Framework
==============

These components require ``djangorestframework`` to be installed.

Authentication
--------------

BearerAuthentication
~~~~~~~~~~~~~~~~~~~~

``pragmatic.authentication.BearerAuthentication``

Extends DRF's ``TokenAuthentication`` to accept ``Bearer`` tokens instead of
the default ``Token`` prefix. Drop-in for APIs that follow the OAuth2 / JWT
convention.

.. code-block:: python

    # settings.py
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'pragmatic.authentication.BearerAuthentication',
        ],
    }

Clients send:

.. code-block:: http

    Authorization: Bearer <token>

Serializers
-----------

ContentTypeSerializer
~~~~~~~~~~~~~~~~~~~~~

``pragmatic.serializers.ContentTypeSerializer``

A ``ModelSerializer`` for ``ContentType`` that serialises instances as
``'app_label.model'`` strings and accepts the same format on input.

.. code-block:: python

    from pragmatic.serializers import ContentTypeSerializer

    class MySerializer(serializers.Serializer):
        content_type = ContentTypeSerializer()

- ``to_representation`` → returns ``'app_label.model'``
- ``to_internal_value`` → accepts ``'app_label.model'`` or
  ``{'app_label': ..., 'model': ...}``

ContentTypeNaturalField
~~~~~~~~~~~~~~~~~~~~~~~

``pragmatic.serializers.ContentTypeNaturalField``

A ``PrimaryKeyRelatedField`` that represents a ``ContentType`` as its natural
key string (``'app_label.model'``) on both read and write.

.. code-block:: python

    from pragmatic.serializers import ContentTypeNaturalField

    class EventSerializer(serializers.ModelSerializer):
        content_type = ContentTypeNaturalField()

Routers
-------

HybridRouter
~~~~~~~~~~~~

``pragmatic.routers.HybridRouter``

Extends DRF's ``DefaultRouter`` to allow mixing ViewSet-based URLs (registered
with ``router.register()``) and plain ``APIView``-based URLs (added with
``router.add_url()``). All registered views are listed in the browsable API
root.

.. code-block:: python

    from pragmatic.routers import HybridRouter
    from django.urls import path
    from myapp.views import ArticleViewSet, StatsView

    router = HybridRouter()
    router.register('articles', ArticleViewSet, basename='article')
    router.add_url(path('stats/', StatsView.as_view(), name='stats'))

    urlpatterns = router.urls

The API root lists all ViewSet URLs plus the manually added URLs, sorted
alphabetically by name.

Select2 Views
-------------

AutoSlugResponseView
~~~~~~~~~~~~~~~~~~~~~

``pragmatic.select2.AutoSlugResponseView``

Extends ``django-select2``'s ``AutoResponseView`` to return each object's
``slug`` as the ``id`` in the JSON response (instead of the primary key).

.. code-block:: python

    # urls.py
    from pragmatic.select2 import AutoSlugResponseView

    urlpatterns = [
        path('select2/auto/', AutoSlugResponseView.as_view(), name='django_select2-json'),
    ]

Requires ``django-select2`` to be installed.

Debug Toolbar Panel
-------------------

SQLPanel
~~~~~~~~

``pragmatic.panels.SQLPanel``

Extends ``django-debug-toolbar``'s ``SQLPanel`` to add an ``EXPLAIN ANALYZE``
endpoint alongside the existing ``SELECT`` and ``PROFILE`` views.

.. code-block:: python

    # settings.py
    DEBUG_TOOLBAR_PANELS = [
        ...
        'pragmatic.panels.SQLPanel',
    ]

The ``sql_explain`` view runs:

- ``EXPLAIN QUERY PLAN <sql>`` on SQLite
- ``EXPLAIN ANALYZE <sql>`` on PostgreSQL
- ``EXPLAIN <sql>`` on other databases

Requires ``django-debug-toolbar`` and ``sqlparse`` to be installed.

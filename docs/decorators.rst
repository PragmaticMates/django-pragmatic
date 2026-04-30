Decorators
==========

All decorators live in ``pragmatic.decorators``.

Permission Decorators
---------------------

permissions_required
~~~~~~~~~~~~~~~~~~~~

Checks that the user has **at least one** permission in the given app.

.. code-block:: python

    from pragmatic.decorators import permissions_required

    @permissions_required('billing', raise_exception=True)
    def billing_dashboard(request):
        ...

Parameters:

- ``app_label`` — Django app label (e.g. ``'billing'``)
- ``login_url`` — redirect URL for unauthenticated users (defaults to
  ``settings.LOGIN_URL``)
- ``raise_exception`` — if ``True``, raises ``PermissionDenied`` and stores
  ``app_label`` on ``request.user.permission_error``

permission_required
~~~~~~~~~~~~~~~~~~~

Checks that the user has a **specific permission**.

.. code-block:: python

    from pragmatic.decorators import permission_required

    @permission_required('billing.view_invoice', raise_exception=True)
    def invoice_list(request):
        ...

Parameters:

- ``perm`` — dotted permission string, e.g. ``'app_label.codename'``
- ``login_url`` — redirect URL for unauthenticated users
- ``raise_exception`` — if ``True``, raises ``PermissionDenied`` and stores
  the ``Permission`` object (or the raw string) on
  ``request.user.permission_error``

Signal Decorator
----------------

receiver_subclasses
~~~~~~~~~~~~~~~~~~~

Connects a signal receiver to a sender *and all of its subclasses*. Useful
for model inheritance hierarchies.

.. code-block:: python

    from django.db.models.signals import post_save
    from pragmatic.decorators import receiver_subclasses

    @receiver_subclasses(post_save, MyBaseModel, 'mybasemodel_post_save')
    def handle_save(sender, instance, **kwargs):
        ...

Parameters:

- ``signal`` — Django signal (e.g. ``post_save``)
- ``sender`` — base model class
- ``dispatch_uid_prefix`` — unique string; the actual ``dispatch_uid`` is
  ``{prefix}_{SubclassName}``

Database Decorator
------------------

require_lock
~~~~~~~~~~~~

Acquires a PostgreSQL table-level lock before executing the view function.
Must be used inside an atomic block.

.. code-block:: python

    from django.db import transaction
    from pragmatic.decorators import require_lock

    @transaction.atomic
    @require_lock(MyModel, 'ACCESS EXCLUSIVE')
    def my_view(request):
        ...

Supported lock modes (``LOCK_MODES``):
``ACCESS SHARE``, ``ROW SHARE``, ``ROW EXCLUSIVE``,
``SHARE UPDATE EXCLUSIVE``, ``SHARE``, ``SHARE ROW EXCLUSIVE``,
``EXCLUSIVE``, ``ACCESS EXCLUSIVE``.

Cache Utilities
---------------

Cached
~~~~~~

A context manager that wraps Django's cache. Read from cache on ``__enter__``;
call ``.save(data)`` to store the result.

.. code-block:: python

    from pragmatic.decorators import Cached

    def expensive_view(request):
        with Cached('my_cache_key', user=request.user, timeout=3600) as cached:
            if cached is not None:
                return cached

            result = expensive_computation()
            Cached('my_cache_key', user=request.user, timeout=3600).save(result)
            return result

Constructor parameters:

- ``key`` — cache key string
- ``version`` — cache version (optional)
- ``user`` — user object; used to build a per-user key when ``per_user=True``
- ``per_user`` — default ``True``; appends ``:user={pk}`` to the key
- ``timeout`` — cache timeout in seconds; ``0`` disables caching entirely

Cached.cache_decorator
~~~~~~~~~~~~~~~~~~~~~~~

A ``@property`` decorator that caches the return value of a method using the
instance's ``cache_key`` attribute.

.. code-block:: python

    from pragmatic.decorators import Cached

    class MyModel(models.Model):
        cache_key = 'mymodel'

        @Cached.cache_decorator()
        def expensive_property(self):
            return compute_something()

The cache key is ``{instance.cache_key}.{method_name}``. The cache version is
read from ``self.cache_version`` if it exists. Default timeout is 3600 seconds.

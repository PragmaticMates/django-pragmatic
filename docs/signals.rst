Signals
=======

All signal utilities are in ``pragmatic.signals``.

SignalsHelper
-------------

A utility class for deferring side-effect functions until after a model signal
fires. This avoids race conditions caused by executing related logic (e.g.
sending notifications) *inside* a ``pre_save`` handler before the transaction
commits.

add_task_and_connect
~~~~~~~~~~~~~~~~~~~~

Register a function to be called after a signal fires on a specific instance.

.. code-block:: python

    from pragmatic.signals import SignalsHelper
    from django.db.models.signals import post_save

    def pre_save_handler(sender, instance, **kwargs):
        # Schedule notification to run after the record is saved
        SignalsHelper.add_task_and_connect(
            sender=sender,
            instance=instance,
            func=send_notification,
            arguments=(instance.pk,),
            signal_type='post_save',  # 'post_save' | 'post_delete' | 'm2m_changed'
        )

    post_save.connect(pre_save_handler, sender=MyModel)

``execute_instance_tasks`` is called by the connected receiver and processes
all queued tasks for the instance, then clears the queue.

attribute_changed
~~~~~~~~~~~~~~~~~

Compares the current in-memory instance against the database to detect field
changes. Useful in ``pre_save`` handlers.

.. code-block:: python

    from pragmatic.signals import SignalsHelper

    def my_pre_save(sender, instance, **kwargs):
        if SignalsHelper.attribute_changed(instance, diff_fields=['status']):
            # status was changed
            ...

        # Check specific value transitions
        if SignalsHelper.attribute_changed(
            instance,
            diff_fields=['status'],
            diff_contains={'status': {'from': ['draft'], 'to': ['published']}}
        ):
            # status changed from draft → published
            ...

Parameters of ``attribute_changed``:

- ``instance`` — unsaved model instance
- ``diff_fields`` — list of field names to check
- ``diff_contains`` — optional dict constraining which values trigger a
  ``True`` result; accepts either a list (any match) or a
  ``{'from': [...], 'to': [...]}`` dict
- ``obj_exists`` — when ``True``, returns ``False`` for new (unsaved) objects
  instead of ``True``

Returns ``True`` if any of the listed fields changed (within the optional
constraints), or if the object did not previously exist (and ``obj_exists``
is ``False``).

get_db_instance
~~~~~~~~~~~~~~~

Fetches the currently persisted version of an instance from the database.

.. code-block:: python

    db_instance = SignalsHelper.get_db_instance(instance)
    if db_instance and db_instance.status != instance.status:
        ...

Returns ``None`` if the object does not yet exist in the database.

APM Integration
---------------

apm_custom_context
~~~~~~~~~~~~~~~~~~

A decorator that attaches signal/task context to an active Elastic APM
transaction. Silently no-ops if ``elastic-apm`` is not installed.

.. code-block:: python

    from pragmatic.signals import apm_custom_context

    @apm_custom_context('signals')
    def my_signal_handler(sender, instance, **kwargs):
        ...

    @apm_custom_context('tasks')
    def my_task(arg1, arg2):
        ...

Types: ``'signals'`` (reads ``instance`` from kwargs) and ``'tasks'``
(logs the call arguments).

Context Managers
----------------

temporary_disconnect_signal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Temporarily disconnects a signal receiver and reconnects it on exit.
Safe for use in tests or bulk-import scripts.

.. code-block:: python

    from pragmatic.signals import temporary_disconnect_signal
    from django.db.models.signals import post_save

    with temporary_disconnect_signal(
        signal=post_save,
        receiver=my_handler,
        sender=MyModel,
        dispatch_uid='my_uid',  # optional
    ):
        MyModel.objects.bulk_create(objects)

The receiver is only disconnected if it was actually connected when the context
is entered; it is always reconnected on exit.

disable_signals
~~~~~~~~~~~~~~~

Disables a set of Django model signals for the duration of a block. By default
disables all standard signals (``pre_init``, ``post_init``, ``pre_save``,
``post_save``, ``pre_delete``, ``post_delete``, ``pre_migrate``,
``post_migrate``, ``m2m_changed``).

.. code-block:: python

    from pragmatic.signals import disable_signals

    # Disable all signals
    with disable_signals():
        do_bulk_operation()

    # Disable only specific signals
    with disable_signals(disabled_signals=[post_save, pre_save]):
        do_bulk_operation()

    # Keep only specific signals enabled
    with disable_signals(enabled_signals=[post_save]):
        do_bulk_operation()

    # Disable specific receivers by name
    with disable_signals(disabled_receviers=['my_expensive_receiver']):
        do_bulk_operation()

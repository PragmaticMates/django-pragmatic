django-pragmatic
================

Pragmatic tools and utilities for Django projects.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   settings

.. toctree::
   :maxdepth: 2
   :caption: Reference

   models
   mixins
   decorators
   templatetags
   fields
   filters
   widgets
   middleware
   managers
   context_processors
   signals
   utils
   jobs
   rest_framework
   management_commands

Overview
--------

**django-pragmatic** is a collection of reusable building blocks for Django projects.
All components are independent and can be used selectively — include only what you need.

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Module
     - What it provides
   * - :doc:`models`
     - ``DeletedObject`` — audit trail for deleted model instances
   * - :doc:`mixins`
     - CBV and form mixins for permissions, deletion, list views, PDF, slugs
   * - :doc:`decorators`
     - View decorators, PostgreSQL table lock, cache context manager
   * - :doc:`templatetags`
     - ``{% load pragmatic_tags %}`` — filter values, sorting, pagination, URL tools
   * - :doc:`fields`
     - ``RangeField``, ``SliderField``, ``MultiSelectField``, ``ChoiceArrayField``
   * - :doc:`filters`
     - django-filters extensions: ``SliderFilter``, ``OneFieldRangeFilter``, etc.
   * - :doc:`widgets`
     - ``GroupedCheckboxSelectMultiple``, ``SliderWidget``, map widgets
   * - :doc:`middleware`
     - ``MaintenanceModeMiddleware`` — serve 503 during downtime
   * - :doc:`managers`
     - ``EmailManager`` — template-based email with optional RQ background queue
   * - :doc:`context_processors`
     - Date formats, installed apps, URL identifier, settings
   * - :doc:`signals`
     - ``SignalsHelper``, APM integration, ``temporary_disconnect_signal``
   * - :doc:`utils`
     - ``build_absolute_uri``, ``get_task_decorator``, zip compression
   * - :doc:`jobs`
     - Background email via RQ, ``ConnectionClosingWorker``
   * - :doc:`rest_framework`
     - ``ContentTypeSerializer``, ``HybridRouter``, ``BearerAuthentication``
   * - :doc:`management_commands`
     - ``clean_migrations``, ``rqscheduler``

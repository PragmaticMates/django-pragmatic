Filters
=======

All filters extend ``django-filter`` and live in ``pragmatic.filters``.

SliderFilter
------------

Integrates :class:`SliderField` with django-filter. Supports single-value and
range filtering. Optionally loads min/max/distribution data from the database
and caches it.

.. code-block:: python

    import django_filters
    from pragmatic.filters import SliderFilter

    class ProductFilter(django_filters.FilterSet):
        price = SliderFilter(
            field_name='price',
            min_value=0,
            max_value=500,
            step=5,
            has_range=True,
            appended_text='€',
            # Optional: auto-compute min/max/distribution from the DB
            segment='myapp.Product.price',
            count=20,               # number of histogram segments
            queryset_method='all',  # manager method to call
        )

        class Meta:
            model = Product
            fields = ['price']

The ``segment`` argument takes an ``'app_label.ModelName.field_name'`` string.
On first use, it queries the database for ``min``, ``max``, and a count
distribution across ``count`` equal-width buckets, then caches the result for
24 hours (86 400 s).

.. note::

   When ``has_range=True`` the filter applies ``field__gte`` for ``value.start``
   and ``field__lte`` for ``value.stop``. For single-value mode it delegates to
   the parent filter with the configured ``lookup_expr`` (default: ``'lte'``).

OneFieldRangeFilter
-------------------

Uses :class:`RangeField` to filter with a single ``start-stop`` text input.

.. code-block:: python

    from pragmatic.filters import OneFieldRangeFilter

    class OrderFilter(django_filters.FilterSet):
        quantity = OneFieldRangeFilter(field_name='quantity')

Applies ``field__range=(start, stop)``.

TruncatedModelChoiceFilter
--------------------------

Filter field backed by :class:`TruncatedModelChoiceField`. Drop-in replacement
for ``django_filters.ModelChoiceFilter`` when labels need truncation.

.. code-block:: python

    from pragmatic.filters import TruncatedModelChoiceFilter

    class InvoiceFilter(django_filters.FilterSet):
        customer = TruncatedModelChoiceFilter(
            queryset=Customer.objects.all(),
            truncate_chars=40,
        )

ArrayFilter
-----------

Filters a PostgreSQL ``ArrayField`` by checking whether a given value is
contained in the array. Also checks indexed positions up to ``array_size``.

.. code-block:: python

    from pragmatic.filters import ArrayFilter

    class ArticleFilter(django_filters.FilterSet):
        tag = ArrayFilter(field_name='tags', array_size=10)

IntegerFilter
-------------

A ``NumberFilter`` that enforces an integer ``IntegerField`` form field.

.. code-block:: python

    from pragmatic.filters import IntegerFilter

    class StockFilter(django_filters.FilterSet):
        quantity = IntegerFilter(field_name='quantity', lookup_expr='gte')

PositiveBooleanFilter
---------------------

A ``BooleanFilter`` that passes the queryset through unchanged when the value
is falsy (i.e. only filters when ``True``).

.. code-block:: python

    from pragmatic.filters import PositiveBooleanFilter

    class ArticleFilter(django_filters.FilterSet):
        is_featured = PositiveBooleanFilter(field_name='is_featured')

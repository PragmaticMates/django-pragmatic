Fields
======

All fields are in ``pragmatic.fields``.

Form Fields
-----------

RangeField
~~~~~~~~~~

Accepts a single number or a range expressed as ``start-stop`` (e.g.
``10-50``). Returns a ``(start, stop)`` tuple.

.. code-block:: python

    from pragmatic.fields import RangeField

    class SearchForm(forms.Form):
        price = RangeField(required=False)

User input examples: ``"42"``, ``"10-100"``, ``"1.5-9.9"``.

TruncatedModelChoiceField
~~~~~~~~~~~~~~~~~~~~~~~~~

A ``ModelChoiceField`` whose option labels are truncated to
``truncate_chars`` characters, with ``truncate_suffix`` (default ``'...'``)
appended when truncation occurs.

.. code-block:: python

    from pragmatic.fields import TruncatedModelChoiceField

    class OrderForm(forms.Form):
        customer = TruncatedModelChoiceField(
            queryset=Customer.objects.all(),
            truncate_chars=40,
        )

AlwaysValidChoiceField
~~~~~~~~~~~~~~~~~~~~~~

A ``ChoiceField`` that accepts any value without validation. Useful when the
choice list is dynamic and populated client-side.

AlwaysValidMultipleChoiceField
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Same as ``AlwaysValidChoiceField`` but for multiple-select inputs.

MultiSelectFormField
~~~~~~~~~~~~~~~~~~~~

A ``MultipleChoiceField`` rendered as ``CheckboxSelectMultiple``.

.. code-block:: python

    from pragmatic.fields import MultiSelectFormField

    class TagForm(forms.Form):
        tags = MultiSelectFormField(choices=TAG_CHOICES)

SliderField
~~~~~~~~~~~

A range-slider form field backed by :class:`SliderWidget`. Returns a scalar
value or a ``slice(start, stop)`` depending on ``has_range``.

.. code-block:: python

    from pragmatic.fields import SliderField

    class FilterForm(forms.Form):
        price = SliderField(
            min_value=0,
            max_value=1000,
            step=10,
            has_range=True,      # True → range slider, False → single value
            show_value=True,     # display current value next to slider
            appended_text='€',   # unit suffix
            show_inputs=True,    # show text inputs alongside slider
            required=False,
        )

When ``has_range=False``, boundary values (equal to ``min_value``) are
coerced to ``None`` (treated as "no filter") unless ``required=True``.

Model Fields
------------

MultiSelectField
~~~~~~~~~~~~~~~~

A ``CharField``-based model field that stores multiple choices as a
comma-separated string. Use ``MultiSelectFormField`` as its form representation.

.. code-block:: python

    from pragmatic.fields import MultiSelectField

    COLOURS = (('R', 'Red'), ('G', 'Green'), ('B', 'Blue'))

    class Product(models.Model):
        colours = MultiSelectField(max_length=20, choices=COLOURS, blank=True)

.. note::

   ``MultiSelectField`` is a legacy field that predates
   ``django.contrib.postgres.fields.ArrayField``. For new PostgreSQL projects,
   prefer ``ChoiceArrayField`` below.

ChoiceArrayField
~~~~~~~~~~~~~~~~

A PostgreSQL ``ArrayField`` whose ``formfield()`` renders as
``CheckboxSelectMultiple``.

.. code-block:: python

    from pragmatic.fields import ChoiceArrayField
    from django.db import models

    STATUS_CHOICES = (('draft', 'Draft'), ('published', 'Published'))

    class Article(models.Model):
        statuses = ChoiceArrayField(
            models.CharField(max_length=20, choices=STATUS_CHOICES),
            default=list,
            blank=True,
        )

Requires ``django.contrib.postgres`` in ``INSTALLED_APPS`` and a PostgreSQL database.

ArrayFieldSelectMultiple
~~~~~~~~~~~~~~~~~~~~~~~~

A ``SelectMultiple`` widget that reads and writes a delimited string rather
than a list. Used as the default widget for ``ChoiceArrayField`` in some
contexts.

.. code-block:: python

    from pragmatic.fields import ArrayFieldSelectMultiple

    class ArticleForm(forms.ModelForm):
        class Meta:
            model = Article
            widgets = {
                'statuses': ArrayFieldSelectMultiple(delimiter=','),
            }

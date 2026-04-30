Widgets
=======

All widgets live in ``pragmatic.widgets``.

GroupedCheckboxSelectMultiple
-----------------------------

An advanced ``CheckboxSelectMultiple`` widget that organises choices into
named, collapsible groups with Bootstrap 3 panel styling. Each group has an
optional header checkbox that toggles all its children.

.. code-block:: python

    from pragmatic.widgets import GroupedCheckboxSelectMultiple
    from django.utils.translation import gettext_lazy as _

    class PermissionsForm(forms.Form):
        permissions = forms.MultipleChoiceField(
            choices=ALL_PERMISSIONS,
            widget=GroupedCheckboxSelectMultiple(attrs={
                'groups': (
                    (_('Billing'), {
                        'classes': ('col-md-4',),
                        'choices': (
                            ('billing.view_invoice', _('View invoices')),
                            ('billing.add_invoice',  _('Add invoices')),
                        ),
                        # Optional: check these values when the group is checked
                        # 'predefined_values_on_check': 'all' | None | ['val1', ...]
                    }),
                    (_('Reporting'), {
                        'classes': ('col-md-4',),
                        'choices': (
                            ('reports.view_report', _('View reports')),
                        ),
                    }),
                )
            }),
        )

``groups`` attribute format:

Each item is a ``(label, config)`` tuple where ``config`` is a dict with:

- ``choices`` (required) — iterable of ``(value, label)`` pairs
- ``classes`` — tuple of CSS classes applied to the group wrapper
- ``predefined_values_on_check`` — values to pre-check when the group header is ticked: ``'all'`` to check all, a list of specific values, or omit for no auto-check

The widget requires ``static/pragmatic/js/grouped-checkboxes.js`` in your
template.

SliderWidget
------------

A ``TextInput`` widget styled for use with a range slider (e.g.
`Bootstrap Slider <https://seiyria.com/bootstrap-slider/>`_).
Used by :class:`SliderField` and :class:`SliderFilter`.

.. code-block:: python

    from pragmatic.widgets import SliderWidget

    class FilterForm(forms.Form):
        price = forms.CharField(widget=SliderWidget(attrs={
            'data-slider-min': '0',
            'data-slider-max': '500',
        }))

Renders ``widgets/slider_input.html``. Default ``data-*`` attributes:

.. list-table::
   :widths: 40 60
   :header-rows: 1

   * - Attribute
     - Default
   * - ``data-slider-min``
     - ``'0'``
   * - ``data-slider-max``
     - ``'100'``
   * - ``data-slider-step``
     - ``'1'``
   * - ``data-slider-tooltip``
     - ``'show'``
   * - ``data-slider-show-value``
     - ``'true'``

Map Widgets (optional)
-----------------------

These widgets are available only when ``django-map-widgets`` is installed.

AutocompleteGooglePointFieldWidget
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extends ``mapwidgets.GooglePointFieldWidget`` to also load
``pragmatic/js/map-widget-utils.js``.

.. code-block:: python

    from pragmatic.widgets import AutocompleteGooglePointFieldWidget

    class LocationForm(forms.ModelForm):
        class Meta:
            model = Location
            widgets = {'coordinates': AutocompleteGooglePointFieldWidget()}

AutocompleteCityWidget
~~~~~~~~~~~~~~~~~~~~~~~

A ``TextInput`` that triggers a Google Places city autocomplete. Reads the
API key from ``mw_settings.GOOGLE_MAP_API_KEY`` and loads
``pragmatic/js/city-autocomplete.js``.

.. code-block:: python

    from pragmatic.widgets import AutocompleteCityWidget

    class AddressForm(forms.Form):
        city = forms.CharField(widget=AutocompleteCityWidget())

Template Tags
=============

Load the tag library in any template:

.. code-block:: django

    {% load pragmatic_tags %}

All tags and filters are defined in ``pragmatic.templatetags.pragmatic_tags``.

URL Tags
--------

translate_url
~~~~~~~~~~~~~

Switches a URL to another language, with smart fallback for object-specific URLs.

.. code-block:: django

    {# Switch current page to Slovak #}
    {% translate_url 'sk' %}

    {# Explicit path #}
    {% translate_url 'sk' path='/about/' %}

    {# Object URL via a callable #}
    {% translate_url 'sk' object=article callable='get_absolute_url' %}

uri
~~~

Builds an absolute URI from a relative path. Falls back to
``django.contrib.sites`` when ``request`` is not available.

.. code-block:: django

    {% uri '/path/to/page/' %}
    {% uri '/path/to/page/' protocol='https' %}

Requires ``django.contrib.sites`` in ``INSTALLED_APPS`` when used outside a
request context.

Query Parameter Filters
~~~~~~~~~~~~~~~~~~~~~~~

Manipulate the query string of a URL without a full page redirect.

.. code-block:: django

    {# Add ?page=2 only if not already present #}
    {{ request.get_full_path|add_query_param:"page=2" }}

    {# Replace or add ?display=table #}
    {{ request.get_full_path|replace_query_param:"display=table" }}

    {# Remove ?display= entirely #}
    {{ request.get_full_path|remove_query_param:"display" }}

Filter Value Tags
-----------------

filter_values
~~~~~~~~~~~~~

Inclusion tag that renders the active filter values as human-readable labels.
Renders ``helpers/filter_values.html``.

.. code-block:: django

    {% filter_values filter %}

filtered_values
~~~~~~~~~~~~~~~

Simple tag that returns a ``dict`` of active filter values keyed by parameter
name. Each value is ``{'label': ..., 'value': ...}``.

.. code-block:: django

    {% filtered_values filter request.GET as active_filters %}

num_applied_filters
~~~~~~~~~~~~~~~~~~~

Returns the count of active (non-empty) filter parameters.

.. code-block:: django

    {% num_applied_filters filter request.GET as n %}
    {{ n }} filter{{ n|pluralize }} applied

List View Tags
--------------

display_modes
~~~~~~~~~~~~~

Inclusion tag for switching between display modes defined on
:class:`DisplayListViewMixin`. Renders ``helpers/display_modes.html``.

.. code-block:: django

    {% display_modes %}

Provides context: ``displays`` (list of ``{mode, active, url, localized_mode}``
dicts) and ``paginate_values``.

sorting
~~~~~~~

Inclusion tag for sorting controls, driven by ``sorting_options`` from
:class:`SortingListViewMixin`. Renders ``helpers/sorting.html``.

.. code-block:: django

    {% sorting %}

paginator
~~~~~~~~~

Inclusion tag for pagination controls. Renders ``helpers/pagination.html``.

.. code-block:: django

    {% paginator page_obj %}
    {% paginator page_obj page_ident='p' anchor='results' adjacent=3 %}

Parameters:

- ``objects`` — the ``Page`` object from a paginated view
- ``page_ident`` — query parameter name (default: ``'page'``)
- ``anchor`` — URL fragment appended to page links
- ``adjacent`` — number of page links on each side of the current page (default: ``2``)

Admin Tags
----------

admin_chart
~~~~~~~~~~~

Renders a Chart.js bar or line chart for an admin change list. Requires
``templates/admin/chart.html`` to be included in your admin template.

.. code-block:: django

    {% admin_chart queryset label="New users" color="blue" type="line" date_field="date_joined" %}

Parameters:

- ``objects`` — a queryset
- ``label`` — chart dataset label
- ``color`` — CSS colour string (default: ``'red'``)
- ``type`` — chart type: ``'bar'`` or ``'line'`` (default: ``'bar'``)
- ``date_field`` — date/datetime field to group by (default: ``'created'``)

objects_stats
~~~~~~~~~~~~~

Returns an annotated ``values()`` queryset with ``count`` (and optionally
``sum``) per distinct value of an attribute.

.. code-block:: django

    {% objects_stats orders 'status' as stats %}
    {% objects_stats orders 'status' 'total' as stats %}

Utility Filters
---------------

get_item
~~~~~~~~

Dynamic attribute and key access — traverses dot-separated paths.

.. code-block:: django

    {{ my_dict|get_item:"key" }}
    {{ obj|get_item:"address.city" }}
    {{ my_list|get_item:0 }}

get_list
~~~~~~~~

Returns a list of values for a repeated query parameter from a ``QueryDict``.

.. code-block:: django

    {{ request.GET|get_list:"tag" }}

split
~~~~~

Splits a string by a separator.

.. code-block:: django

    {{ "a,b,c"|split:"," }}  {# → ['a', 'b', 'c'] #}

attribute
~~~~~~~~~

Returns ``getattr(value, attr)``.

.. code-block:: django

    {{ obj|attribute:"verbose_name" }}

klass / class_name
~~~~~~~~~~~~~~~~~~

Returns the class name of an object as a string.

.. code-block:: django

    {{ obj|klass }}       {# e.g. 'Article' #}
    {{ obj|class_name }}  {# same #}

class_module
~~~~~~~~~~~~

Returns the module path of an object's class.

.. code-block:: django

    {{ obj|class_module }}  {# e.g. 'myapp.models' #}

bootstrap3_field
~~~~~~~~~~~~~~~~

Adds ``form-control`` CSS class to a form field widget.

.. code-block:: django

    {{ form.email|bootstrap3_field }}

filtered_objects_counts
~~~~~~~~~~~~~~~~~~~~~~~

Returns a formatted string describing filtered vs. total object counts.

.. code-block:: django

    {{ filtered_count|filtered_objects_counts:total_count }}
    {# → '<strong>5 (10.00%)</strong> filtered, from a total of 50' #}

qrcode
~~~~~~

Renders a QR code ``<img>`` tag using the Google Charts API.

.. code-block:: django

    {{ some_url|qrcode }}
    {{ some_url|qrcode:"alt text" }}

barcode
~~~~~~~

Renders a barcode ``<img>`` tag (base64-encoded PNG) using the ``python-barcode``
library.

.. code-block:: django

    {{ product.ean|barcode }}
    {{ product.ean|barcode:"EAN13" }}

Mathematical Filters
~~~~~~~~~~~~~~~~~~~~

.. code-block:: django

    {{ value|divide:3 }}
    {{ value|multiply:2 }}
    {{ value|addition:10 }}
    {{ value|subtract:5 }}
    {{ "hello"|concat:" world" }}

order_by
~~~~~~~~

.. code-block:: django

    {{ queryset|order_by:"-created" }}

Date Filters
~~~~~~~~~~~~

.. code-block:: django

    {# Returns now() + N days #}
    {{ 7|add_days }}

    {# Returns now() + N months (requires python-dateutil) #}
    {{ 3|add_months }}

    {# Parse ISO date string to date object #}
    {{ "2024-01-15"|date_from_isoformat }}

Other Filters
~~~~~~~~~~~~~

``translate``
    Passes a string through ``gettext()``.

``filename``
    Returns the basename of a file field value.

``url_anchor``
    Wraps bare URLs in the string with ``<a>`` tags.

``get_objects_by_ids``
    Looks up objects by a comma-separated id list and a ``app_label.model`` string.

    .. code-block:: django

        {{ "1,2,3"|get_objects_by_ids:"myapp.Article" }}

Block Tag
---------

capture
~~~~~~~

Captures a block of template content into a context variable.

.. code-block:: django

    {% capture my_var %}{{ object.title }} — {{ object.subtitle }}{% endcapture %}
    {% if my_var in allowed_titles %}...{% endif %}

Simple Tags
-----------

values_list
~~~~~~~~~~~

Returns a flat ``values_list`` from a queryset.

.. code-block:: django

    {% values_list article_qs "id,title" as id_title_pairs %}

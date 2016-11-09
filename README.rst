.. image:: https://travis-ci.org/PragmaticMates/django-pragmatic.svg?branch=master
    :target: https://travis-ci.org/PragmaticMates/django-pragmatic

django-pragmatic
================

Pragmatic tools and utilities for Django projects

Tested on Django 1.5 up to Django 1.10.2


Requirements
------------
- Django

Some utilities require additional libraries as:

- django_filters
- fpdf
- Pillow/PIL
- pyBarcode


Installation
------------

1. Install python library using pip: pip install django-pragmatic

2. Add ``pragmatic`` to ``INSTALLED_APPS`` in your Django settings file


Usage
-----

Templates
'''''''''
``pragmatic/helpers/breadcrumbs.html``
    Template helper for **django-breadcrumbs** app.

``pragmatic/helpers/confirm_delete.html``
    Form for delete confirmation.

``pragmatic/helpers/messages.html``
    Template helper for django messages framework.

``pragmatic/helpers/pagination.html``
    Template helper for paginating objects in ListViews.

``pragmatic/helpers/pagination-listview.html``
    Template helper for paginating objects in ListViews.

``maintenance_mode.html``
    Template for maintenance mode. See **MaintenanceModeMiddleware** below.


Template tags
'''''''''''''
``{% load pragmatic_tags %}``

``def klass(obj)``
    Returns string of instance class name.

``def translate(obj)``
    Returns translated string of input value (string or any object).

``def filename(obj)``
    Returns name of the file without its path (basename).

``def bootstrap3_field(field)``
    Adds *form-control* class to field widget classes.

``def filtered_objects_counts(filtered, all)``
    Returns translatable percentage description of value filtered/all in this format:
    *'<strong>%d (%.2f%%)</strong> filtered, from a total of %d' % (filtered, percent, all)'*

``def qrcode(value, alt=None)``
    Outputs generated QR code using Google charts API from a given string and adds alternative description to it.

``def barcode(code, args=None)``:
    Outputs generated barcode using pyBarcode library from a given string.

``def paginator(context, objects, page_ident='page', anchor=None, adjacent=2)``
    Pagination template tag.

``def divide(value, arg)``
    Divides the value by argument.

``def multiply(value, arg)``
    Multiplies the value by argument.

``def add(value, arg)``
    Adds the arg to the value.

``def subtract(value, arg)``
    Subtracts the arg to the value.

``def capture(parser, token)``
    Capture contents of block into context.


Context processors
''''''''''''''''''
``def date_formats(request)``
    Returns a lazy 'date formats' context variables DATE_FORMAT_JS, DATE_FORMAT_TAG, DATE_FORMAT_FULLMONTH_TAG,
    from settings file.

``def installed_apps(request)``
    Returns a lazy 'INSTALLED_APPS' context variable.


Decorators
''''''''''
``def permissions_required(app_label, login_url=None, raise_exception=False)``
    Decorator for views that checks whether a user has at least one app permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised and app label of missing permission is stored in user instance.

``def permission_required(perm, login_url=None, raise_exception=False)``
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised and missing permission is stored in user instance.

``def receiver_subclasses(signal, sender, dispatch_uid_prefix, **kwargs)``
    A decorator for connecting receivers and all receiver's subclasses to signals.


Fields
''''''
``class RangeField(forms.Field)``
    Form field which expects input to be a number or number range (2 numbers divided with '-').

``class MultiSelectField(models.Field)``
    Model field which stores multiple choices as a comma-separated list of values, using the normal CHOICES attribute.

``class MultiSelectFormField(forms.MultipleChoiceField)``
    Form field for model field above (MultiSelectField).

``class TruncatedModelChoiceField(forms.ModelChoiceField)``
    ModelChoiceField is a form field which truncates overflowed characters from instance label
    and adds '...' instead of them.


Filters
'''''''
``class TruncatedModelChoiceFilter(forms.ModelChoiceField)``
    Filter field for TruncatedModelChoiceField.

``class OneFieldRangeFilter(django_filters.Filter)``
    Filter field for RangeField.


Middleware
''''''''''
``class MaintenanceModeMiddleware(object)``
    It looks for ``settings.MAINTENANCE_MODE`` attribute.
    If it is set to True, template **maintenance_mode.html** will render for each request.


Loghandlers
'''''''''''
``class AlternativeAdminEmailHandler(AdminEmailHandler)``
    Same as ``django.utils.log import AdminEmailHandler``, but uses ``ALTERNATE_EMAIL_HOST_PASSWORD``,
    ``ALTERNATE_EMAIL_HOST_USER``,  ``ALTERNATE_EMAIL_HOST``, ``ALTERNATE_EMAIL_PORT`` and
    ``ALTERNATE_EMAIL_USE_TLS`` as connection settings.


Mixins
''''''
``class ReadOnlyFormMixin(forms.BaseForm)``
    Adds 'readonly and 'disabled' attributes to fields specified in ``read_only`` form attribute.

``class DeleteObjectMixin(object)``
    Mixin for object delete confirmation. Implement ``get_parent()`` method or ``get_success_url()``
    and ``get_back_url()`` methods instead.

``class PickadateFormMixin(object)``
    Mixin which fixes **pickadate.js** inputs and adds *data-value* attribute to them if you use your own date formats.

``class FPDFMixin(object)``
    Mixin helper for generating PDF outputs in Django using fpdf library.


Widgets
'''''''
``class GroupedCheckboxSelectMultiple(CheckboxSelectMultiple)``
    Advanced form field widget for grouping multiple choices into custom groups.
    Use it with **static/js/grouped-checkboxes.js**


Thirdparty
''''''''''
``class BarcodeImageWriter(ImageWriter)``
    Fixed version of barcode.writer.ImageWriter.

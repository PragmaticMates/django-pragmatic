Mixins
======

All mixins live in ``pragmatic.mixins``.

Form Mixins
-----------

ReadOnlyFormMixin
~~~~~~~~~~~~~~~~~

Makes specific form fields read-only and disabled on existing instances.

.. code-block:: python

    from pragmatic.mixins import ReadOnlyFormMixin
    from django import forms

    class ProfileForm(ReadOnlyFormMixin, forms.ModelForm):
        read_only = ('username', 'email')

        class Meta:
            model = User
            fields = ['username', 'email', 'first_name']

Fields listed in ``read_only`` have ``readonly`` and ``disabled`` attributes
added to their widgets and are excluded from validation (they return the
current instance value through a custom ``clean_<field>`` method).

Set ``read_only_without_instance = True`` to enforce read-only even when
there is no ``instance.pk`` (useful for display-only forms that never have an
instance).

PickadayFormMixin
~~~~~~~~~~~~~~~~~

Fixes `pickaday.js <https://pikaday.com/>`_ date/datetime inputs by adding a
``data-value`` attribute in the format specified by ``settings.DATE_FORMAT``.

.. code-block:: python

    from pragmatic.mixins import PickadayFormMixin

    class EventForm(PickadayFormMixin, forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fix_fields(self, *args, **kwargs)

Access Control Mixins
---------------------

LoginPermissionRequiredMixin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extends Django's ``PermissionRequiredMixin`` with ``raise_exception = True``
and stores the missing permission on ``request.user.permission_error`` for use
in error handlers.

.. code-block:: python

    from pragmatic.mixins import LoginPermissionRequiredMixin

    class InvoiceListView(LoginPermissionRequiredMixin, ListView):
        permission_required = 'billing.view_invoice'

StaffRequiredMixin
~~~~~~~~~~~~~~~~~~

Restricts a view to staff users (``is_staff`` or ``is_superuser``).
Unauthenticated or non-staff requests are redirected to
``settings.LOGIN_REDIRECT_URL`` with a flash error message.

.. code-block:: python

    from pragmatic.mixins import StaffRequiredMixin

    class AdminDashboard(StaffRequiredMixin, TemplateView):
        template_name = 'admin/dashboard.html'

Set ``raise_exception = True`` on the class to raise ``PermissionDenied``
instead of redirecting.

SuperuserRequiredMixin
~~~~~~~~~~~~~~~~~~~~~~

Same as ``StaffRequiredMixin`` but restricts to superusers only.

Delete Mixins
-------------

DeleteObjectMixin
~~~~~~~~~~~~~~~~~

Handles object deletion in a ``DeleteView``. Override ``get_success_url()``
and optionally ``get_back_url()`` / ``get_failure_url()``.

.. code-block:: python

    from pragmatic.mixins import DeleteObjectMixin
    from django.views.generic import DeleteView

    class ArticleDeleteView(DeleteObjectMixin, DeleteView):
        model = Article
        success_url = reverse_lazy('article-list')

When ``PRAGMATIC_TRACK_DELETED_OBJECTS = True``, a ``DeletedObject`` record is
created on successful deletion.

On ``ProtectedError`` (related objects block deletion), the view redirects to
``get_failure_url()`` with a flash error.

**Customisable attributes:**

- ``title`` — page title (default: ``'Delete object'``)
- ``message_success`` — flash message on success
- ``message_error`` — flash message on ``ProtectedError``
- ``back_url`` — URL to return to; falls back to ``object.get_absolute_url()``
- ``failure_url`` — URL on failure; falls back to ``back_url``

CheckProtectedDeleteObjectMixin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extends ``DeleteObjectMixin``. Before showing the confirmation page, it
inspects ``NestedObjects`` and, if any protected relations exist, redirects
immediately with an error listing the blocking object types and counts.

.. code-block:: python

    from pragmatic.mixins import CheckProtectedDeleteObjectMixin

    class CustomerDeleteView(CheckProtectedDeleteObjectMixin, DeleteView):
        model = Customer
        success_url = reverse_lazy('customer-list')

List View Mixins
----------------

SafePaginator
~~~~~~~~~~~~~

A ``Paginator`` subclass that clamps out-of-range page numbers to the last
page rather than raising ``EmptyPage``. Also supports an optional
``count_only_id=True`` argument to count using ``.only('id')`` for performance.

.. code-block:: python

    from pragmatic.mixins import SafePaginator

    class ArticleListView(ListView):
        paginator_class = SafePaginator

DisplayListViewMixin
~~~~~~~~~~~~~~~~~~~~

Supports multiple display modes (e.g. ``list``, ``table``, ``map``) controlled
by a ``?display=`` query parameter. Automatically sets
``template_name_suffix`` to ``_{display}``, so a ``table`` display resolves
to ``myapp/article_table.html``.

.. code-block:: python

    from pragmatic.mixins import DisplayListViewMixin

    class ArticleListView(DisplayListViewMixin, ListView):
        model = Article
        displays = ['list', 'table']
        paginate_by_display = {
            'list': [10, 25, 50],
            'table': 100,
        }

The active display defaults to the first entry in ``displays``. Per-display
pagination values are read from ``paginate_by_display``; the first value in
the list is the default.

Context variables added: ``display_modes``, ``paginate_by_display``,
``paginate_by``.

SortingListViewMixin
~~~~~~~~~~~~~~~~~~~~

URL-parameter-driven queryset sorting via ``?sorting=<key>``.

.. code-block:: python

    from pragmatic.mixins import SortingListViewMixin

    class ArticleListView(SortingListViewMixin, ListView):
        model = Article
        sorting_options = {
            '-created': 'Newest first',
            'title': 'Title A–Z',
            # tuple form: (display_label, queryset_ordering)
            '-price': ('Price high–low', '-price'),
        }

The active sorting defaults to the first key. Negative prefixes (``-field``)
use ``F(field).desc(nulls_last=True)``.

Context variable added: ``sorting_options``.

PaginateListViewMixin
~~~~~~~~~~~~~~~~~~~~~

Minimal mixin that passes ``paginate_by`` from the view to the context. Use
this when you need ``get_paginate_by()`` override without the full
``DisplayListViewMixin``.

Model Mixins
------------

SlugMixin
~~~~~~~~~

Auto-generates a URL-safe slug on ``save()``, ensuring uniqueness by
appending an integer suffix if needed.

.. code-block:: python

    from pragmatic.mixins import SlugMixin
    from django.db import models

    class Article(SlugMixin, models.Model):
        title = models.CharField(max_length=200)
        slug = models.SlugField(unique=True)

        # Optional overrides:
        # SLUG_FIELD = 'title'        # source field (default)
        # MAX_SLUG_LENGTH = 150       # truncate before uniqueness check
        # FORCE_SLUG_REGENERATION = True  # regenerate on every save (default)

PDF Mixins
----------

FPDFMixin
~~~~~~~~~

Helper for generating PDF responses using the `fpdf2 <https://py-pdf.github.io/fpdf2/>`_
library. Override ``write_pdf_content()`` to add content to ``self.pdf``.

.. code-block:: python

    from pragmatic.mixins import FPDFMixin
    from django.views.generic import View

    class InvoicePdfView(FPDFMixin, View):
        orientation = FPDFMixin.ORIENTATION_PORTRAIT

        def get_filename(self):
            return 'invoice.pdf'

        def write_pdf_content(self):
            self.pdf.set_font('Arial', size=12)
            self.pdf.cell(200, 10, txt='Hello', ln=True)

        def get(self, request, *args, **kwargs):
            return self.render()

``FPDFMixin`` constants:

- ``FORMAT_A4`` / ``ORIENTATION_PORTRAIT`` / ``ORIENTATION_LANDSCAPE``
- ``margin_left``, ``margin_right``, ``margin_top``, ``margin_bottom`` (default 8 mm each)

PdfDetailMixin
~~~~~~~~~~~~~~

Renders an existing ``DetailView`` template as a PDF by POSTing the rendered
HTML to an external conversion API (``HTMLTOPDF_API_URL`` or
``PRINTMYWEB_URL``).

.. code-block:: python

    from pragmatic.mixins import PdfDetailMixin

    class InvoicePdfView(PdfDetailMixin, DetailView):
        model = Invoice
        template_name = 'billing/invoice_pdf.html'
        inline = True  # True = inline in browser, False = download

        def get_filename(self):
            return f'invoice-{self.get_object().number}.pdf'

Set ``HTMLTOPDF_API_URL`` or ``PRINTMYWEB_URL`` (plus ``PRINTMYWEB_TOKEN``)
in your settings.

import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.db.models.deletion import ProtectedError
from django.forms.widgets import HiddenInput
from django.http.response import HttpResponseRedirect, HttpResponse
from django.utils import timezone, six
from django.utils.translation import ugettext_lazy as _


class ReadOnlyFormMixin(forms.BaseForm):
    def _get_cleaner(self, field):
        def clean_field():
            return getattr(self.instance, field, None)
        return clean_field

    def __init__(self, *args, **kwargs):
        super(ReadOnlyFormMixin, self).__init__(*args, **kwargs)
        if hasattr(self, "read_only"):
            if self.instance and self.instance.pk:
                for field in self.read_only:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].widget.attrs['disabled'] = True
                    self.fields[field].required = False
                    setattr(self, "clean_" + field, self._get_cleaner(field))


class RestrictUserMixin(object):
    def set_choices_or_queryset(self, field, choices, queryset, num_fields):
        hide_field = False
        if choices is not None:
            field.choices = choices
            hide_field = len(choices) <= 1
        if queryset is not None:
            field.queryset = queryset
            hide_field = hide_field or queryset.count() <= 1
        if hide_field and num_fields > 1:
            field.widget = HiddenInput()

    def restrict_user(self, request, empty_value=False, empty_label=_(u'Select client')):
        # restrict user clients
        client = request.user.get_selected_client(request)
        choices = None
        queryset = None

        if client is not None:
            # choices
            choices = (('', empty_label),) if empty_value else ()
            choices += ((client.pk, client), )
        else:
            # queryset
            if not (request.user.is_admin or request.user.is_superadmin):
                queryset = request.user.get_clients()

        try:
            # filter
            self.set_choices_or_queryset(self.form.fields['client'], choices, queryset, len(self.form.fields))
        except AttributeError:
            # form
            self.set_choices_or_queryset(self.fields['client'], choices, queryset, len(self.fields))


class DeleteObjectMixin(object):
    template_name = 'utils/confirm_delete.html'
    title = _(u'Delete object')
    message_success = _(u'Object successfully deleted.')
    message_error = _(u'Object could not be deleted, check if some objects are not associated with it.')

    def get_success_url(self):
        return self.get_parent().get_absolute_url()

    def get_back_url(self):
        return self.get_parent().get_absolute_url()

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            if self.message_success:
                messages.success(request, self.message_success)
        except ProtectedError:
            if self.message_error:
                messages.error(request, self.message_error)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context_data = super(DeleteObjectMixin, self).get_context_data(**kwargs)
        context_data['title'] = self.title
        context_data['back_url'] = self.get_back_url()
        return context_data


class PickadayFormMixin(object):
    def fix_fields(self, *args, **kwargs):
        for field_name in self.fields:
            if isinstance(self.fields[field_name], forms.fields.DateField):
                self.fix_field(field_name, *args, **kwargs)

    def fix_field(self, field_name, *args, **kwargs):
        date = None
        if field_name in self.data:
            date = self.data.get(field_name)
        elif 'initial' in kwargs and field_name in kwargs.get('initial'):
            date = kwargs.get('initial').get(field_name)
        if not date and kwargs.get('instance', None) is not None:
            instance = kwargs.get('instance')
            date = getattr(instance, field_name)
        if date:
            if type(date) == datetime.date:
                # convert date to datetime
                date = datetime.datetime.combine(date, datetime.time(0, 0))
                # convert from naive to aware (without pytz)
                date = date.replace(tzinfo = timezone.utc)

                # convert from naive to aware (with pytz)
#                import pytz
#                date = pytz.timezone("Europe/Helsinki").localize(naive, is_dst=None)

            if type(date) == datetime.date or type(date) == datetime.datetime:
                # get date in custom format in local time
                date = timezone.localtime(date)
                date = date.strftime(settings.DATE_FORMAT)
            self.fields[field_name].widget.attrs['data-value'] = date


class FPDFMixin(object):
    DEBUG = settings.DEBUG
    FORMAT_A4 = 'A4'
    FORMATS = {
        FORMAT_A4: {
            'width': 210,
            'height': 297
        }
    }
    format = FORMAT_A4
    ORIENTATION_PORTRAIT = 'P'
    ORIENTATION_LANDSCAPE = 'L'
    ORIENTATIONS = (
        (ORIENTATION_PORTRAIT, _(u'Portrait')),
        (ORIENTATION_LANDSCAPE, _(u'Landscape'))
    )
    orientation = ORIENTATION_PORTRAIT
    marginLeft = 8
    marginRight = 8
    marginTop = 8
    marginBottom = 8

    def render(self, **kwargs):
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.
        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

        self.init_sizes()
        self.init_pdf()
        self.write_pdf_content()

        self.response = HttpResponse(
            content=self.pdf.output(dest='S'),
            content_type='application/octet-stream'
        )
#        self.response['Content-Type'] = 'application/octet-stream; charset=UTF-8'
        self.response['Content-Disposition'] =\
            'attachment;filename="%(filename)s"' % {
            'filename': self.get_filename()
            }
        return self.response

    def get_filename(self):
        return 'doc.pdf'

    def init_sizes(self):
        self.page_width = self.FORMATS[self.format]['width']
        self.page_height = self.FORMATS[self.format]['height']
        if self.orientation == 'L':
            self.page_width, self.page_height = self.page_height, self.page_width

        self.contentWidth = self.page_width - self.marginLeft - self.marginRight
        self.contentHeight = self.page_height - self.marginTop - self.marginBottom

    def init_pdf(self):
        from fpdf import FPDF
        self.pdf = FPDF(self.orientation, 'mm', self.format)
        self.pdf.set_margins(self.marginLeft, self.marginTop, self.marginRight)
        self.pdf.set_auto_page_break(True, margin=self.marginBottom)
        self.pdf.add_page()

    def write_pdf_content(self):
        pass
import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin, AccessMixin
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone, six
from django.utils.translation import ugettext_lazy as _, ugettext


class ReadOnlyFormMixin(forms.BaseForm):
    def _get_cleaner(self, field):
        def clean_field():
            return getattr(self.instance, field, None)
        return clean_field

    def __init__(self, *args, **kwargs):
        super(ReadOnlyFormMixin, self).__init__(*args, **kwargs)
        without_instance = self.read_only_without_instance if hasattr(self, "read_only_without_instance") else False
        if hasattr(self, "read_only"):
            if self.instance and self.instance.pk or without_instance:
                for field in self.read_only:
                    self.fields[field].widget.attrs['readonly'] = True
                    self.fields[field].widget.attrs['disabled'] = True
                    self.fields[field].required = False
                    setattr(self, "clean_" + field, self._get_cleaner(field))


class LoginPermissionRequiredMixin(DjangoPermissionRequiredMixin):
    raise_exception = True

    def get_permission_denied_message(self):
        """
        Override this method to override the permission_denied_message attribute.
        """
        if self.permission_denied_message:
            return self.permission_denied_message

        return self.permission_required

    def handle_no_permission(self):
        self.request.user.permission_error = self.get_permission_denied_message()

        if not self.request.user.is_authenticated:
            self.raise_exception = False

        return super().handle_no_permission()


class StaffRequiredMixin(AccessMixin):
    """
    CBV mixin which verifies that the current user is staff
    """
    raise_exception = False
    permission_denied_message = ugettext('You are not authorized for this operation')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and not request.user.is_superuser:
            return self.handle_no_permission()
        return super(StaffRequiredMixin, self).dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())

        messages.error(self.request, self.get_permission_denied_message())
        return redirect(reverse('dashboard'))


class DeleteObjectMixin(object):
    template_name = 'confirm_delete.html'
    title = _(u'Delete object')
    message_success = _(u'Object successfully deleted.')
    message_error = _(u'Object could not be deleted, check if some objects are not associated with it.')
    back_url = None
    failure_url = None

    def get_back_url(self):
        try:
            return self.back_url if self.back_url else self.object.get_absolute_url()
        except:
            return self.success_url

    def get_failure_url(self):
        return self.failure_url if self.failure_url else self.get_back_url()

    def get_success_url(self):
        return self.success_url

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            if self.message_success:
                messages.success(request, self.message_success)
            return HttpResponseRedirect(self.get_success_url())
        except ProtectedError:
            if self.message_error:
                messages.error(request, self.message_error)
        return HttpResponseRedirect(self.get_failure_url())

    def get_context_data(self, **kwargs):
        context_data = super(DeleteObjectMixin, self).get_context_data(**kwargs)
        context_data['title'] = self.title
        context_data['back_url'] = self.get_back_url()
        return context_data


class PickadayFormMixin(object):
    def fix_fields(self, form=None, *args, **kwargs):
        self.field_array = form.fields if form else self.fields
        for field_name in self.field_array:
            is_datefield = isinstance(self.field_array[field_name], forms.fields.DateField)
            is_datetimefield = isinstance(self.field_array[field_name], forms.fields.DateTimeField)
            if is_datefield or is_datetimefield:
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
        elif not date and getattr(self, 'instance', None) is not None:
            date = getattr(self.instance, field_name)
        if date:
            if type(date) == datetime.date:
                # convert date to datetime
                date = datetime.datetime.combine(date, datetime.time(0, 0))
                # convert from naive to aware (without pytz)
                date = date.replace(tzinfo=timezone.utc)

                # convert from naive to aware (with pytz)
#                import pytz
#                date = pytz.timezone("Europe/Helsinki").localize(naive, is_dst=None)

            if type(date) == datetime.date or type(date) == datetime.datetime:
                # get date in custom format in local time
                date = timezone.localtime(date)
                date = date.strftime(settings.DATE_FORMAT)
            self.field_array[field_name].widget.attrs['data-value'] = date


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
    margin_left = 8
    margin_right = 8
    margin_top = 8
    margin_bottom = 8

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
        return 'document.pdf'

    def init_sizes(self):
        # page sizes
        self.page_width = self.FORMATS[self.format]['width']
        self.page_height = self.FORMATS[self.format]['height']
        if self.orientation == 'L':
            self.page_width, self.page_height = self.page_height, self.page_width

        # content sizes
        self.content_width = self.page_width - self.margin_left - self.margin_right
        self.content_height = self.page_height - self.margin_top - self.margin_bottom

    def get_pdf_instance(self):
        from fpdf import FPDF, HTMLMixin
        class MyFPDF(FPDF, HTMLMixin):
            pass
        page_format = dict(self.FORMATS).get(self.format, None)
        if page_format is not None:
            pdf = MyFPDF(self.orientation, 'mm', (page_format['width'], page_format['height']))
        else:
            pdf = MyFPDF(self.orientation, 'mm', self.format)
        return pdf

    def init_pdf(self):
        self.pdf = self.get_pdf_instance()
        self.pdf.set_margins(self.margin_left, self.margin_top, self.margin_right)
        self.pdf.set_auto_page_break(True, margin=self.margin_bottom)
        self.pdf.add_page()

    def write_pdf_content(self):
        pass

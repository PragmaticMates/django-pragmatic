import datetime
import inspect
import io
from itertools import groupby

import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin, AccessMixin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.validators import EMPTY_VALUES
from django.core.paginator import EmptyPage, Paginator
from django.db import router
from django.db.models import F, QuerySet
from django.db.models.deletion import ProtectedError
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.inspect import method_has_no_args
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _, gettext

from pragmatic.models import DeletedObject


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
    permission_denied_message = gettext('You are not authorized for this operation')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff and not request.user.is_superuser:
            return self.handle_no_permission()
        return super(StaffRequiredMixin, self).dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())

        messages.error(self.request, self.get_permission_denied_message())
        return redirect(getattr(settings, 'LOGIN_REDIRECT_URL', '/'))


class SuperuserRequiredMixin(StaffRequiredMixin):
    """
    CBV mixin which verifies that the current user is superuser
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return self.handle_no_permission()
        return super(SuperuserRequiredMixin, self).dispatch(request, *args, **kwargs)


class DeleteObjectMixin(object):
    template_name = 'confirm_delete.html'
    title = _('Delete object')
    message_success = _('Object successfully deleted.')
    message_error = _('Object could not be deleted, check if some objects are not associated with it.')
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
        track_deleted_objects = getattr(settings, 'PRAGMATIC_TRACK_DELETED_OBJECTS', False)

        try:
            if track_deleted_objects:
                # prepare tracking data
                content_type = ContentType.objects.get_for_model(self.object, for_concrete_model=False)
                object_id = self.object.id
                object_str = str(self.object)
                user = self.request.user

            # delete object
            self.object.delete()

            # show success message if available
            if self.message_success:
                messages.success(request, self.message_success)

            if track_deleted_objects:
                # track deleted object
                DeletedObject.objects.create(
                    content_type=content_type,
                    object_id=object_id,
                    object_str=object_str,
                    user=user if user.is_authenticated else None
                )

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


class CheckProtectedDeleteObjectMixin(DeleteObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        using = router.db_for_write(self.get_object()._meta.model)
        collector = NestedObjects(using=using)
        collector.collect([self.get_object()])
        protected = collector.protected

        if protected:
            objects = []
            grouped_dict = {}

            for object_type, grouper in groupby(protected, key=type):
                if grouped_dict.get(object_type):
                    existing_list = grouped_dict.get(object_type)
                    for obj in list(grouper):
                        existing_list.append(obj)

                    grouped_dict[object_type] = existing_list
                else:
                    grouped_dict[object_type] = list(grouper)

            for obj_type, obj_list in grouped_dict.items():
                obj_name = _(obj_type._meta.verbose_name_plural)
                objects.append(mark_safe(
                    '%(text)s' % {'text': str(obj_name) + ' (' + str(len(obj_list)) + ')'}))

                # try:
                #     url = reverse_lazy(f'{obj_type._meta.app_label}:{obj_type._meta.model_name}_list')
                #     objects.append(mark_safe(
                #         '<a href="%(url)s" target="_blank">%(text)s</a>' % {'url': url + '?person=' + str(self.get_object().pk),
                #                                                             'text': str(obj_name) + ' (' + str(len(obj_list)) + ')'}))
                # except NoReverseMatch:
                #     objects.append(mark_safe(
                #         '%(text)s' % {'text': str(obj_name) + ' (' + str(len(obj_list)) + ')'}))

            messages.error(self.request, _('Instance cannot be deleted because of related objects: {}').format(', '.join(objects)))
            return redirect(self.get_object().get_absolute_url())

        return super().dispatch(request, *args, **kwargs)


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
        (ORIENTATION_PORTRAIT, _('Portrait')),
        (ORIENTATION_LANDSCAPE, _('Landscape'))
    )
    orientation = ORIENTATION_PORTRAIT
    margin_left = 8
    margin_right = 8
    margin_top = 8
    margin_bottom = 8

    def render(self, **kwargs):
        # Go through keyword arguments, and either save their values to our
        # instance, or raise an error.

        try:
            from django.utils import six
        except ImportError:
            import six

        for key, value in six.iteritems(kwargs):
            setattr(self, key, value)

        self.init_sizes()
        self.init_pdf()
        self.write_pdf_content()

        self.response = HttpResponse(
            content=bytes(self.pdf.output()),
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


class SafePaginator(Paginator):
    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True, count_only_id=False):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self.count_only_id = count_only_id

    @cached_property
    def count(self):
        """Return the total number of objects, across all pages, count only id if objectlist is queryset"""
        object_list = self.object_list.only('id') if isinstance(self.object_list, QuerySet) and self.count_only_id else self.object_list
        c = getattr(object_list, 'count', None)
        if callable(c) and not inspect.isbuiltin(c) and method_has_no_args(c):
            return c()
        return len(object_list)

    def validate_number(self, number):
        try:
            return super(SafePaginator, self).validate_number(number)
        except EmptyPage:
            if number > 1:
                return self.num_pages
            else:
                raise


class DisplayListViewMixin(object):
    displays = []
    paginate_by_display = {}
    paginator_class = SafePaginator

    def dispatch(self, request, *args, **kwargs):
        self.eval_get_paginate_by(request)
        self.template_name_suffix = f'_{self.display}'
        return super().dispatch(request, *args, **kwargs)

    def eval_get_paginate_by(self, request):
        paginate_values = self.paginate_by_display.get(self.display, None)
        paginate_values = paginate_values if isinstance(paginate_values, list) else [paginate_values]
        self.paginate_by = request.GET.get('paginate_by', next(iter(paginate_values)))
        self.paginate_by = int(self.paginate_by) if self.paginate_by in map(str, paginate_values) else paginate_values[0]

    @property
    def display(self):
        display = self.request.GET.get('display', self.displays[0])
        display = display if display in self.displays else self.displays[0]
        return display

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True, **kwargs):
        return super().get_paginator(queryset, per_page, orphans=0, allow_empty_first_page=True, count_only_id=getattr(self, 'paginator_count_only_id', False), **kwargs)

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by current display, or ``None`` for no pagination.
        """
        return self.paginate_by

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['display_modes'] = self.displays
        context_data['paginate_by_display'] = self.paginate_by_display
        context_data['paginate_by'] = self.paginate_by
        return context_data


class PaginateListViewMixin(object):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        """
        Get the number of items to paginate by current display, or ``None`` for no pagination.
        """
        return self.paginate_by

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        return context_data


class SortingListViewMixin(object):
    sorting_options = {}

    @property
    def sorting(self):
        first_sorting_option = next(iter(self.get_sorting_options().keys())) if len(self.get_sorting_options().keys()) > 0 else None
        sorting = self.request.GET.get('sorting', first_sorting_option)
        sorting = sorting if sorting in self.get_sorting_options() else first_sorting_option
        sorting_value = self.get_sorting_options().get(sorting)
        sorting = sorting_value[1] if isinstance(sorting_value, tuple) else sorting
        return sorting

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)
        context_data['sorting_options'] = self.get_sorting_options()
        return context_data

    def get_sorting_options(self):
        return self.sorting_options

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.sort_queryset(queryset)

    def sort_queryset(self, queryset):
        if not self.sorting:
            return queryset

        if isinstance(self.sorting, list):
            return queryset.order_by(*self.sorting)

        sorting = F(self.sorting[1:]).desc(nulls_last=True) if self.sorting.startswith('-') else self.sorting
        return queryset.order_by(sorting)


class SlugMixin(object):
    MAX_SLUG_LENGTH = 150
    FORCE_SLUG_REGENERATION = True
    SLUG_FIELD = 'title'

    def save(self, **kwargs):
        if self.slug in EMPTY_VALUES or self.FORCE_SLUG_REGENERATION:
            slug_field = getattr(self, self.SLUG_FIELD)
            slug = slugify(slug_field)
            self.slug = slug
            index = 1

            # Ensure uniqueness
            while self.__class__.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f'{slug}-{index}'
                index += 1

        return super().save(**kwargs)


class PdfDetailMixin(object):
    inline = True

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        if not getattr(response, 'is_rendered', True) and callable(getattr(response, 'render', None)):
            response.render()

        response = self.render_pdf(response.content, self.get_filename(), self.inline)
        return response

    def get_filename(self):
        return f'{self.get_object()}.pdf'

    @staticmethod
    def render_pdf(html_content, filename='output.pdf', inline=True):
        htmltopdf_api_url = getattr(settings, 'HTMLTOPDF_API_URL', None)
        printmyweb_url = getattr(settings, 'PRINTMYWEB_URL', None)
        printmyweb_token = getattr(settings, 'PRINTMYWEB_TOKEN', None)

        print_api_url = htmltopdf_api_url or printmyweb_url

        kwargs = {}
        if printmyweb_token:
            kwargs['headers'] = {
                'api-key': printmyweb_token
            }

        content_type = 'inline' if inline else 'attachment'
        pdf_response = requests.post(print_api_url, data=html_content, **kwargs)
        buffer = io.BytesIO(pdf_response.content)

        from PyPDF2 import PdfFileMerger
        pdf_merger = PdfFileMerger()
        pdf_merger.append(buffer)
        pdf_merger.addMetadata({'/Title': filename})
        pdf_merger.write(buffer)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'{content_type}; filename="{filename}"'
        return response

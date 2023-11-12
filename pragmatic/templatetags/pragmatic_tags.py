import datetime
import json
import os
import re
import urllib
from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import DateField, Count, Sum
from django.db.models.functions import TruncDay
from django.template.defaultfilters import stringfilter
from django.urls import translate_url as django_translate_url
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from django.utils.translation import gettext_lazy as _, gettext, override as override_language

from python_pragmatic.strings import barcode as pragmatic_barcode

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, lang, *args, **kwargs):
    path = kwargs.get('path', None)
    object = kwargs.get('object', None)
    callable_object = kwargs.get('callable', None)

    if path and (object or callable_object):
        raise ValueError('"path" argument can not be used together with "object" or "callable"')

    if object and not callable_object or callable_object and not object:
        raise ValueError('Both "object" or "callable" has to be defined')

    if not path:
        # custom object
        if object:
            with override_language(lang):
                path = getattr(object, callable_object)()
                return django_translate_url(path, lang)

        # context object
        context_object = context.get('object', None)

        if context_object:
            with override_language(lang):
                get_absolute_url = getattr(context_object, "get_absolute_url", None)

                if get_absolute_url and callable(get_absolute_url):
                    return context_object.get_absolute_url()

        # URL path
        # path = context['request'].path
        request = context.get('request', None)
        path = request.path if request else f'/{lang}/'

    return django_translate_url(path, lang)


@register.filter
def get_item(value, arg):
    """Gets an attribute of an object dynamically AND recursively from a string name"""

    numeric_test = re.compile(r'^\d+$')

    try:  # for dict and  __getitem__(self, name)
        return value[arg]
    except (KeyError, TypeError, IndexError):
        pass

    if "." in str(arg):
        firstarg = str(arg).split(".")[0]
        value = get_item(value, firstarg)
        arg = ".".join(str(arg).split(".")[1:])

        return get_item(value, arg)

    if hasattr(value, str(arg)):
        return getattr(value, str(arg))

    if numeric_test.match(str(arg)) and len(value) > int(arg):
        try:
            return value[int(arg)]
        except (KeyError, IndexError):
            pass

    try:
        dict_value = dict(value)

        if isinstance(dict_value, dict) and arg in dict_value:
            return dict_value[arg]
    except ValueError:
        pass

    return getattr(settings, 'TEMPLATE_STRING_IF_INVALID', None)


@register.filter()
def get_list(querydict, param):
    return querydict.getlist(param)


@register.filter
@stringfilter
def split(string, sep):
    """Return the string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)


@register.filter
def attribute(value, attr):
    return getattr(value, attr)


@register.filter
def klass(ob):
    return ob.__class__.__name__


@register.filter
def class_name(ob):
    return ob.__class__.__name__


@register.filter
def class_module(ob):
    return ob.__class__.__module__


@register.filter(name='bootstrap3_field')
def bootstrap3_field(obj):
    if 'class' in obj.field.widget.attrs:
        obj.field.widget.attrs['class'] = 'form-control ' + obj.field.widget.attrs['class']
    else:
        obj.field.widget.attrs['class'] = 'form-control'

    return obj


@register.inclusion_tag('helpers/filter_values.html', takes_context=True)
def filter_values(context, filter):
    request = context.get('request', None)

    if not request:
        return {}

    values = filtered_values(filter, request.GET)

    return {
        'full_path': request.get_full_path(),
        'filter_values': values
    }


@register.simple_tag()
def filtered_values(filter, request_data):
    values = {}

    form = filter.form
    form.full_clean()
    cleaned_data = form.cleaned_data

    for param in request_data:
        filter_name = param
        label_suffix = ''

        slice_value_name = None

        for ending in ['_before', '_after', '_min', '_max']:
            if param.endswith(ending):
                filter_name = param[:-len(ending)]

                if ending in ['_after', '_min']:
                    slice_value_name = 'start'
                    label_suffix = gettext('after') if ending == '_after' else gettext('from')
                else:
                    slice_value_name = 'stop'
                    label_suffix = gettext('before') if ending == '_before' else gettext('to')

        filter_field = filter.filters.get(filter_name, None)

        if filter_field:
            value = cleaned_data.get(filter_name, None)

            if value:
                if isinstance(value, list):
                    # multiple choice field
                    if hasattr(filter_field, 'queryset'):
                        value = ', '.join([str(v) for v in value])
                    else:
                        value_values = []

                        for v in value:
                            try:
                                v_display = dict(form.fields[filter_name].choices)[v]
                                v_display = str(v_display)
                                value_values.append(v_display)
                            except (KeyError, AttributeError):
                                try:
                                    # grouped choices
                                    choices = {}
                                    for group in form.fields[filter_name].choices:
                                        choices.update(dict(group[1]))

                                    v_display = choices[v]
                                    v_display = str(v_display)
                                    value_values.append(v_display)
                                except (KeyError, AttributeError):
                                    pass


                        value = ', '.join(value_values)
                else:
                    # choice field
                    try:
                        if not hasattr(filter_field, 'queryset'):
                            choices = form.fields[filter_name].choices

                            choices_dict = None
                            if hasattr(choices, 'choices'):
                                choices = choices.choices
                                if isinstance(value, str):
                                    choices_dict = {str(key): val for key, val in choices}

                            choices_dict = choices_dict if choices_dict is not None else dict(choices)
                            value = choices_dict[value]
                    except (KeyError, AttributeError):
                        pass

                if isinstance(value, slice):
                    # range field
                    if slice_value_name:
                        slice_value = getattr(value, slice_value_name)

                        if slice_value_name in ['start', 'stop']:
                            first_value = form.fields[filter_name].fields[0].to_python(getattr(value, 'start'))
                            last_value = form.fields[filter_name].fields[1].to_python(getattr(value, 'stop'))

                            if first_value != last_value:
                                slice_value = first_value if slice_value_name == 'start' else last_value

                        value = slice_value
                    else:
                        if value.start and value.stop:
                            value = ' - '.join([str(value.start), str(value.stop)])
                        else:
                            if value.start:
                                value = gettext('at least') + ' ' + str(value.start)
                            elif value.stop:
                                value = gettext('up to') + ' ' + str(value.stop)

                values[param] = {
                    'label': (filter_field.label + ' ' + label_suffix).strip(),
                    'value': value
                }

    return values


@register.simple_tag()
def num_applied_filters(filter, request_data):
    form = filter.form
    form.full_clean()
    cleaned_data = form.cleaned_data

    num_applied_filters = 0

    for param in request_data:
        filter_name = param

        for ending in ['_before', '_after', '_min', '_max']:
            if param.endswith(ending):
                filter_name = param[:-len(ending)]

        filter_field = filter.filters.get(filter_name, None)

        if filter_field:
            value = cleaned_data.get(filter_name, None)

            if value:
                num_applied_filters += 1

    return num_applied_filters


@register.filter('filtered_objects_counts')
def filtered_objects_counts(filtered, all):
    try:
        if filtered == all or all == 0:
            return mark_safe('%s: <strong>%d</strong>' % (gettext('total'), all))
        else:
            percent = 100 * float(filtered) / all
            return mark_safe('<strong>%d (%.2f%%)</strong> %s %d' % (filtered, percent, gettext('filtered, from a total of'), all))
    except (ValueError, TypeError):
        return ''


@register.filter
@stringfilter
def qrcode(value, alt=None):
    """
    Generate QR Code image from a string with the Google charts API

    http://code.google.com/intl/fr-FR/apis/chart/types.html#qrcodes

    Exemple usage --
    {{ my_string|qrcode:"my alt" }}

    <img src="http://chart.apis.google.com/chart?chs=150x150&amp;cht=qr&amp;chl=my_string&amp;choe=UTF-8" alt="my alt" />
    """

    url = conditional_escape("http://chart.apis.google.com/chart?%s" % \
                             urllib.urlencode({'chs': '250x250', 'cht': 'qr', 'chl': value, 'choe': 'UTF-8'}))
    alt = conditional_escape(alt or value)

    return mark_safe("""<img class="qrcode" src="%s" width="250" height="250" alt="%s" />""" % (url, alt))


@register.filter
@stringfilter
def barcode(code, args=None):
    from barcode.errors import IllegalCharacterError

    try:
        barcode = pragmatic_barcode(code, args)
        # return as HTML element
        return mark_safe('<img src="data:image/png;base64,' + barcode + '" />')
    except IllegalCharacterError as e:
        message = str(e)

        if ':' in message:
            character = message.split(':', 1)[1]
            return '{}: {}'.format(_('Invalid characters'), character)
        else:
            return message


@register.inclusion_tag('helpers/pagination.html', takes_context=True)
def paginator(context, objects, page_ident='page', anchor=None, adjacent=2):
    page_range = objects.paginator.page_range
    number = objects.number

    page_numbers = [n for n in range(number - adjacent, number + adjacent + 1) if n > 0 and n <= len(page_range)]

    show_left_dots = True
    if number - adjacent - 1 == 1:
        show_left_dots = False

    show_right_dots = True
    if number + adjacent + 1 == len(page_range):
        show_right_dots = False

    page_obj = objects.paginator.page(objects.number)

    return {
        'anchor': anchor,
        'request': context.get('request', None),
        'page_ident': page_ident,
        'results_per_page': objects.paginator.per_page,
        'page': objects.number,
        'pages': page_range,
        'count': len(page_range),
        'total_count': objects.paginator.count,
        'page_numbers': page_numbers,
        'next': objects.next_page_number,
        'previous': objects.previous_page_number,
        'has_next': objects.has_next,
        'has_previous': objects.has_previous,
        'show_first': 1 not in page_numbers,
        'show_last': False if len(page_range) - number <= adjacent else True,
        'show_left_dots': show_left_dots,
        'show_right_dots': show_right_dots,
        'start': page_obj.start_index(),
        'end': page_obj.end_index()
    }


@register.filter(is_safe=False)
def divide(value, arg):
    """Divides the value by argument."""
    try:
        return float(value) / float(arg)
    except ZeroDivisionError:
        return float(value)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def multiply(value, arg):
    """Multiplies the value by argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def addition(value, arg):
    """Adds the arg to the value."""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter(is_safe=False)
def subtract(value, arg):
    """Subtracts the arg to the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter()
def translate(text):
    return gettext(text)


@register.filter
def filename(value):
    try:
        return os.path.basename(str(value.file.name))
    except:
        return value


@register.tag
def capture(parser, token):
    """
    Capture contents of block into context
    --------------------------------------

    Use case: variable accessing based on current variable values.

    {% capture foo %}{{ foo.value }}-suffix{% endcapture %}
    {% if foo in bar %}{% endif %}

    Created on Monday, February 2012 by Yuji Tomita
    """
    nodelist = parser.parse(('endcapture',))
    parser.delete_first_token()
    varname = token.contents.split()[1]
    return CaptureNode(nodelist, varname)


class CaptureNode(template.Node):
    def __init__(self, nodelist, varname):
        self.nodelist = nodelist
        self.varname = varname

    def render(self, context):
        context[self.varname] = self.nodelist.render(context)
        return ''


def modify_query_param(url, param, action):
    from urllib import parse
    from django.http import QueryDict

    # parse URL
    parsed_url = parse.urlparse(url)

    # path
    path = parsed_url.path

    # params as string
    params = parsed_url.query

    # convert params string to querydict
    querydict = QueryDict(params, mutable=True)

    for key, value in QueryDict(param).lists():
        if action == 'remove':
            # remove param from querydict (if exists)
            if key in querydict:
                querydict.pop(key)
        elif action == 'add':
            # add param to querydict (if not exists)
            if key not in querydict:
                querydict.setlist(key, value)
        elif action == 'replace':
            # add (and replace) param in querydict
            querydict.setlist(key, value)

    # encode params to string
    encoded_params = querydict.urlencode()

    # construct new path
    new_url = '{}?{}'.format(path, encoded_params)

    return new_url.strip('?')


@register.filter()
def add_query_param(url, param):
    return modify_query_param(url, param, action='add')


@register.filter()
def replace_query_param(url, param):
    return modify_query_param(url, param, action='replace')


@register.filter()
def remove_query_param(url, param):
    return modify_query_param(url, param, action='remove')


@register.filter
def url_anchor(html):
    pat = re.compile(r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]\.[^\s]{2,})')
    sub = re.sub(pat, lambda x: '<a class="url-anchor" href="' + x.group(1) + '">' + x.group(1) + '</a>', html)
    return mark_safe(sub)


@register.inclusion_tag('helpers/display_modes.html', takes_context=True)
def display_modes(context):
    request = context['request']
    url = request.path
    modes = context.get('display_modes', ['list', 'table'])
    current_mode = request.GET.get('display', modes[0])
    localized_modes = {
        'table': _('Table'),
        'list': _('List'),
        'columns': _('Columns'),
        'map': _('Map'),
        'matrix': _('Matrix'),
        'tv': _('TV'),
        'graph': _('Graph'),
        'calendar': _('Calendar'),
    }
    displays = get_displays(current_mode, localized_modes, modes, request, url)

    current_paginate_by = ''
    paginate_values = []
    available_paginate_values = context.get('paginate_by_display')

    if available_paginate_values:
        available_paginate_values = available_paginate_values.get(current_mode, [None])
        available_paginate_values = available_paginate_values if isinstance(available_paginate_values, list) else [available_paginate_values]
        current_paginate_by = get_current_paginate_by(available_paginate_values, request)
        paginate_values = get_paginate_by(available_paginate_values, request, url)

    return {
        'displays': displays,
        'paginate_values': paginate_values,
        'current_paginate_by': current_paginate_by
    }


def get_current_paginate_by(available_paginate_values, request):
    current_paginate_by = request.GET.get('paginate_by', available_paginate_values[0])
    return int(current_paginate_by) if current_paginate_by in map(str, available_paginate_values) else available_paginate_values[0]


def get_displays(current_mode, localized_modes, modes, request, url):
    displays = []

    for mode in modes:
        display = {}

        params = request.GET.copy()
        params['display'] = mode

        is_active = current_mode == mode
        full_url = f'{url}?{params.urlencode()}'

        display.update({
            'mode': mode,
            'active': is_active,
            'url': full_url,
            'localized_mode': localized_modes.get(mode, mode)
        })

        displays.append(display)

    return displays


def get_paginate_by(available_paginate_values, request, url):
    paginate_by_list = []

    if len(available_paginate_values) > 1:
        for available_paginate_by in available_paginate_values:
            paginate_by = {}

            params = request.GET.copy()
            params['paginate_by'] = available_paginate_by

            full_url = f'{url}?{params.urlencode()}'

            paginate_by.update({
                'value': available_paginate_by,
                'url': full_url,
            })

            paginate_by_list.append(paginate_by)

    return paginate_by_list


@register.inclusion_tag('helpers/sorting.html', takes_context=True)
def sorting(context):
    sorting_list = []
    request = context['request']
    sorting_options = context.get('sorting_options', {'-created': 'Recently created'})
    url = request.path
    current_sorting = None

    if len(sorting_options.keys()) > 0:
        first_sorting_option = next(iter(sorting_options.keys()))
        current_sorting = request.GET.get('sorting', first_sorting_option)
        current_sorting = current_sorting if current_sorting in sorting_options else first_sorting_option
        current_sorting = sorting_options.get(current_sorting, current_sorting)
        current_sorting = str(current_sorting[0]) if isinstance(current_sorting, tuple) else current_sorting

        for sorting_option in sorting_options:
            sorting = {}

            params = request.GET.copy()
            params['sorting'] = sorting_option
            full_url = f'{url}?{params.urlencode()}'
            mode = sorting_options.get(sorting_option)

            sorting.update({
                'mode': mode[0] if isinstance(mode, tuple) else mode,
                'url': full_url,
            })

            sorting_list.append(sorting)

    return {
        'sorting_list': sorting_list,
        'current_sorting': current_sorting
    }


@register.filter
def order_by(queryset, order_by):
    return queryset.order_by(order_by)


@register.filter
def add_days(days):
    return now() + datetime.timedelta(days=days)


@register.filter
def add_months(months):
    from dateutil.relativedelta import relativedelta
    return now() + relativedelta(months=months)


@register.filter(is_safe=False)
def concat(value, arg):
    """Add the arg to the value."""
    try:
        arg = str(arg) if arg else ''
        return str(value) + arg
    except Exception:
        return str(value)


@register.inclusion_tag('admin/chart.html')
def admin_chart(objects, label=_('New data'), color='red', type='bar', date_field='created'):
    chart_data = objects \
        .annotate(date=TruncDay(date_field, output_field=DateField()))\
        .values("date")\
        .annotate(y=Count("id"))\
        .order_by("-date")

    return {
        'data': json.dumps(list(chart_data), cls=DjangoJSONEncoder),
        'label': label,
        'color': color,
        'type': type
    }


@register.simple_tag()
def objects_stats(objects, count_attr, sum_attr=None):
    kwargs = {'count': Count(count_attr)}

    if sum_attr:
        kwargs.update({'sum': Sum(sum_attr)})

    return objects\
        .values(count_attr)\
        .annotate(**kwargs)\
        .order_by('-count')


@register.filter
def date_from_isoformat(date_string):
    return datetime.date.fromisoformat(date_string)


@register.simple_tag()
def values_list(qs, attrs):
    attributes = attrs.split(',')
    return qs.values_list(*attributes, flat=True)


@register.filter()
def get_objects_by_ids(ids, model):
    ids_list = ids.split(',')
    content_type = ContentType.objects.get_by_natural_key(*model.split('.'))

    if not content_type:
        return None

    objects = content_type.model_class().objects.filter(id__in=ids_list)
    return ', '.join(str(obj) for obj in objects.all())

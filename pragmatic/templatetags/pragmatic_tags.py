import os
import urllib

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy as _
from python_pragmatic.strings import barcode as pragmatic_barcode

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, list):
        dictionary = dict(dictionary)

    return dictionary.get(key, key)

@register.filter
@stringfilter
def split(string, sep):
    """Return the string split by sep.

    Example usage: {{ value|split:"/" }}
    """
    return string.split(sep)


@register.filter('klass')
def klass(ob):
    return ob.__class__.__name__


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
                    label_suffix = ugettext('after') if ending == '_after' else ugettext('from')
                else:
                    slice_value_name = 'stop'
                    label_suffix = ugettext('before') if ending == '_before' else ugettext('to')

        filter_field = filter.filters.get(filter_name, None)

        if filter_field:
            value = cleaned_data.get(filter_name, None)

            if value:
                if isinstance(value, list):
                    # multiple choice field
                    value_values = []

                    for v in value:
                        try:
                            v_display = dict(form.fields[filter_name].choices)[v]
                            v_display = str(v_display)
                            value_values.append(v_display)
                        except (KeyError, AttributeError):
                            value_values.append(str(v))

                    value = ', '.join(value_values)
                else:
                    # choice field
                    try:
                        value = dict(form.fields[filter_name].choices)[value]
                    except (KeyError, AttributeError):
                        pass

                if isinstance(value, slice):
                    # range field
                    if slice_value_name:
                        value = getattr(value, slice_value_name)
                    else:
                        if value.start and value.stop:
                            value = ' - '.join([str(value.start), str(value.stop)])
                        else:
                            if value.start:
                                value = ugettext('at least') + ' ' + str(value.start)
                            elif value.stop:
                                value = ugettext('up to') + ' ' + str(value.stop)

                values[param] = {
                    'label': (filter_field.label + ' ' + label_suffix).strip(),
                    'value': value
                }

    return values


@register.filter('filtered_objects_counts')
def filtered_objects_counts(filtered, all):
    try:
        if filtered == all or all == 0:
            return mark_safe('%s: <strong>%d</strong>' % (ugettext(u'total'), all))
        else:
            percent = 100 * float(filtered) / all
            return mark_safe('<strong>%d (%.2f%%)</strong> %s %d' % (filtered, percent, ugettext(u'filtered, from a total of'), all))
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

    url = conditional_escape("http://chart.apis.google.com/chart?%s" %\
                             urllib.urlencode({'chs': '250x250', 'cht': 'qr', 'chl': value, 'choe': 'UTF-8'}))
    alt = conditional_escape(alt or value)

    return mark_safe(u"""<img class="qrcode" src="%s" width="250" height="250" alt="%s" />""" % (url, alt))


@register.filter
@stringfilter
def barcode(code, args=None):
    from barcode.errors import IllegalCharacterError

    try:
        barcode = pragmatic_barcode(code, args)
        # return as HTML element
        return mark_safe('<img src="data:image/png;base64,' + barcode + '" />')
    except IllegalCharacterError as e:
        message = unicode(e)
        character = message.split(':', 1)[1]
        return u'{}: {}'.format(_('Invalid characters'), character)


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
    return ugettext(text)


@register.filter
def filename(value):
    try:
        return os.path.basename(unicode(value.file.name))
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


@register.filter()
def add_query_param(url, param):
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

    # add (replace) param to querydict
    for key, value in QueryDict(param).items():
        querydict[key] = value

    # encode params to string
    encoded_params = querydict.urlencode()

    # construct new path
    new_url = '{}?{}'.format(path, encoded_params)

    return new_url.strip('?')


@register.filter()
def remove_query_param(url, param):
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

    # remove param from querydict (if exists)
    for key, value in QueryDict(param).items():
        if key in querydict:
            querydict.pop(key)

    # encode params to string
    encoded_params = querydict.urlencode()

    # construct new path
    new_url = '{}?{}'.format(path, encoded_params)

    return new_url.strip('?')

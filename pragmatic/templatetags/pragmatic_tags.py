import os
import urllib

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext

register = template.Library()

from python_pragmatic.strings import barcode as pragmatic_barcode

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
    barcode = pragmatic_barcode(code, args)
    # return as HTML element
    return mark_safe('<img src="data:image/png;base64,' + barcode + '" />')


@register.inclusion_tag('helpers/pagination.html', takes_context=True)
def paginator(context, objects, page_ident='page', anchor=None, adjacent=2):
    page_range = objects.paginator.page_range
    number = objects.number

    page_numbers = [n for n in range(number - adjacent, number + adjacent + 1)
                    if n > 0 and n <= len(page_range)]

    show_left_dots = True
    if number - adjacent - 1 == 1:
        show_left_dots = False

    show_right_dots = True
    if number + adjacent + 1 == len(page_range):
        show_right_dots = False

    return {
        'anchor': anchor,
        'request': context.get('request', None),
        'page_ident': page_ident,
        'results_per_page': objects.paginator.per_page,
        'page': objects.number,
        'pages': page_range,
        'count': len(page_range),
        'page_numbers': page_numbers,
        'next': objects.next_page_number,
        'previous': objects.previous_page_number,
        'has_next': objects.has_next,
        'has_previous': objects.has_previous,
        'show_first': 1 not in page_numbers,
        'show_last': False if len(page_range) - number <= adjacent else True,
        'show_left_dots': show_left_dots,
        'show_right_dots': show_right_dots,
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
def add(value, arg):
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

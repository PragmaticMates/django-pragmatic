from itertools import chain

from django import forms
from django.forms import TextInput
from django.forms.widgets import CheckboxSelectMultiple, CheckboxInput
from django.utils.encoding import force_str
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class GroupedCheckboxSelectMultiple(CheckboxSelectMultiple):
    '''
    Sample usage:

    class HomeForm(forms.Form):
        rules = forms.MultipleChoiceField(initial=('b', 'g'), choices=(
            ('a', 'a'),
            ('b', 'b'),
            ('c', 'c'),
            ('d', 'd'),
            ('e', 'e'),
            ('f', 'f'),
            ('g', 'g'),
            ('h', 'h'),

        ), widget=GroupedCheckboxSelectMultiple(attrs={
            'groups': (
                (ugettext('Group 1'), {
                    'classes': ('col-md-3', ),
                    'choices': (('a', 'a'), ('b', 'b'), ),
                }),

                (ugettext('Group 2'), {
                    'classes': ('col-md-3', ),
                    'predefined_values_on_check': 'all'|None|list(),
                    'choices': (('c', 'c'), ('d', 'd'), ),
                }),

                (ugettext('Group 3'), {
                    'classes': ('col-md-3', ),
                    'choices': (('e', 'e'), ('f', 'f'), ),
                }),

                (ugettext('Group 4'), {
                    'classes': ('col-md-3', ),
                    'choices': (('g', 'g'), ('h', 'h'), ),
                }),
            )
        }))

        def __init__(self, *args, **kwargs):
            super(HomeForm, self).__init__(*args, **kwargs)
            self.fields['rules'].label = ''
    '''

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)

        # No groups in widget so render checkboxes in normal way
        if 'groups' not in final_attrs:
            output = []
            # Normalize to strings
            str_values = set([force_str(v) for v in value])
            for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
                # If an ID attribute was given, add a numeric index as a suffix,
                # so that the checkboxes don't all have the same ID attribute.
                if has_id:
                    final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                    label_for = format_html(' for="{0}"', final_attrs['id'])
                else:
                    label_for = ''

                cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
                option_value = force_str(option_value)
                rendered_cb = cb.render(name, option_value)
                option_label = force_str(option_label)
                output.append('<div class="checkbox"><label%s>%s %s</label></div>' % (label_for, rendered_cb, option_label))
            return mark_safe('\n'.join(output))

        output = []
        groups = final_attrs['groups']

        if 'groups' in final_attrs:
            del final_attrs['groups']

        for group_index, group in enumerate(groups):
            str_values = set([force_str(v) for v in value])
            group_id = 'group_%i' % group_index

            result = ['<ul class="list-group">']

            has_opened_checkboxes = False
            for checkbox_index, (option_value, option_label) in enumerate(group[1]['choices']):
                if has_id:
                    final_attrs = dict(final_attrs, id='%s_%s_%s' % (attrs['id'], group_index, checkbox_index))
                    label_for = format_html(' for="{0}"', final_attrs['id'])
                else:
                    label_for = ''

                cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
                if cb.check_test(str(option_value)):
                    has_opened_checkboxes = True
                    break

            open_group = False
            for checkbox_index, (option_value, option_label) in enumerate(group[1]['choices']):
                if has_id:
                    final_attrs = dict(final_attrs, id='%s_%s_%s' % (attrs['id'], group_index, checkbox_index))
                    label_for = format_html(' for="{0}"', final_attrs['id'])
                else:
                    label_for = ''

                if 'on_check' in final_attrs:
                    del final_attrs['on_check']

                if has_opened_checkboxes is False and 'predefined_values_on_check' in group[1]:
                    predefined_values = group[1]['predefined_values_on_check']

                    if type(predefined_values) == str:
                        if predefined_values == 'all':
                            final_attrs['on_check'] = 'checked'
                    elif type(predefined_values) == list or type(predefined_values) == tuple:
                        if option_value in predefined_values:
                            final_attrs['on_check'] = 'checked'

                cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)

                if cb.check_test(str(option_value)):
                    open_group = True

                option_value = force_str(option_value)
                rendered_cb = cb.render(name, option_value)
                option_label = force_str(option_label)
                result.append('<li class="list-group-item"><div class="checkbox"><label%s>%s %s</label></div></li>' % (label_for, rendered_cb, option_label))
            result.append('</ul>')

            output.append('<div class="group %(classes)s"><div class="panel panel-primary"><div class="panel-heading">%(heading)s</div>%(result)s</div></div>' % {
                'heading': '<h4 class="panel-title checkbox"><label for="%(group_id)s">%(title)s</label></h4><a href="#" class="toggler"></a>' % {
                    'group_id': group_id,
                    'title': CheckboxInput().render(group_id, open_group, attrs={
                        'id': group_id,
                    }) + group[0],
                },
                'classes': ' '.join(group[1]['classes']) if 'classes' in group[1] else '',
                'result': '\n'.join(result),
            })

        return mark_safe('\n'.join(output))


class SliderWidget(TextInput):
    template_name = 'widgets/slider_input.html'

    default_attrs = {
        'data-slider-min': '0',
        'data-slider-max': '100',
        'data-slider-step': '1',
        # 'data-slider-value': '50',
        'data-slider-tooltip': 'show',
        'data-slider-show-value': 'true',
    }

    def __init__(self, attrs=None, render_value=False):
        super().__init__(attrs)
        self.render_value = render_value
        self.attrs.update(self.default_attrs)

        if attrs:
            self.attrs.update(attrs)


class VersionedMediaJS:
    def __init__(self, path, version):
        self.path = forms.widgets.Media.absolute_path(None, path)
        self.version = version

    def __repr__(self):
        return 'VersionedMediaJS(path=%r, version=%r)' % (self.path, self.version)

    def __str__(self):
        return self.render()

    def render(self):
        html = '<script type="text/javascript" src="{0}?{1}"></script>'
        return format_html(html, mark_safe(self.path), self.version)

    @staticmethod
    def render_js(media_object):
        html = []
        for path in media_object._js:
            if hasattr(path, 'version'):
                html.append(path.render())
            else:
                html.append(format_html('<script type="text/javascript" src="{0}"></script>', media_object.absolute_path(path)))
        return html


forms.widgets.Media.render_js = VersionedMediaJS.render_js


try:
    import mapwidgets

    class AutocompleteGooglePointFieldWidget(mapwidgets.GooglePointFieldWidget):
        @property
        def media(self):
            js = super().media._js + ["pragmatic/js/map-widget-utils.js", ]
            return forms.Media(js=js, css=super().media._css)

        def render(self, name, value, attrs=None, renderer=None):
            return super().render(name, value, attrs)


    class AutocompleteCityWidget(TextInput):
        def __init__(self, attrs=None):
            super().__init__(attrs)
            from mapwidgets.settings import mw_settings
            self.attrs['data-google-key'] = mw_settings.GOOGLE_MAP_API_KEY

        @property
        def media(self):
            # js = VersionedMediaJS('pragmatic/js/city-autocomplete.js', settings.DEPLOYMENT_TIMESTAMP)  # TODO: fix version
            return forms.Media(js=('pragmatic/js/city-autocomplete.js',))
except ImportError:
    pass

from django.forms import ModelChoiceField
from django.utils.encoding import smart_text

import django_filters
from fields import RangeField


class AdvancedModelChoiceField(ModelChoiceField):
    def __init__(self, queryset, empty_label="---------", cache_choices=False,
                 truncate_suffix='...', truncate_chars=None,
                 required=True, widget=None, label=None, initial=None,
                 help_text=None, to_field_name=None, *args, **kwargs):

        self.truncate_chars = truncate_chars
        self.truncate_suffix = truncate_suffix

        super(AdvancedModelChoiceField, self).__init__(queryset,
            empty_label=empty_label, cache_choices=cache_choices,
            required=required, widget=widget, label=label, initial=initial,
            help_text=help_text, to_field_name=to_field_name, *args, **kwargs)

    def label_from_instance(self, obj):
        if self.truncate_chars:
            return smart_text(obj)[:self.truncate_chars] +\
                   (smart_text(obj)[self.truncate_chars:] and self.truncate_suffix)
        return smart_text(obj)



class AdvancedModelChoiceFilter(django_filters.Filter):
    field_class = AdvancedModelChoiceField


class OneFieldRangeFilter(django_filters.Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__range' % self.name: (value[0], value[1])})
        return qs
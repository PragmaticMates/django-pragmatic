import django_filters
from django.core.validators import EMPTY_VALUES
from pragmatic.fields import TruncatedModelChoiceField, RangeField


class ArrayFilter(django_filters.CharFilter):
    lookup = 'contains'

    def filter(self, qs, value):
        if value not in EMPTY_VALUES:
            value = [value]
            return qs.filter(**{'%s__%s' % (self.field_name, self.lookup): value})
        return qs


class TruncatedModelChoiceFilter(django_filters.Filter):
    field_class = TruncatedModelChoiceField


class OneFieldRangeFilter(django_filters.Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__range' % self.name: (value[0], value[1])})
        return qs

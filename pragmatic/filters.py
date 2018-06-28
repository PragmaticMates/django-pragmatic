from django.db.models import Q

import django_filters
from django.core.validators import EMPTY_VALUES
from pragmatic.fields import TruncatedModelChoiceField, RangeField


class ArrayFilter(django_filters.CharFilter):
    lookup = 'contains'
    array_size = 5

    def __init__(self, array_size=5, **kwargs):
        super(ArrayFilter, self).__init__(**kwargs)
        self.array_size = array_size

    def filter(self, qs, value):
        if value not in EMPTY_VALUES:
            kwargs = Q(**{'%s__%s' % (self.field_name, self.lookup): [value]})

            for i in range(self.array_size):
                kwargs |= Q(**{'%s__%d__%s' % (self.field_name, i, self.lookup_expr): value})

            return qs.filter(kwargs)
        return qs


class TruncatedModelChoiceFilter(django_filters.Filter):
    field_class = TruncatedModelChoiceField


class OneFieldRangeFilter(django_filters.Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__range' % self.name: (value[0], value[1])})
        return qs

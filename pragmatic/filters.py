import django_filters

from fields import TruncatedModelChoiceField, RangeField


class TruncatedModelChoiceFilter(django_filters.Filter):
    field_class = TruncatedModelChoiceField


class OneFieldRangeFilter(django_filters.Filter):
    field_class = RangeField

    def filter(self, qs, value):
        if value:
            return qs.filter(**{'%s__range' % self.name: (value[0], value[1])})
        return qs

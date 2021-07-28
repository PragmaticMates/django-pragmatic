import json
import django_filters
from django import forms
from django.apps import apps
from django.core.cache import cache
from django.core.validators import EMPTY_VALUES
from django.db.models import Max, Min, Count, Q
from django_filters.constants import EMPTY_VALUES
from pragmatic.fields import TruncatedModelChoiceField, RangeField, SliderField
from django.core.exceptions import ImproperlyConfigured


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


class IntegerFilter(django_filters.NumberFilter):
    field_class = forms.IntegerField


class PositiveBooleanFilter(django_filters.BooleanFilter):
    def filter(self, qs, value):
        if not value:
            return qs
        return super().filter(qs, value)


class SliderFilter(django_filters.Filter):
    field_class = SliderField
    queryset_method = 'all'
    count = 20

    def __init__(self, *args, **kwargs):
        segment = kwargs.pop('segment', None)
        self.count = kwargs.pop('count', self.count)
        self.queryset_method = kwargs.pop('queryset_method', self.queryset_method)
        super().__init__(*args, **kwargs)

        if segment:
            self.init_segments(segment)

        self.lookup_expr = kwargs.get('lookup_expr', 'lte')

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        if isinstance(value, slice):
            if value.start:
                qs = qs.filter(**{'%s__gte' % self.field_name: value.start})

            if value.stop:
                qs = qs.filter(**{'%s__lte' % self.field_name: value.stop})
        else:
            qs = super().filter(qs, value)

        return qs

    def init_segments(self, segment):
        range_highlights = []

        dispersion = self.get_segments(segment)

        if dispersion:
            min_value = dispersion.get('min')
            max_value = dispersion.get('max')
            segments = dispersion.get('segments')

            if segments:
                max_count = max(segments.values())
                segment = (max_value - min_value) / self.count

                for num in range(0, self.count):
                    value_percent = int(segments.get("segment_" + str(num), 0) / max_count * 100)
                    class_name = 'hl-' + str(value_percent) + 'p'
                    range_highlights.append({'start': float(min_value + segment * num), 'end': float(min_value + segment * (num + 1)), 'class': class_name})

                self.field.widget.attrs.update({'data-slider-max': max_value})
                self.field.widget.attrs.update({'data-slider-min': min_value})
                self.field.widget.attrs.update({'data-slider-rangeHighlights': json.dumps(range_highlights)})
                self.field.min = min_value
                self.field.max = max_value

    def get_segment_details(self, segment):
        app_label, model_name, field_name = segment.split('.')
        model_class = apps.get_model(app_label=app_label, model_name=model_name)
        cache_key = 'slider_segments'
        cache_version = '{}_{}_{}'.format(self.count, model_class.__name__, field_name)

        return {
            'app_label': app_label,
            'model_name': model_name,
            'field_name': field_name,
            'cache_key': cache_key,
            'cache_version': cache_version,
        }

    def get_segments(self, segment):
        # read cache
        segment_details = self.get_segment_details(segment)

        try:
            saved_value = cache.get(segment_details['cache_key'], version=segment_details['cache_version'])
        except ImproperlyConfigured:
            saved_value = None

        if saved_value is not None:
            return saved_value

        model_class = apps.get_model(app_label=segment_details['app_label'], model_name=segment_details['model_name'])
        field_name = segment_details['field_name']

        qs = model_class._default_manager
        qs = getattr(qs, self.queryset_method)()

        try:
            if not qs.exists():
                return {}
        except:
            return {}

        qs = qs.values(field_name, 'id')
        min_max_count_value = qs.aggregate(Max(field_name), Min(field_name), Count('id'))
        min_value = min_max_count_value[f'{field_name}__min']
        max_value = min_max_count_value[f'{field_name}__max']
        count_values = min_max_count_value['id__count']
        aggregate_params = {}
        segments = {}

        if max_value is not None and min_value is not None:
            segment = (max_value - min_value) / self.count

            for num in range(0, self.count):
                segment_name = 'segment_' + str(num)
                query_args = {f'{field_name}__range': (min_value + segment * num, min_value + segment * (num + 1))}
                aggregate_params.update({segment_name: Count('pk', filter=Q(**query_args))})

            segments = qs.aggregate(**aggregate_params)

        store = {
            'segments': segments,
            'min': min_value,
            'max': max_value,
            'count': count_values,
        }

        # save into cache
        try:
            cache.set(segment_details['cache_key'], store, version=segment_details['cache_version'], timeout=86400)
        except ImproperlyConfigured:
            pass

        return store

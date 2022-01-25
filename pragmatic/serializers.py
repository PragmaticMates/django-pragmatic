from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        exclude = []
        fields = ['id', 'app_label', 'model']

    def to_internal_value(self, data):
        if isinstance(data, dict):
            app_label = data['app_label']
            model = data['model']
        else:
            app_label, model = data.split('.')

        content_type = ContentType.objects.get_by_natural_key(app_label, model)

        return {
            'id': content_type.id,
            'app_label': app_label,
            'model': model
        }

    def to_representation(self, instance):
        return '.'.join(instance.natural_key())


class ContentTypeNaturalField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        self.queryset = kwargs.pop('queryset', ContentType.objects.all())
        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        return ContentType.objects.get_by_natural_key(*data.split('.'))

    def to_representation(self, value):
        return '.'.join(value.natural_key())

from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        exclude = []
        fields = ['id', 'app_label', 'model']

    def to_internal_value(self, data):
        app_label, model = data.split('.')

        content_type = ContentType.objects.get_by_natural_key(app_label, model)

        return {
            'id': content_type.id,
            'app_label': app_label,
            'model': model
        }

    def to_representation(self, instance):
        return '.'.join(instance.natural_key())

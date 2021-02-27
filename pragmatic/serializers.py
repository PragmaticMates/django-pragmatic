import json

from django.contrib.gis.geos import Point
from rest_framework import serializers


class PointField(serializers.Field):
    """
    Point objects are serialized into '{latitude, longitude}' notation.
    """
    def to_representation(self, value):
        return {
            'latitude': value.y,
            'longitude': value.x,
        }

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = json.loads(data)
        return Point(data['longitude'], data['latitude'])

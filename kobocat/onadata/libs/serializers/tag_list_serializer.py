from rest_framework import serializers
from rest_framework.exceptions import ParseError


class TagListSerializer(serializers.WritableField):

    def from_native(self, data):
        if type(data) is not list:
            raise ParseError("expected a list of data")

        return data

    def to_native(self, obj):
        if obj is None:
            return super(TagListSerializer, self).to_native(obj)

        if type(obj) is not list:
            return list(obj.values_list('name', flat=True))

        return obj

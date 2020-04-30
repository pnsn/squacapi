from drf_yasg.inspectors import SwaggerAutoSchema
from collections import OrderedDict


class ReadOnly():
    def get_fields(self):
        new_fields = OrderedDict()
        for fieldName, field in super().get_fields().items():
            if not field.write_only:
                new_fields[fieldName] = field
        return new_fields


class WriteOnly():
    def get_fields(self):
        new_fields = OrderedDict()
        for fieldName, field in super().get_fields().items():
            if not field.read_only:
                new_fields[fieldName] = field
        return new_fields


class BlankMeta:
    pass


class ReadWriteAutoSchema(SwaggerAutoSchema):
    """
    Generates Read-only and write-only versions of the schema for the
    serializer
    Credit to Eric Bauerfeld
    https://github.com/axnsan12/drf-yasg/issues/70#issuecomment-485050813
    """
    def get_view_serializer(self):
        return self._convert_serializer(WriteOnly)

    def get_default_response_serializer(self):
        # nobody is not defined. commenting out
        # body_override = self._get_request_body_override()
        # if body_override and body_override is not no_body:
        #     return body_override

        return self._convert_serializer(ReadOnly)

    def _convert_serializer(self, new_class):
        serializer = super().get_view_serializer()
        if not serializer:
            return serializer

        class CustomSerializer(new_class, serializer.__class__):
            class Meta(getattr(serializer.__class__, 'Meta', BlankMeta)):
                ref_name = new_class.__name__ + serializer.__class__.__name__

        new_serializer = CustomSerializer(data=serializer.data)
        return new_serializer

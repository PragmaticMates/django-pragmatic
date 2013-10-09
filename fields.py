from django.core.exceptions import ValidationError
from django.core.validators import EMPTY_VALUES
from django.forms import Field
from django.utils.translation import ugettext_lazy as _


class RangeField(Field):
    default_error_messages = {
        'invalid': _("Enter a number or range of numbers with '-' separator."),
    }

    def to_python(self, value):
        """
        Validates input value. It has to be number of range of number.
        Returns the list or range limits or None for empty values.
        """
        if value in EMPTY_VALUES:
            return None
        value = value.strip()
        #value = smart_text(value)

        #if self.localize:
        #    value = formats.sanitize_separators(value)

        try:
            value = float(value)
            start = value
            stop = value
            return start, stop
        except (ValueError, TypeError):
            pass

        try:
            start, stop = value.split('-', 1)
            start = float(start.strip())
            stop = float(stop.strip())
            return start, stop
        except (ValueError, TypeError):
            raise ValidationError(self.error_messages['invalid'])

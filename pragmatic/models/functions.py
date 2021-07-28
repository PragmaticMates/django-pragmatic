from django.db.models.expressions import Func, Expression
from pragmatic.models.expressions import F, Value


class Round(Func):
    function = 'ROUND'
    arity = 2


# https://github.com/primal100/django_postgres_extensions
class SimpleFunc(Func):

    def __init__(self, field, *values, **extra):
        if not isinstance(field, Expression):
            field = F(field)
            if values and not isinstance(values[0], Expression):
                values = [Value(v) for v in values]
        super(SimpleFunc, self).__init__(field, *values, **extra)


class ArrayAppend(SimpleFunc):
    function = 'ARRAY_APPEND'


class ArrayPrepend(Func):
    function = 'ARRAY_PREPEND'

    def __init__(self, value, field, **extra):
        if not isinstance(value, Expression):
            value = Value(value)
            field = F(field)
        super(ArrayPrepend, self).__init__(value, field, **extra)


class ArrayRemove(SimpleFunc):
    function = 'ARRAY_REMOVE'


class ArrayReplace(SimpleFunc):
    function = 'ARRAY_REPLACE'


class ArrayPosition(SimpleFunc):
    function = 'ARRAY_POSITION'


class ArrayPositions(SimpleFunc):
    function = 'ARRAY_POSITIONS'


class ArrayLength(SimpleFunc):
    function = 'ARRAY_LENGTH'

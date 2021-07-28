from django.db.models.expressions import F as BaseF, Value as BaseValue, Func, Expression


# https://github.com/primal100/django_postgres_extensions
class OperatorMixin(object):
    CAT = '||'
    REPLACE = '#='
    DELETE = '#-'
    KEY = '->'
    KEYTEXT = '->>'
    PATH = '#>'
    PATHTEXT = '#>>'

    def cat(self, other):
        return self._combine(other, self.CAT, False)

    def replace(self, other):
        return self._combine(other, self.REPLACE, False)

    def delete(self, other):
        return self._combine(other, self.DELETE, False)

    def key(self, other):
        return self._combine(other, self.KEY, False)

    def keytext(self, other):
        return self._combine(other, self.KEYTEXT, False)

    def path(self, other):
        return self._combine(other, self.PATH, False)

    def pathtext(self, other):
        return self._combine(other, self.PATHTEXT, False)


class F(BaseF, OperatorMixin):
    pass


class Value(BaseValue, OperatorMixin):
    def as_sql(self, compiler, connection):
        if self._output_field_or_none and any(self._output_field_or_none.get_internal_type() == fieldname for fieldname in
                                      ['ArrayField', 'MultiReferenceArrayField']):
            base_field = self._output_field_or_none.base_field
            return '%s::%s[]' % ('%s', base_field.db_type(connection)), [self.value]
        return super(Value, self).as_sql(compiler, connection)

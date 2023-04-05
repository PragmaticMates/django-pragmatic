import sqlparse
from debug_toolbar.panels.sql import SQLPanel as ToolbarSQLPanel
from debug_toolbar.panels.sql import views
from debug_toolbar.panels.sql.forms import SQLSelectForm
from django.http import HttpResponseBadRequest
from django.urls import re_path

try:
    # Django>=3.0
    from django.shortcuts import render
except ImportError:
    # older Django
    from django.shortcuts import render_to_response as render


from django.views.decorators.csrf import csrf_exempt


class SQLPanel(ToolbarSQLPanel):
    @classmethod
    def get_urls(cls):
        return [
            re_path(r'^sql_select/$', views.sql_select, name='sql_select'),
            re_path(r'^sql_explain/$', sql_explain, name='sql_explain'),
            re_path(r'^sql_profile/$', views.sql_profile, name='sql_profile'),
        ]


@csrf_exempt
def sql_explain(request):
    """Returns the output of the SQL EXPLAIN on the given query"""
    form = SQLSelectForm(request.POST or None)

    if form.is_valid():
        sql = form.cleaned_data['raw_sql']
        params = form.cleaned_data['params']
        vendor = form.connection.vendor
        cursor = form.cursor

        if vendor == 'sqlite':
            # SQLite's EXPLAIN dumps the low-level opcodes generated for a query;
            # EXPLAIN QUERY PLAN dumps a more human-readable summary
            # See http://www.sqlite.org/lang_explain.html for details
            cursor.execute("EXPLAIN QUERY PLAN %s" % (sql,), params)
        elif vendor == 'postgresql':
            cursor.execute("EXPLAIN ANALYZE %s" % (sql,), params)
        else:
            cursor.execute("EXPLAIN %s" % (sql,), params)

        headers = [d[0] for d in cursor.description]
        result = cursor.fetchall()
        cursor.close()
        context = {
            'result': result,
            'sql': form.reformat_sql(),
            'sql_raw': sqlparse.format(form.cleaned_data['sql'], reindent=True, keyword_case='upper'),
            'duration': form.cleaned_data['duration'],
            'headers': headers,
            'alias': form.cleaned_data['alias'],
        }
        # Using render()/render_to_response() avoids running global context processors.
        return render('panels/sql_explain.html', context)
    return HttpResponseBadRequest('Form errors')

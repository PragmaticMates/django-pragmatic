# django-pragmatic

[![Build Status](https://travis-ci.org/PragmaticMates/django-pragmatic.svg?branch=master)](https://travis-ci.org/PragmaticMates/django-pragmatic)

Pragmatic tools and utilities for Django projects.

## Requirements

- Python 3.8+
- Django 3.2+
- [django-filter](https://django-filter.readthedocs.io/)
- [python-pragmatic](https://github.com/PragmaticMates/python-pragmatic)

Optional dependencies are required only for the modules that use them
(see [Installation](https://django-pragmatic.readthedocs.io/en/latest/installation.html)).

## Installation

```bash
pip install django-pragmatic
```

Add `pragmatic` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'pragmatic',
]
```

Run migrations (needed only if you use deleted-object tracking):

```bash
python manage.py migrate pragmatic
```

## What's included

| Module | Description |
|---|---|
| [Models](https://django-pragmatic.readthedocs.io/en/latest/models.html) | `DeletedObject` — audit trail for deleted instances |
| [Mixins](https://django-pragmatic.readthedocs.io/en/latest/mixins.html) | CBV/form mixins: permissions, delete, pagination, sorting, display modes, PDF, slugs |
| [Decorators](https://django-pragmatic.readthedocs.io/en/latest/decorators.html) | `permissions_required`, `permission_required`, PostgreSQL lock, `Cached` |
| [Template tags](https://django-pragmatic.readthedocs.io/en/latest/templatetags.html) | `{% load pragmatic_tags %}` — filter display, sorting, pagination, URL tools |
| [Fields](https://django-pragmatic.readthedocs.io/en/latest/fields.html) | `RangeField`, `SliderField`, `MultiSelectField`, `ChoiceArrayField` |
| [Filters](https://django-pragmatic.readthedocs.io/en/latest/filters.html) | `SliderFilter`, `OneFieldRangeFilter`, `ArrayFilter` and more |
| [Widgets](https://django-pragmatic.readthedocs.io/en/latest/widgets.html) | `GroupedCheckboxSelectMultiple`, `SliderWidget`, map widgets |
| [Middleware](https://django-pragmatic.readthedocs.io/en/latest/middleware.html) | `MaintenanceModeMiddleware` — serve 503 during downtime |
| [Managers](https://django-pragmatic.readthedocs.io/en/latest/managers.html) | `EmailManager` — template-based email with optional RQ queue |
| [Context processors](https://django-pragmatic.readthedocs.io/en/latest/context_processors.html) | Date formats, installed apps, URL identifier, settings |
| [Signals](https://django-pragmatic.readthedocs.io/en/latest/signals.html) | `SignalsHelper`, `apm_custom_context`, `disable_signals` |
| [Utils](https://django-pragmatic.readthedocs.io/en/latest/utils.html) | `build_absolute_uri`, `get_task_decorator`, zip compression |
| [Jobs](https://django-pragmatic.readthedocs.io/en/latest/jobs.html) | Background email via RQ, `ConnectionClosingWorker` |
| [REST Framework](https://django-pragmatic.readthedocs.io/en/latest/rest_framework.html) | `ContentTypeSerializer`, `HybridRouter`, `BearerAuthentication` |
| [Management commands](https://django-pragmatic.readthedocs.io/en/latest/management_commands.html) | `clean_migrations`, `rqscheduler` |

## Quick examples

**Maintenance mode:**

```python
# settings.py
MAINTENANCE_MODE = True
MAINTENANCE_MODE_BYPASS_USERS = [1]  # superuser can still log in
```

**Send an email from a template:**

```python
from pragmatic.managers import EmailManager

EmailManager.send_mail(
    to=user,
    template_prefix='emails/welcome',
    subject='Welcome!',
    data={'activation_link': url},
    request=request,
)
```

**List view with display modes and sorting:**

```python
from pragmatic.mixins import DisplayListViewMixin, SortingListViewMixin

class ArticleListView(SortingListViewMixin, DisplayListViewMixin, ListView):
    model = Article
    displays = ['list', 'table']
    paginate_by_display = {'list': [10, 25], 'table': 100}
    sorting_options = {'-created': 'Newest', 'title': 'Title A–Z'}
```

**Template filter values display:**

```django
{% load pragmatic_tags %}
{% filter_values filter %}
{% num_applied_filters filter request.GET as n %}
{{ n }} active filter{{ n|pluralize }}
```

**Background task decorator:**

```python
# settings.py
PRAGMATIC_TASK_DECORATOR = 'django_rq.job'  # or 'celery.shared_task'
```

```python
from pragmatic.utils import get_task_decorator

task = get_task_decorator(queue='default')

@task
def process_export(export_id):
    ...
```

## Documentation

Full documentation is at [django-pragmatic.readthedocs.io](https://django-pragmatic.readthedocs.io/).

## License

BSD License — see [LICENSE](LICENSE) for details.

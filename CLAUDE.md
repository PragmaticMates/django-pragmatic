# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`django-pragmatic` is a reusable Django library (v6.0.3) providing utilities, mixins, and helpers for Django projects. It is distributed as a pip package (`pip install django-pragmatic`) and requires `django>=3.2`, `django-filter`, and `python-pragmatic`.

## Build & Install

```bash
# Install in development mode
pip install -e .

# Build distribution
python setup.py sdist

# Run tests (no dedicated test suite — uses setup.py test via Travis CI)
python setup.py test
```

## Architecture

The package lives entirely in `pragmatic/` with no sub-applications. All modules are flat utilities intended to be imported a-la-carte:

- **`pragmatic/models/__init__.py`** — `DeletedObject` model: tracks deleted objects via ContentType framework. Activated by setting `PRAGMATIC_TRACK_DELETED_OBJECTS = True` in settings.
- **`pragmatic/mixins.py`** — CBV and form mixins. Key ones:
  - `ReadOnlyFormMixin` — makes specified fields readonly/disabled on existing instances
  - `LoginPermissionRequiredMixin`, `StaffRequiredMixin`, `SuperuserRequiredMixin` — access control
  - `DeleteObjectMixin`, `CheckProtectedDeleteObjectMixin` — handles object deletion with ProtectedError handling
  - `DisplayListViewMixin` — supports multiple display modes (list/table/map/etc.) with per-display pagination; sets `template_name_suffix` to `_{display}`
  - `SortingListViewMixin` — URL-param-driven queryset sorting with F() expression support for nulls_last
  - `SafePaginator` — extends Django's Paginator to clamp out-of-range pages to last page
  - `FPDFMixin` — PDF generation via fpdf library
  - `PdfDetailMixin` — renders a detail view as PDF via external API (`HTMLTOPDF_API_URL` or `PRINTMYWEB_URL`/`PRINTMYWEB_TOKEN` settings)
  - `SlugMixin` — auto-generates unique slugs from a field on save
- **`pragmatic/decorators.py`** — `permissions_required`, `permission_required`, `receiver_subclasses`, `require_lock` (PostgreSQL table lock), `Cached` (context manager + `cache_decorator` property decorator)
- **`pragmatic/templatetags/pragmatic_tags.py`** — Load with `{% load pragmatic_tags %}`. Notable tags:
  - `translate_url` — switch language-prefixed URLs, with object-aware fallback
  - `get_item` — recursive attribute/key access from templates
  - `filter_values`, `filtered_values`, `num_applied_filters` — display active django-filters values
  - `display_modes`, `sorting` — inclusion tags for list view UI controls
  - `admin_chart` — renders a chart in Django admin using Chart.js
  - `uri` — builds absolute URI from request (falls back to Sites framework if request is None)
  - URL manipulation filters: `add_query_param`, `replace_query_param`, `remove_query_param`
- **`pragmatic/utils.py`** — `build_absolute_uri` (request-optional absolute URL builder using Sites framework fallback), `compress` (zip utility), `get_task_decorator` (returns task decorator based on `PRAGMATIC_TASK_DECORATOR` setting, defaults to `django.tasks.task`)
- **`pragmatic/managers.py`** — `EmailManager`: sends HTML/text emails from templates, optionally via RQ background queue (`MAILS_QUEUE` setting)
- **`pragmatic/jobs.py`** — `send_mail_in_background` RQ job; `ConnectionClosingWorker`/`ConnectionClosingSimpleWorker` for DB connection cleanup before fork
- **`pragmatic/fields.py`** — Form and model fields: `RangeField`, `MultiSelectField`, `ChoiceArrayField`, `SliderField` (range slider backed by `SliderWidget`)
- **`pragmatic/middleware.py`** — `MaintenanceModeMiddleware`: returns 503 when `MAINTENANCE_MODE = True`; bypasses for users listed in `MAINTENANCE_MODE_BYPASS_USERS`
- **`pragmatic/management/commands/clean_migrations.py`** — Interactive command to squash migrations for apps with a given prefix
- **`pragmatic/management/commands/rqscheduler.py`** — RQ scheduler management command

## Key Settings

| Setting | Description |
|---|---|
| `PRAGMATIC_TRACK_DELETED_OBJECTS` | Enable `DeletedObject` tracking on delete |
| `PRAGMATIC_TASK_DECORATOR` | Task decorator path (default: `django.tasks.task`) |
| `MAINTENANCE_MODE` | Enable maintenance mode (bool) |
| `MAINTENANCE_MODE_BYPASS_USERS` | List of user PKs to bypass maintenance mode |
| `MAILS_QUEUE` | RQ queue name for background emails |
| `HTMLTOPDF_API_URL` / `PRINTMYWEB_URL` | External HTML-to-PDF API endpoint |
| `PRINTMYWEB_TOKEN` | API key for printmyweb |

## Localization

Slovak translations in `pragmatic/locale/sk/LC_MESSAGES/django.po`. Compile with:
```bash
python manage.py compilemessages
```

from django.conf import settings


def date_formats(request):
    """
    Returns a lazy 'date formats' context variables.
    """
    return {
        'DATE_FORMAT_JS': settings.DATE_FORMAT_JS,
        'DATE_FORMAT_TAG': settings.DATE_FORMAT_TAG,
        'DATE_FORMAT_FULLMONTH_TAG': settings.DATE_FORMAT_FULLMONTH_TAG
    }


def installed_apps(request):
    return {
        'INSTALLED_APPS': settings.INSTALLED_APPS
    }

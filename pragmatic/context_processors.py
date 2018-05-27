from django.conf import settings as django_settings


def date_formats(request):
    """
    Returns a lazy 'date formats' context variables.
    """
    return {
        'DATE_FORMAT_JS': django_settings.DATE_FORMAT_JS,
        'DATE_FORMAT_TAG': django_settings.DATE_FORMAT_TAG,
        'DATE_FORMAT_FULLMONTH_TAG': django_settings.DATE_FORMAT_FULLMONTH_TAG
    }


def installed_apps(request):
    return {
        'INSTALLED_APPS': django_settings.INSTALLED_APPS
    }


def url_identifier(request):
    try:
        url_name = request.resolver_match.url_name
    except AttributeError:
        return {}

    try:
        namespace = request.resolver_match.namespaces[0]
        return {
            'url_namespace': namespace,
            'url_name': url_name,
            'url_id': namespace + ':' + url_name
        }
    except IndexError:
        return {
            'url_id': url_name
        }


def settings(request):
    return {
        'settings': django_settings
    }

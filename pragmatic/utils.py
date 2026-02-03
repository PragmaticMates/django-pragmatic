def import_name(name):
    components = name.split('.')
    mod = __import__('.'.join(components[0:-1]), globals(), locals(), [components[-1]])
    return getattr(mod, components[-1])


def compress(files):
    import io
    import zipfile

    file_like_object = io.BytesIO()
    zf = zipfile.ZipFile(file_like_object, mode='w')

    try:
        for file in files:
            name = file.get('name', None)
            content = file.get('content', None)
            if name and content:
                zf.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)

    except FileNotFoundError:
        print('An error occurred during compression')
    finally:
        zf.close()
        file_like_object.seek(0)
        return file_like_object


def build_absolute_uri(request, location, protocol=None):
    """
    Build an absolute URI based on the given request and location.
    Like request.build_absolute_uri, but gracefully handling
    the case where request is None.
    """
    if request:
        return request.build_absolute_uri(location)

    from django.apps import apps
    from django.core.exceptions import ImproperlyConfigured

    if not apps.is_installed("django.contrib.sites"):
        raise ImproperlyConfigured("Passing `request=None` requires `sites` to be enabled.")

    from django.conf import settings
    from django.contrib.sites.models import Site
    from urllib.parse import urlsplit

    protocol = protocol or ("http" if settings.DEBUG else "https")
    site = Site.objects.get_current()
    bits = urlsplit(location)
    return location if bits.scheme and bits.netloc else f"{protocol}://{site.domain}{location}"

def get_task_decorator(queue=None):
    """
    Import task decorator based on PRAGMATIC_TASK_DECORATOR setting.

    Default: 'django.tasks.task' (Django 6.0+)
    Examples: 'django_rq.job', 'celery.shared_task'

    Args:
        queue: Queue name for backends that support it (e.g. django_rq)

    Raises ImportError if the module is not installed.
    """
    from django.conf import settings
    from django.utils.module_loading import import_string

    task_decorator = getattr(settings, 'PRAGMATIC_TASK_DECORATOR', 'django.tasks.task')

    try:
        decorator = import_string(task_decorator)
    except ImportError as e:
        raise ImportError(
            f"Task decorator '{task_decorator}' is not installed. "
            f"Install the required package or set PRAGMATIC_TASK_DECORATOR to a valid decorator path."
        ) from e

    # django_rq.job requires queue name as first argument
    if task_decorator == 'django_rq.job' and queue:
        return decorator(queue)

    return decorator
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

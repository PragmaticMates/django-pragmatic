from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist

from python_pragmatic.classes import get_subclasses


def permissions_required(app_label, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has at least one app permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised and app label of missing permission is stored in user instance.
    """
    def check_perms(user):
        # First check if the user has the permission (even anon users)
        if user.has_module_perms(app_label):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            user.permission_error = app_label
            raise PermissionDenied
        # As the last resort, show the login form
        return False

    return user_passes_test(check_perms, login_url=login_url)


def permission_required(perm, login_url=None, raise_exception=False):
    """
    Decorator for views that checks whether a user has a particular permission
    enabled, redirecting to the log-in page if necessary.
    If the raise_exception parameter is given the PermissionDenied exception
    is raised and missing permission is stored in user instance.
    """
    def check_perms(user):
        # First check if the user has the permission (even anon users)
        if user.has_perm(perm):
            return True
        # In case the 403 handler should be called raise the exception
        if raise_exception:
            try:
                app_label, codename = perm.split('.')
                permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
            except (ObjectDoesNotExist, ValueError):
                permission = perm
            user.permission_error = permission
            raise PermissionDenied
        # As the last resort, show the login form
        return False
    return user_passes_test(check_perms, login_url=login_url)


def receiver_subclasses(signal, sender, dispatch_uid_prefix, **kwargs):
    """
    A decorator for connecting receivers and all receiver's subclasses to signals. Used by passing in the
    signal and keyword arguments to connect::

        @receiver_subclasses(post_save, MyModel, 'mymodel_post_save')
        def signal_receiver(sender, **kwargs):
            ...

    Thanks to: http://codeblogging.net/blogs/1/14/
    """
    def _decorator(func):
        all_senders = get_subclasses(sender)
        #logging.info(all_senders)
        for snd in all_senders:
            signal.connect(func, sender=snd, dispatch_uid=dispatch_uid_prefix+'_'+snd.__name__, **kwargs)
        return func
    return _decorator


LOCK_MODES = (
    'ACCESS SHARE',
    'ROW SHARE',
    'ROW EXCLUSIVE',
    'SHARE UPDATE EXCLUSIVE',
    'SHARE',
    'SHARE ROW EXCLUSIVE',
    'EXCLUSIVE',
    'ACCESS EXCLUSIVE',
)


def require_lock(model, lock='ACCESS EXCLUSIVE'):
    """
    Decorator for PostgreSQL's table-level lock functionality

    Example:
        @transaction.commit_on_success
        @require_lock(MyModel, 'ACCESS EXCLUSIVE')
        def myview(request)
            ...

    PostgreSQL's LOCK Documentation:
    http://www.postgresql.org/docs/8.3/interactive/sql-lock.html
    """

    def require_lock_decorator(view_func):
        def wrapper(*args, **kwargs):
            if lock not in LOCK_MODES:
                raise ValueError('%s is not a PostgreSQL supported lock mode.')
            from django.db import connection
            cursor = connection.cursor()
            cursor.execute(
                'LOCK TABLE %s IN %s MODE' % (model._meta.db_table, lock)
            )
            return view_func(*args, **kwargs)
        return wrapper
    return require_lock_decorator


class Cached(object):
    def __init__(self, key, version=None, user=None, per_user=True, timeout=None):
        self.cache_key = key
        self.version = version
        self.user = user
        self.per_user = per_user
        self.timeout = timeout

    def __enter__(self):
        if self.timeout == 0:
            return None

        # read cache
        return cache.get(self.key, version=self.version)

    def __exit__(self, type, value, traceback):
        pass

    @property
    def key(self):
        if self.user and self.user.is_authenticated and self.per_user:
            return '{}:user={}'.format(self.cache_key, self.user.pk)

        return self.cache_key

    def save(self, data):
        if self.timeout != 0:
            # save to cache
            cache.set(self.key, data, version=self.version, timeout=self.timeout)

    @staticmethod
    def cache_decorator(*args, **kwargs):
        def _decorator(func):
            """
            Decorator to cache return value.
            """

            @property
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                key = kwargs.get('key', None)

                if not key:
                    if hasattr(self, 'cache_key') and self.cache_key:
                        key = f'{self.cache_key}.{func.__name__}'
                    else:
                        key = func.__qualname__

                timeout = kwargs.get('timeout', 3600)
                version = kwargs.get('version', getattr(self, 'cache_version', None))
                cached = cache.get(key, version=version)

                if cached is not None:
                    return cached

                value = func(self, *args, **kwargs)
                cache.set(key, value, version=version, timeout=timeout)

                return value

            return wrapper

        return _decorator
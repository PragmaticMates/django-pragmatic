import logging
import traceback

from django.conf import settings
from django.core import mail
from django.utils.log import AdminEmailHandler
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

# Make sure a NullHandler is available
# This was added in Python 2.7/3.2
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Make sure that dictConfig is available
# This was added in Python 2.7/3.2
try:
    from logging.config import dictConfig
except ImportError:
    from django.utils.dictconfig import dictConfig

getLogger = logging.getLogger

# Ensure the creation of the Django logger
# with a null handler. This ensures we don't get any
# 'No handlers could be found for logger "django"' messages
logger = getLogger('django')
if not logger.handlers:
    logger.addHandler(NullHandler())


class AlternativeAdminEmailHandler(AdminEmailHandler):
    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                (request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 and 'internal' or 'EXTERNAL'),
                record.getMessage()
            )
            filter = get_exception_reporter_filter(request)
            request_repr = filter.get_request_repr(request)
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None
            request_repr = "Request repr() unavailable."
        subject = self.format_subject(subject)

        if record.exc_info:
            exc_info = record.exc_info
            stack_trace = '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            exc_info = (None, record.getMessage(), None)
            stack_trace = 'No stack trace available'

        message = "%s\n\n%s" % (stack_trace, request_repr)
        reporter = ExceptionReporter(request, is_email=True, *exc_info)
        html_message = self.include_html and reporter.get_traceback_html() or None

        # create new connection
        connection = mail.get_connection()
        connection.password = settings.ALTERNATE_EMAIL_HOST_PASSWORD
        connection.username = settings.ALTERNATE_EMAIL_HOST_USER
        connection.host = settings.ALTERNATE_EMAIL_HOST
        connection.port = settings.ALTERNATE_EMAIL_PORT
        connection.use_tls = settings.ALTERNATE_EMAIL_USE_TLS

        mail.mail_admins(subject, message, fail_silently=True, html_message=html_message, connection=connection)

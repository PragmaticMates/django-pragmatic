from django_rq import job
from django.conf import settings
from django.db import connection

from rq.worker import Worker, SimpleWorker


@job(getattr(settings, 'MAILS_QUEUE', 'default'))
def send_mail_in_background(email):
    email.send()


class ConnectionClosingWorker(Worker):
    """
    RQ Worker that closes the database connection before forking.

    See also https://github.com/ui/django-rq/issues/17
    """

    def execute_job(self, job, queue):
        connection.close()
        return super().execute_job(job, queue)


class ConnectionClosingSimpleWorker(SimpleWorker):
    """
        RQ Worker that closes the database connection before forking.

        See also https://github.com/ui/django-rq/issues/17
        """

    def execute_job(self, job, queue):
        connection.close()
        return super().execute_job(job, queue)

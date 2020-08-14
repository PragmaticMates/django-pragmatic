from django_rq import job
from django.conf import settings


@job(settings.MAILS_QUEUE)
def send_mail_in_background(email):
    email.send()

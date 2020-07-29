from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template import loader, TemplateDoesNotExist
from pragmatic.jobs import send_mail_in_background


class EmailManager(object):
    @staticmethod
    def send_mail(recipient, template_prefix, subject, data=None, request=None):
        # template
        try:
            t = loader.get_template(f'{template_prefix}.txt')
        except TemplateDoesNotExist:
            t = None

        # HTML template
        try:
            t_html = loader.get_template(f'{template_prefix}.html')
        except TemplateDoesNotExist:
            t_html = None

        # recipients
        recipient_list = [recipient.email]

        site = get_current_site(request)

        # context
        context = {
            'recipient': recipient,
            'subject': subject,
            'request': request,
            'site': site,
            'settings': settings
        }

        if data:
            context.update(data)

        # message
        message = t.render(context) if t else ''
        html_message = t_html.render(context) if t_html else ''

        if getattr(settings, 'MAILS_QUEUE', None):
            send_mail_in_background.delay(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)
        else:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, html_message=html_message, fail_silently=False)

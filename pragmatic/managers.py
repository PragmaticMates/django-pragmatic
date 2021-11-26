from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.core.validators import EMPTY_VALUES
from django.template import loader, TemplateDoesNotExist


class EmailManager(object):
    @staticmethod
    def get_recipient(to):
        return to if isinstance(to, str) else to.email

    @staticmethod
    def get_recipients(to):
        if not to:
            return None

        recipient_list = []
        if isinstance(to, list):
            for r in to:
                recipient_list.append(EmailManager.get_recipient(r))
        else:
            recipient_list.append(EmailManager.get_recipient(to))

        return recipient_list

    @staticmethod
    def send_mail(to, template_prefix, subject, data=None, attachments=[], reply_to=None, request=None):
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

        # context
        context = {
            'subject': subject,
            'request': request,
            'site': get_current_site(request),
            'settings': settings
        }

        if data:
            context.update(data)

        if not isinstance(to, list):
            context.update({'recipient': to})

        # message
        message = t.render(context) if t else ''
        html_message = t_html.render(context) if t_html else ''

        # message
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=EmailManager.get_recipients(to),
            reply_to=EmailManager.get_recipients(reply_to)
        )

        if html_message not in EMPTY_VALUES:
            email.attach_alternative(html_message, "text/html")

        # attachments
        for attachment in attachments:
            email.attach(attachment['filename'], attachment['content'], attachment['content_type'])

        if getattr(settings, 'MAILS_QUEUE', None):
            from pragmatic.jobs import send_mail_in_background
            send_mail_in_background.delay(email)
        else:
            return email.send()

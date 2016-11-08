from django.conf import settings
from django.http import HttpResponse
from django.template import loader
from django.template.response import SimpleTemplateResponse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django < 1.10
    # Works perfectly for everyone using MIDDLEWARE_CLASSES
    MiddlewareMixin = object


class MaintenanceModeMiddleware(MiddlewareMixin):
    template_name = 'maintenance_mode.html'

    def process_response(self, request, response):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            try:
                context_processors = settings.TEMPLATE_CONTEXT_PROCESSORS
            except AttributeError:
                context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']

            if 'django.core.context_processors.request' in context_processors or \
                'django.template.context_processors.request' in context_processors:
                template = loader.get_template(self.template_name)
                return HttpResponse(template.render({}, request))
            else:
                return SimpleTemplateResponse(self.template_name).render()
        return response

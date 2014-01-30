from django.conf import settings
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.template.response import SimpleTemplateResponse


class MaintenanceModeMiddleware(object):
    template_name = 'maintenance_mode.html'

    def process_response(self, request, response):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            if 'django.core.context_processors.request' in settings.TEMPLATE_CONTEXT_PROCESSORS:
                template = loader.get_template(self.template_name)
                context = RequestContext(request, {})
                return HttpResponse(template.render(context))
            else:
                return SimpleTemplateResponse(self.template_name).render()
        return response

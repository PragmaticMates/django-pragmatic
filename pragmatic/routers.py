from collections import OrderedDict

from rest_framework import routers
from rest_framework.reverse import reverse


# credit: https://newbedev.com/using-django-rest-framework-s-browsable-api-with-apiviews
class HybridRouter(routers.DefaultRouter):
    def __init__(self, *args, **kwargs):
        super(HybridRouter, self).__init__(*args, **kwargs)
        self.view_urls = []

    def add_url(self, view):
        self.view_urls.append(view)

    def get_urls(self):
        return super(HybridRouter, self).get_urls() + self.view_urls

    def get_api_root_view(self, api_urls=[]):
        original_view = super(HybridRouter, self).get_api_root_view()

        def view(request, *args, **kwargs):
            resp = original_view(request, *args, **kwargs)
            namespace = request.resolver_match.namespace
            for view_url in self.view_urls:
                name = view_url.name
                url_name = name
                if namespace:
                    url_name = namespace + ':' + url_name
                resp.data[name] = reverse(url_name,
                                          args=args,
                                          kwargs=kwargs,
                                          request=request,
                                          format=kwargs.get('format', None))
            resp.data = OrderedDict(sorted(resp.data.items()))
            return resp
        return view

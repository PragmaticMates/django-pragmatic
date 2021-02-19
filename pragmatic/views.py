from django.views import View
from django.views.defaults import server_error

from pragmatic.mixins import SuperuserRequiredMixin


class RaiseErrorView(SuperuserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return server_error(request)

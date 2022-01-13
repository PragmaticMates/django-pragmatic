from django.http import JsonResponse
from django_select2.views import AutoResponseView


class AutoSlugResponseView(AutoResponseView):
    def get(self, request, *args, **kwargs):
        """
        Return a :class:`.django.http.JsonResponse`.

        Example::

            {
                'results': [
                    {
                        'text': "foo",
                        'id': "bar"
                    }
                ],
                'more': true
            }

        """
        self.widget = self.get_widget_or_404()
        self.term = kwargs.get("term", request.GET.get("term", ""))
        self.object_list = self.get_queryset()
        context = self.get_context_data()
        return JsonResponse(
            {
                "results": [
                    {"text": self.widget.label_from_instance(obj), "id": obj.slug}
                    for obj in context["object_list"]
                ],
                "more": context["page_obj"].has_next(),
            }
        )

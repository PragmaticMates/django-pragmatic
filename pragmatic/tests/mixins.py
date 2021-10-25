from datetime import timedelta, datetime, date
from inspect import isclass
from time import time

import django_rq
from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.forms import BaseFormSet
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.datastructures import MultiValueDict
from rq import SimpleWorker


class RqMixin(object):
    def setUp(self):
        super().setUp()
        queue = django_rq.get_queue('default')
        queue.empty()

    # workaround for worker running in background http://python-rq.org/docs/testing/
    def run_scheduler_jobs(self, job_name=None, channel='default'):
        scheduler = django_rq.get_scheduler(channel)
        queue = django_rq.get_queue(channel)
        queue.empty()

        for job in scheduler.get_jobs():
            if not job_name or job.func_name.endswith(job_name):
                queue.enqueue_job(job)

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)

    def cancel_scheduler_jobs(self, channel='default'):
        scheduler = django_rq.get_scheduler(channel)

        for job in scheduler.get_jobs():
            scheduler.cancel(job)

    def empty_queue(self, channel='default'):
        queue = django_rq.get_queue(channel)
        queue.empty()

    def run_jobs(self, job_name=None, channel='default'):
        queue = django_rq.get_queue(channel)

        if job_name is not None:
            for job in queue.get_jobs():
                if not job.func_name.endswith(job_name):
                    queue.remove(job)

        worker = SimpleWorker([queue], connection=queue.connection)
        worker.work(burst=True)


class UrlTestMixin(object):
    def iterate_get_urls(self, url_params, urlpatterns=[], all_tested_check=True):
        checked_paths = set()

        for path_name, params in url_params.items():
            params_list = params if isinstance(params, list) else [params]

            for params in params_list:
                path = {
                    'name': path_name,
                    'args': params.get('args', ()),
                    'kwargs': params.get('kwargs', {}),
                }
                path['route'] = reverse(path['name'], args=path['args'], kwargs=path['kwargs'])

                if getattr(settings, 'TEST_PRINT_URL', False):
                    print(path_name, params, path)

                checked_paths.add(path_name.split(':')[-1])
                response = self.client.get(path=path['route'], data=params.get('data', None), follow=params.get('follow', False))

                message = path_name
                if hasattr(response, 'redirect_chain') and response.redirect_chain:
                    message += 'redirect chain: ' + str(response.redirect_chain)

                # if response.status_code != 200:
                #     print('response.status_code', response.status_code)
                #
                #     if response.status_code == 302:
                #         print('redirecting to: ', response['Location'])

                if 'view' in params and 'follow' not in params:
                    view = params['view']
                    if hasattr(view, 'sorting_options'):
                        if isinstance(view.sorting_options, dict):
                            self.check_sorting_options(view, path, params)

                    if hasattr(view, 'displays'):
                        self.check_display_options(view, path, params)

                self.assertEqual(response.status_code, params.get('expected_status_code', 200), message)

                if 'expected_url' in params:
                    self.assertRedirects(response, expected_url=params['expected_url'])

        if all_tested_check:
            # check if all urls tested
            existing_paths = {path.name for path in urlpatterns}
            missing_paths = existing_paths - checked_paths
            self.assertEquals(len(missing_paths), 0, "Missing paths: {}".format(missing_paths))

    def check_sorting_options(self, view, path, params):
        for sorting, label in view.sorting_options.items():
            if 'data' not in params:
                params['data'] = {}

            params['data'].update({'sorting': sorting})
            response = self.client.get(path=path['route'], data=params.get('data', None), follow=params.get('follow', False))
            message = (str(path['name']), str(view))
            self.assertEqual(response.status_code, params.get('expected_status_code', 200), message)
            label = label[0] if isinstance(label, tuple) else label

            if 'current_sorting' in response.context:
                self.assertEqual(response.context['current_sorting'], label, message)

    def check_display_options(self, view, path, params):
        for display in view.displays:
            if 'data' not in params:
                params['data'] = {}

            params['data'].update({'display': display})
            response = self.client.get(path=path['route'], data=params.get('data', None), follow=params.get('follow', False))
            self.assertEqual(response.status_code, params.get('expected_status_code', 200))

            if hasattr(response, 'template_name'):
                template = response.template_name[-1] if isinstance(response.template_name, list) else response.template_name
                self.assertTrue(template.endswith(f'{display}.html'))

    def iterate_post_urls(self, url_params, data, delete_last=None, change_data=None):
        index = 0
        for path_name, params in url_params.items():
            params_list = params if isinstance(params, list) else [params]

            for params in params_list:
                path = {
                    'name': path_name,
                    'args': params.get('args', ()),
                    'kwargs': params.get('kwargs', {}),
                }
                path['route'] = reverse(path['name'], args=path['args'], kwargs=path['kwargs'])

                if getattr(settings, 'TEST_PRINT_URL', False):
                    print(path_name, params, path)

                form = params.get('form')

                if isclass(form):
                    form_kwargs = params.get('form_kwargs', {})

                    if change_data:
                        for field in change_data:
                            if isinstance(data[field], (datetime, date)):
                                data[field] += timedelta(days=index)
                            elif field == 'email':
                                data[field] = f'{time()}@example.com'
                            elif isinstance(data[field], str):
                                data[field] += str(index)
                            elif isinstance(data[field], int) and field =='month':
                                data[field] = (data[field] + index) % 12 + 1
                            else:
                                data[field] += index

                    form_kwargs['data'] = data
                    form = form(**form_kwargs)

                # change_data is not working with form instance
                elif change_data:
                    raise TypeError()

                if not isinstance(form, BaseFormSet):
                    # skip formset data  # TODO: improve
                    data_without_formset = {key: value for key, value in data.items() if not key.startswith('form-')}

                    # check if all fields are passed, if not pass problem fields to fail message
                    self.assertEqual(
                        data_without_formset.keys(),
                        form.fields.keys(),
                        (path_name, 'fields not matching:', set(form.fields.keys()).symmetric_difference(set(data_without_formset.keys())))
                    )

                # test if form is valid, if not pass form errors to fail message
                self.assertTrue(
                    form.is_valid(),
                    (path_name, 'form errors:', form.errors)
                )

                follow = params.get('follow', False if 'expected_status_code' in params else True)
                response = self.client.post(path=path['route'], data=form.data, follow=follow)

                message = path_name
                if hasattr(response, 'redirect_chain') and response.redirect_chain:
                    message += 'redirect chain: ' + str(response.redirect_chain)

                self.assertEqual(response.status_code, params.get('expected_status_code', 200), message)

                if 'expected_url' in params:
                    self.assertRedirects(response, expected_url=params['expected_url'])

                # deleting last created object, intended to order unique fields conflict
                if delete_last is not None and delete_last.objects.all().count() > 1 and hasattr(delete_last, 'created'):
                    delete_last.objects.order_by('created').last().delete()

                index += 1


class FilterTestMixin(object):
    def check_filter(self, filter_class, data, queryset='default', objs_to_find=[], **kwargs):
        queryset = filter_class._meta.model.objects.all() if queryset == 'default' else queryset
        if queryset is not None:
            kwargs['queryset'] = queryset

        # transform to multivalue dict
        for key, value in data.items():
            if not isinstance(value, list):
                data[key] = [value]

        data = MultiValueDict(data)
        filter = filter_class(data=data, **kwargs)

        filter_fields = set(filter.form.fields.keys())
        tested_fields = set(data.keys())
        missing_fields = filter_fields ^ tested_fields

        self.assertEqual(filter_fields, tested_fields)
        self.assertEqual(len(filter.errors), 0, f'Filter errors: {filter.errors}')

        qs = filter.qs.all()
        for obj in objs_to_find:
            self.assertIn(obj, qs)

    def iterate_filter_method(self, method, qs, obj, obj_attr, values={}, **kwargs):
        # values: dictionary with filter values as keys and corresponding attribute values as dict values
        # or list of values, which will be expanded to dict with above logic

        if not isinstance(values, dict):
            values = {x: x for x in values}

        for filter_val, attr_val in values.items():
            setattr(obj, obj_attr, attr_val)
            obj.save(update_fields=[obj_attr, ])

            self.check_filter_method(method, qs, values.keys(), obj, [filter_val, ], attr_val=attr_val, **kwargs)

    def check_filter_method(self, method, qs, filter_values=[], objs_to_find=[], values_when_find=[], objs_not_to_find=[], attr_val=None, **kwargs):
        # values: filter values to iterate over
        # obj_values: list of filter values for which objs should be found in filtered queryset

        if not isinstance(objs_to_find, list): # or objs_to_find != []:
            objs_to_find = [objs_to_find]

        if not isinstance(objs_not_to_find, list): # or objs_not_to_find != []:
            objs_not_to_find = [objs_not_to_find]

        for value in filter_values:
            filtered_qs = method(qs, value=value, **kwargs)

            # empty value shouldn't change queryset
            if value in ['']:
                self.assertEqual(qs, filtered_qs)

            if value in values_when_find:
                for obj in objs_to_find:
                    self.assertIn(obj, filtered_qs, f'filter value: {value}, object attribute value: {attr_val}')
                for obj in objs_not_to_find:
                    self.assertNotIn(obj, filtered_qs, value)
            else:
                for obj in objs_to_find:
                    self.assertNotIn(obj, filtered_qs, value)


class ManagerTestMixin(object):
    def check_manager(self, qs_or_manager, methods_with_params={}):
        # qs_or_manager can be instance or class
        checked_methods = set()
        manager_class = qs_or_manager if isclass(qs_or_manager) else qs_or_manager.__class__
        properties = {p for p in dir(manager_class) if isinstance(getattr(manager_class, p), property)}

        for method_name, params in methods_with_params.items():
            checked_methods.add(method_name)

            method = getattr(qs_or_manager, method_name)

            # if attribute is property continue
            if method_name in properties:
                continue

            # call method with params
            try:
                method(**params)
            except TypeError:
                method(params)

        # look for not tested methods
        existing_methods = {attr for attr in qs_or_manager.__class__.__dict__.keys()
                            if not attr.startswith('_')
                            and callable(getattr(qs_or_manager, attr))
                            and attr != 'mro'
                            and not isclass(getattr(qs_or_manager, attr))}

        missing_methods = existing_methods - checked_methods
        self.assertEqual(len(missing_methods), 0, "Missing methods: {}".format(missing_methods))

    def check_manager_method(self, method, exception=None, **kwargs):
        if exception is not None:
            with self.assertRaises(exception):
                method(**kwargs)


class PermissionTestMixin(object):
    USER_MODEL = User

    def setUp(self):
        super().setUp()
        self.logged_user = self.USER_MODEL.objects.create_user(first_name='permission user', email='permission_user@test.com', password='demodemo', is_active=True)
        self.client.login(email=self.logged_user.email, password='demodemo')

    def set_permissions(self, permissions, user=None):
        # permissions should be list of strings in format 'app_label.permission_codename'
        user = self.logged_user if not user else user
        user.user_permissions.set([])

        for permission in permissions:
            if permission == 'is_superuser':
                user.is_superuser = True
                user.save(update_fields=['is_superuser'])
            else:
                app_label, codename = permission.split('.')
                permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                user.user_permissions.add(permission)

    def check_queryset_permission(self, permission, test_obj, qs, method, method_kwargs):
        method = getattr(qs, method)

        self.set_permissions([])
        self.assertNotIn(test_obj, method(**method_kwargs))

        self.set_permissions([permission])
        self.logged_user = get_object_or_404(self.USER_MODEL, pk=self.logged_user.pk)
        self.assertIn(test_obj, method(**method_kwargs))

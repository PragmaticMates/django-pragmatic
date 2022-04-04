import ast
import functools
import importlib
import inspect
import os
import pkgutil
import random
import re
import traceback
from datetime import timedelta
from pprint import pformat, pprint

import sys
from collections import OrderedDict

from django import urls
from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as gis_models
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.geos import Point
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.postgres import fields as postgres_fields
from django.contrib.postgres import forms as postgres_forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import transaction
from django.db.models import NOT_PROVIDED, BooleanField, TextField, CharField, SlugField, EmailField, DateTimeField, \
    DateField, FileField, PositiveSmallIntegerField, DecimalField, IntegerField, QuerySet, PositiveIntegerField, \
    SmallIntegerField, BigIntegerField, FloatField, ImageField, GenericIPAddressField, JSONField, URLField
from django.db.models.fields.related import RelatedField, ManyToManyField, ForeignKey, OneToOneField
from django_filters import fields as django_filter_fields, FilterSet
from django.forms import fields as django_form_fields
from django.forms import models as django_form_models
from django.http import QueryDict
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import CreateView, UpdateView, DeleteView
from internationalflavor.countries import CountryField, CountryFormField
from internationalflavor.countries.data import UN_RECOGNIZED_COUNTRIES
from internationalflavor.vat_number import VATNumberField, VATNumberFormField


class GenericBaseMixin(object):
    # USER_MODEL = User
    objs = OrderedDict()
    TEST_PASSWORD = 'testpassword'
    RAISE_EVERY_TIME = False
    IGNORE_MODEL_FIELDS = []
    RUN_ONLY_THESE_URL_NAMES = []  # for debug purposes to save time
    IGNORE_URL_NAMES_CONTAINING = []
    POST_ONLY_URLS = []
    GET_ONLY_URLS = []

    def manual_model_dependency(self):
        '''
        for example required by model_field_values_map
        return {
            User: {Group}
        }
        '''

        return {}

    @property
    def model_field_values_map(self):
        '''{
            User: {
                'my_user': {
                    'username': lambda self: f'user.{GenericTestMixin.next_id(User)}@example.com',
                    'email': lambda self: f'user.{GenericTestMixin.next_id(User)}@example.com',
                    'password': 'testpassword',
                    'is_superuser': True,
                }
            },
        }
        '''
        return {}

    @property
    def user_model(self):
        try:
            return self.USER_MODEL
        except:
            return get_user_model()

    @property
    def default_field_map(self):
        # values can be callables with with field variable
        return {
            ForeignKey: lambda f: self.get_generated_obj(f.related_model),
            OneToOneField: lambda f: self.get_generated_obj(f.related_model),
            BooleanField: False,
            TextField: lambda f: '{}_{}'.format(f.model._meta.label_lower, f.name),
            CharField: lambda f: list(f.choices)[0][0] if f.choices else '{}_{}'.format(f.model._meta.label_lower, f.name)[:f.max_length],
            SlugField: lambda f: '{}_{}'.format(f.name, self.next_id(f.model)),
            EmailField: lambda f: '{}.{}@example.com'.format(f.model._meta.label_lower, self.next_id(f.model)),
            CountryField: 'LU',
            gis_models.PointField: Point(0.1276, 51.5072),
            VATNumberField: lambda f: 'LU{}'.format(random.randint(10000000, 99999999)),  # 'GB904447273',
            DateTimeField: now(),
            DateField: now().date(),
            postgres_fields.DateTimeRangeField: (now(), now() + timedelta(days=1)),
            postgres_fields.DateRangeField: (now().date(), now() + timedelta(days=1)),
            FileField: self.get_pdf_file_mock(),
            IntegerField: self.get_num_field_mock_value,
            PositiveSmallIntegerField: self.get_num_field_mock_value,
            DecimalField: self.get_num_field_mock_value,
            PositiveIntegerField: self.get_num_field_mock_value,
            SmallIntegerField: self.get_num_field_mock_value,
            BigIntegerField: self.get_num_field_mock_value,
            FloatField: self.get_num_field_mock_value,
            ImageField: self.get_image_file_mock(),
            GenericIPAddressField: '127.0.0.1',
            postgres_fields.JSONField: {},
            JSONField: {},
            URLField: lambda f: f'www.google.com',
        }

    @property
    def default_form_field_map(self):
        # values can be callables with with field variable
        return {
            django_form_fields.EmailField: lambda f: self.get_new_email(),
            django_form_fields.CharField: lambda f: '{}_{}'.format(f.label, random.randint(1, 999))[:f.max_length],
            django_form_fields.TypedChoiceField: lambda f: list(f.choices)[-1][0] if f.choices else '{}'.format(f.label)[:f.max_length],
            django_form_fields.ChoiceField: lambda f: list(f.choices)[-1][0] if f.choices else '{}'.format(f.label)[:f.max_length],
            CountryFormField: 'LU',  # random.choice(UN_RECOGNIZED_COUNTRIES),
            VATNumberFormField: lambda f: 'LU{}'.format(random.randint(10000000, 99999999)),  # 'GB904447273',
            django_form_fields.ImageField: self.get_image_file_mock(),
            django_form_fields.FileField: self.get_pdf_file_mock(),
            django_form_fields.DateTimeField: lambda f: now().strftime(list(f.input_formats)[-1]) if hasattr(f, 'input_formats') else now(),
            django_form_fields.DateField: now().date(),
            django_form_fields.IntegerField: lambda f: self.get_num_field_mock_value(f),
            django_form_fields.DecimalField: lambda f: self.get_num_field_mock_value(f),
            django_form_models.ModelMultipleChoiceField: lambda f: [f.queryset.first().id],
            django_form_models.ModelChoiceField: lambda f: f.queryset.first().id,
            django_form_fields.BooleanField: True,
            django_filter_fields.ModelChoiceField: lambda f: f.queryset.first().id,
            django_filter_fields.ChoiceField: lambda f: list(f.choices)[-1][0],
            django_form_fields.NullBooleanField: True,
            gis_forms.PointField: 'POINT (0.1276 51.5072)',
            django_form_fields.DurationField: 1,
            postgres_forms.SimpleArrayField: lambda f: [self.default_form_field_map[f.base_field.__class__](f.base_field)],
            django_form_fields.FloatField: lambda f: self.get_num_field_mock_value(f),
            django_form_fields.MultipleChoiceField: lambda f: [list(f.choices)[-1][0]] if f.choices else ['{}'.format(f.label)],
            django_form_fields.URLField: lambda f: f'www.google.com',
        }

    def import_modules_if_needed(self):
        module_names = self.get_submodule_names(self.CHECK_MODULES, self.CHECK_MODULES, self.EXCLUDE_MODULES)

        for module_name in module_names:
            try:
                if module_name not in sys.modules.keys():
                    importlib.import_module(module_name)
            except Exception as e:
                print('Failed to import module: {}'.format(module_name))
                raise e

    def get_source_code(self, modules, lines=True):
        module_names = sorted(self.get_submodule_names(self.CHECK_MODULES, modules, self.EXCLUDE_MODULES))

        if lines:
            return OrderedDict(
                ((module_name, inspect.getsourcelines(sys.modules[module_name])) for module_name in module_names))

        return OrderedDict(((module_name, inspect.getsource(sys.modules[module_name])) for module_name in module_names))

    @property
    def apps_to_check(self):
        return [app for app in apps.get_app_configs() if app.name.startswith(tuple(self.CHECK_MODULES))]

    def get_module_class_methods(self, module):
        # get classes defined in module, not imported
        classes = self.get_module_classes(module)
        methods = set()

        for cls in classes:
            methods |= {value for value in cls.__dict__.values() if callable(value)}

        return methods

    def get_module_classes(self, module):
        return {m[1] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__}

    def get_module_functions(self, module):
        return {m[1] for m in inspect.getmembers(module, inspect.isfunction) if m[1].__module__ == module.__name__}

    def get_submodule_names(self, parent_module_names, submodule_names, exclude_names=[]):
        # looks for submodules of parent_module containing submodule_name and not containing any of exclude_names,
        # which are not package (files, not dirs)
        module_names = set()

        if isinstance(parent_module_names, str):
            parent_module_names = [parent_module_names]

        if isinstance(submodule_names, str):
            submodule_names = [submodule_names]

        if isinstance(exclude_names, str):
            exclude_names = [exclude_names]

        for parent_module_name in parent_module_names:
            parent_module = sys.modules[parent_module_name]

            for importer, modname, ispkg in pkgutil.walk_packages(path=parent_module.__path__,
                                                                  prefix=parent_module.__name__ + '.',
                                                                  onerror=lambda x: None):

                for submodule_name in submodule_names:
                    if submodule_name in modname and not ispkg:
                        if not any([exclude_name in modname for exclude_name in exclude_names]):
                            module_names.add(modname)

        return (module_names)

    def parse_args(self, args, eval_args=True, eval_kwargs=True):
        args = 'f({})'.format(args)
        tree = ast.parse(args)
        funccall = tree.body[0].value
        if eval_args:
            args = [ast.literal_eval(arg) for arg in funccall.args if ast.unparse(arg) != '*args']
        else:
            args = [ast.unparse(arg) for arg in funccall.args if ast.unparse(arg) != '*args']

        if eval_kwargs:
            kwargs = {arg.arg: ast.literal_eval(arg.value) for arg in funccall.keywords if arg.arg is not None}
        else:
            kwargs = {arg.arg: ast.unparse(arg.value) for arg in funccall.keywords if arg.arg is not None}

        # if eval_args:
        #     args = [ast.literal_eval(arg) for arg in funccall.args if arg.id != '*args']
        # else:
        #     args = [arg.elts if isinstance(arg, ast.List) else arg.id for arg in funccall.args if isinstance(arg, ast.List) or ast.unparse(arg) != '*args']
        #
        # if eval_kwargs:
        #     kwargs = {arg.arg: ast.literal_eval(arg.value) for arg in funccall.keywords if arg.arg is not None}
        # else:
        #     kwargs = {arg.arg: arg.value.attr if isinstance(arg.value, ast.Attribute) else arg.value.s if isinstance(arg.value, ast.Str) else arg.value.id  for arg in funccall.keywords if arg.arg is not None}

        return args, kwargs

    def get_generated_email(self, model=None):
        if model is None:
            model = self.user_model

        return self.get_generated_obj(model).email

    def get_new_email(self):
        return 'email.{}@example.com'.format(random.randint(1, 999))

    def get_mock_request(self, **kwargs):
        request = RequestFactory().get('/')

        for key, value in kwargs.items():
            setattr(request, key, value)

        return request

    def generate_kwargs(self, args=[], kwargs={}, func=None, default={}):
        # maching kwarg names with
        # 1. model names and assigns generated objs acordingly,
        # 2. field names of instance.model if exists such that instance.func
        models = {model._meta.label_lower.split('.')[-1]: model for model in self.get_models()}
        result_kwargs = {}
        try:
            for name, value in kwargs.items():
                if name in default:
                    result_kwargs[name] = default[name]
                elif name == 'email':
                    result_kwargs[name] = self.get_generated_email()
                else:
                    matching_models = [model for model_name, model in models.items() if model_name == name]

                    if len(matching_models) == 1:
                        result_kwargs[name] = self.get_generated_obj(matching_models[0])
                    elif not func is None:
                        model = None

                        if hasattr(func, 'im_self') and hasattr(func.im_self, 'model'):
                            model = func.im_self.model

                        if not model is None:
                            try:
                                result_kwargs[name] = getattr(self.get_generated_obj(model), name)
                            except AttributeError:
                                pass

        except:
            raise
            kwargs = {}

        for arg in args:
            if arg in ['self', '*args', '**kwargs']:
                continue

            if arg in default:
                result_kwargs[arg] = default[arg]
            elif arg == 'email':
                result_kwargs[arg] = self.get_generated_email()
            else:
                matching_models = [model for name, model in models.items() if name == arg]

                if len(matching_models) == 1:
                    result_kwargs[arg] = self.get_generated_obj(matching_models[0])
                elif not func is None:
                    model = None

                    if hasattr(func, 'im_self') and hasattr(func.im_self, 'model'):
                        model = func.im_self.model

                    if not model is None:
                        try:
                            result_kwargs[arg] = getattr(self.get_generated_obj(model), arg)
                        except AttributeError:
                            pass

        return result_kwargs

    def generate_func_args(self, func, default={}):
        source = inspect.getsource(func)
        args = r'([^\)]*)'
        args = re.findall('def {}\({}\):'.format(func.__name__, args), source)
        args = [args[0].replace(' *,', '')] # dont really get why would someone use this but it happened
        return self.generate_kwargs(*self.parse_args(args[0], eval_args=False, eval_kwargs=False), func=func, default=default)

    def generate_form_data(self, form, default_data):
        data = {}

        for name, field in form.fields.items():
            if name in default_data:
                value = default_data[name]
                data[name] = value(self) if callable(value) else value
            else:
                value = self.default_form_field_map[field.__class__]
                data[name] = value(field) if callable(value) else value

        return data

    def get_url_namespace_map(self):
        resolver = urls.get_resolver(urls.get_urlconf())
        namespaces = {'': [key for key in resolver.reverse_dict.keys() if not callable(key)]}
        for key_1, resolver_1 in resolver.namespace_dict.items():
            namespaces[key_1] = [key for key in resolver_1[1].reverse_dict.keys() if not callable(key)]

            for key_2, resolver_2 in resolver_1[1].namespace_dict.items():
                namespaces['{}:{}'.format(key_1, key_2)] = [key for key in resolver_2[1].reverse_dict.keys() if not callable(key)]

                for key_3, resolver_3 in resolver_2[1].namespace_dict.items():
                    namespaces['{}:{}:{}'.format(key_1, key_2, key_3)] = [key for key in resolver_3[1].reverse_dict.keys() if
                                                              not callable(key)]

        return namespaces

    def get_url_namespaces(self):
        source_by_module = self.get_source_code(['urls'], lines=False)
        namespace_map = OrderedDict()

        for module_name, source_code in source_by_module.items():
            regex_paths = re.findall(r'app_name=["\']([\w_]+)["\'], ?namespace=["\']([\w_]+)["\']', source_code)
            namespace_map.update({})

    def get_url_views_by_module(self):
        source_by_module = self.get_source_code(['urls'], lines=False)
        paths_by_module = OrderedDict()

        skip_comments = r'([ \t]*#*[ \t]*)'
        pgettext_str = r'(?:pgettext_lazy\(["\']url["\'],)? ?'
        url_pattern_1 = r'["\'](.*)["\']'
        url_pattern_2 = r'r["\']\^(.*)\$["\']'
        url_pattern = '(?:{}|{})'.format(url_pattern_1, url_pattern_2)
        view_class = r'(\w+)'
        view_params = r'([^\)]*)'
        path_name = r'["\']([\w-]+)["\']'

        for module_name, source_code in source_by_module.items():
            regex_paths = re.findall(
                '{}(?:path|url)\({}{}\)?, ?{}.as_view\({}\), ?name={}'.format(skip_comments, pgettext_str, url_pattern, view_class, view_params, path_name),
                source_code)
            imported_classes = dict(inspect.getmembers(sys.modules[module_name], inspect.isclass))
            app_name = re.findall('app_name *= *\'(\w+)\'', source_code)

            if not app_name:
                app_name = [module_name.replace('.urls', '').split('.')[-1]]

            paths_by_module[module_name] = [{
                'app_name': app_name[0],
                'path_name': regex_path[5],
                'url_pattern': regex_path[1] if regex_path[1] else regex_path[2],
                'view_class': imported_classes.get(regex_path[3], None),
                'view_params': self.parse_args(regex_path[4], eval_args=False, eval_kwargs=False),
            } for regex_path in regex_paths if '#' not in regex_path[0]]

        return paths_by_module

    def get_apps_by_name(self, app_name=[]):
        if isinstance(app_name, str):
            app_name = [app_name]

        return [app for app in apps.get_app_configs() if app.name.startswith(tuple(app_name))]

    def get_models_from_app(self, app):
        if isinstance(app, str):
            apps = self.get_apps_by_name(app_name=app)

            if len(apps) > 1:
                raise ValueError('App name "{}" is ambiguous'.format(app))

            app = apps[0]

        return [model for model in app.get_models()]

    def get_models(self):
        models = [model for app in self.apps_to_check for model in app.get_models()]

        for module_name, module_params in self.get_url_views_by_module().items():
            for path_params in module_params:
                model = getattr(path_params['view_class'], 'model', None)
                if model and model not in models:
                    models.append(model)

        proxied_models = [model._meta.concrete_model for model in models if model._meta.proxy]
        proxied_apps = {apps.get_app_config(model._meta.app_label) for model in proxied_models}

        for app in proxied_apps:
            models.extend([model for model in app.get_models() if model not in models])

        return models

    def get_models_with_required_fields(self):
        return OrderedDict({
            model: [f for f in model._meta.get_fields() if
                    not getattr(f, 'blank', False) and f.concrete and not f.auto_created]
            for model in self.get_models()
        })

    def get_models_dependency(self, required_only=True):
        models = self.get_models()

        # find direct dependencies
        dependency = OrderedDict({
            model: {
                'required': {f.related_model for f in model._meta.get_fields()
                             if not getattr(f, 'blank', False) and isinstance(f,
                                                                              RelatedField) and f.concrete and not f.auto_created},
                'not_required': {} if required_only else {f.related_model for f in model._meta.get_fields()
                                                          if getattr(f, 'blank', False) and isinstance(f,
                                                                                                       RelatedField) and f.concrete and not f.auto_created},
            } for model in self.get_models()
        })

        missing_models = set()

        for model, relations in dependency.items():
            missing_models |= relations['required']

        missing_models -= set(dependency.keys())
        missing_models -= {ContentType}

        # add missing models
        dependency.update({
            model: {
                'required': {f.related_model for f in model._meta.get_fields()
                             if not getattr(f, 'blank', False) and isinstance(f,
                                                                              RelatedField) and f.concrete and not f.auto_created},
                'not_required': {} if required_only else {f.related_model for f in model._meta.get_fields()
                                                          if getattr(f, 'blank', False) and isinstance(f,
                                                                                                       RelatedField) and f.concrete and not f.auto_created},
            } for model in missing_models
        })

        # add manualy set dependencies
        for model, relations in self.manual_model_dependency().items():
            dependency[model]['required'] |= relations

        # add deeper level dependencies
        for i in range(2):
            # include 2nd and 3rd level dependencies, increase range to increase depth level
            for model in dependency.keys():
                for necesary_model in set(dependency[model]['required']):
                    if necesary_model in dependency.keys():
                        dependency[model]['required'] |= dependency[necesary_model]['required']

        return dependency

    def get_sorted_models_dependency(self, required_only=False, reverse=False):
        def compare_models_dependency(x, y):
            # less dependent first
            if x[0] in y[1]['required'] and y[0] in x[1]['required']:
                # circular required dependency should not happen
                raise ValueError('Circular dependency of models {}, {}'.format(x[0], y[0]))

            if x[0] in y[1]['required'] and y[0] not in x[1]['required']:
                # model y depends on x through required field, x < y
                return -1

            if x[0] not in y[1]['required'] and y[0] in x[1]['required']:
                # model x depends on y through required field, x > y
                return +1

            if x[0] in y[1]['not_required'] and y[0] not in x[1]['not_required']:
                # model y depends on x, x < y
                return -1

            if x[0] not in y[1]['not_required'] and y[0] in x[1]['not_required']:
                # model x depends on y, x > y
                return +1

            if len(x[1]['required']) < len(y[1]['required']):
                # model x doesnt require any model, y does
                return -1

            if len(x[1]['required']) > len(y[1]['required']):
                # model y doesnt require any model, x does
                return +1

            if len(x[1]['not_required']) < len(y[1]['not_required']):
                # model x  doesnt depend on any model, y does
                return -1

            if len(x[1]['not_required']) > len(y[1]['not_required']):
                # model y  doesnt depend on any model, x does
                return +1

            return 0

        sorted_models = sorted(self.get_models_dependency(required_only).items(), key=lambda x: x[0]._meta.label,
                               reverse=reverse)
        sorted_models = OrderedDict(
            sorted(sorted_models, key=functools.cmp_to_key(compare_models_dependency), reverse=reverse))
        return sorted_models

    def generate_objs(self):
        models_hierarchy = self.get_sorted_models_dependency(required_only=False)
        generated_objs = OrderedDict()
        models = models_hierarchy.keys()

        for model in models:
            if model._meta.proxy:
                continue

            generated_objs[model] = self.generate_model_objs(model)

        return generated_objs

    def delete_ojbs(self):
        models_hierarchy = self.get_sorted_models_dependency(required_only=False, reverse=True)

        for model in models_hierarchy.keys():
            model.objects.all().delete()

    def get_models_fields(self, model, required=None, related=None):
        is_required = lambda f: not getattr(f, 'blank', False) if required is True else getattr(f, 'blank', False) if required is False else True
        is_related = lambda f: isinstance(f, RelatedField) if related is True else not isinstance(f, RelatedField) if related is False else True
        # required = lambda f: not getattr(f, 'blank', False) if required_only else True
        # related = lambda f: isinstance(f, RelatedField) if related_only else True
        return [f for f in model._meta.get_fields() if is_required(f) and is_related(f) and f.concrete and not f.auto_created]

    def generate_model_field_values(self, model, field_values={}):
        not_related_fields = self.get_models_fields(model, related=False)
        related_fields = self.get_models_fields(model, related=True)
        m2m_values = {}

        for field in not_related_fields:
            if field.name not in self.IGNORE_MODEL_FIELDS and field.name not in field_values and (not isinstance(field, ManyToManyField)):
                field_value = field.default

                if inspect.isclass(field.default) and issubclass(field.default,
                                                                 NOT_PROVIDED) or field.default is None:
                    field_value = self.default_field_map.get(field.__class__, None)

                    if callable(field_value):
                        field_value = field_value(field)

                else:
                    if callable(field_value):
                        field_value = field_value()

                if field_value is None:
                    raise ValueError(
                        'Don\'t know ho to generate {}.{} value {}'.format(model._meta.label, field.name, field_value))

                field_values[field.name] = field_value

        for field in related_fields:
            if isinstance(field, ManyToManyField) and field.name in field_values:
                m2m_values[field.name] = field_values[field.name]
                del field_values[field.name]
            elif field.name not in self.IGNORE_MODEL_FIELDS and field.name not in field_values and (
            not isinstance(field, ManyToManyField)) and field.related_model.objects.exists():
                field_value = field.default

                if inspect.isclass(field.default) and issubclass(field.default,
                                                                 NOT_PROVIDED) or field.default is None:
                    field_value = self.default_field_map.get(field.__class__, None)

                    if callable(field_value):
                        field_value = field_value(field)

                else:
                    if callable(field_value):
                        field_value = field_value()

                if field_value is None:
                    raise ValueError(
                        'Don\'t know ho to generate {}.{} value {}'.format(model._meta.label, field.name, field_value))

                field_values[field.name] = field_value

        return field_values, m2m_values

    def generate_model_objs(self, model):
        # required_fields = self.get_models_fields(model, required_only=True)
        # related_fields = self.get_models_fields(model, related_only=True)
        model_obj_values_map = self.model_field_values_map.get(model, {model._meta.label_lower.replace('.', '_'): {}})
        new_objs = []

        for obj_name, obj_values in model_obj_values_map.items():
            obj = self.objs.get(obj_name, None)

            if obj:
                try:
                    obj.refresh_from_db()
                except model.DoesNotExist:
                    obj=None

            if not obj:
                field_values = obj_values(self) if callable(obj_values) else obj_values
                field_values, m2m_values = self.generate_model_field_values(model, field_values)

                if model == self.user_model:
                    if hasattr(self, 'create_user'):
                        obj = self.create_user(**field_values)
                    else:
                        obj = getattr(model._default_manager, 'create_user')(**field_values)
                else:

                    try:
                        with transaction.atomic():
                            obj = getattr(model._default_manager, 'create')(**field_values)
                    except Exception as e:
                        obj = model(**field_values)
                        obj.save()

                for m2m_attr, m2m_value in m2m_values.items():
                    getattr(obj, m2m_attr).set(m2m_value)

                new_objs.append(obj)
                self.objs[obj_name] = obj

        return new_objs


    def get_generated_obj(self, model, obj_name=None):
        if obj_name is None:
            if model._meta.proxy:
                model = model._meta.concrete_model

            if model in self.model_field_values_map.keys():
                obj_name = sorted(list(self.model_field_values_map[model].keys()))[0]

            if obj_name not in self.objs:
                obj_name = model._meta.label_lower.replace('.', '_')

        obj =  self.objs.get(obj_name, None)

        if obj:
            try:
                obj.refresh_from_db()
            except model.DoesNotExist:
                obj = None


        if not obj:
            self.generate_model_objs(model)
            obj = self.objs.get(obj_name, None)

        if not obj:
            raise Exception('Something\'s fucked')

        return obj
        # return self.objs.get(obj_name, model.objects.first())

    @classmethod
    def next_id(cls, model):
        return model.objects.order_by('id').last().id + 1 if model.objects.exists() else 0

    def get_pdf_file_mock(self, name='test.pdf'):
        file_path = os.path.join(os.path.dirname(__file__), 'blank.pdf')
        file = open(file_path, 'rb')
        file_mock = SimpleUploadedFile(
            name,
            file.read(),
            content_type='application/pdf'
        )
        return file_mock

    def get_image_file_mock(self, name='test.jpg', file_path=None):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(__file__), 'blank.jpg')
        file = open(file_path, 'rb')
        file_mock = SimpleUploadedFile(
            name,
            file.read(),
            content_type='image/png'
        )
        return file_mock

    def get_num_field_mock_value(self, field):
        if field.validators:
            if len(field.validators) == 2 \
                    and isinstance(field.validators[0], (MinValueValidator, MaxValueValidator)) \
                    and isinstance(field.validators[1], (MinValueValidator, MaxValueValidator)):
                # value = (field.validators[0].limit_value + field.validators[1].limit_value) / 2
                value = random.randint(*sorted([validator.limit_value for validator in field.validators]))
                if isinstance(field, IntegerField):
                    return int(value)

                return value

            validator = field.validators[0]

            if isinstance(validator, MinValueValidator):
                # return validator.limit_value + 1
                return random.randint(validator.limit_value, validator.limit_value + 9)

            if isinstance(validator, MaxValueValidator):
                # return validator.limit_value - 1
                return random.randint(1, validator.limit_value)

        return random.randint(1, 9)

    @property
    def url_params_map(self):
        '''{
            'accounts:user_list':{
                'params_1: {
                    'args': [],
                    'kwargs': {},
                    'data': {},
                    'form_kwargs': {},
                },
                'params_2': {} # passing empty dict behaves as if no params were specified, use to check also default behaviour besides specified params (params_1)
        }
        '''
        return {}

    @property
    def queryset_params_map(self):
        '''{
            'UserQuerySet: {
                'restrict_user': {},
            },
        }
        '''
        return {}

    @property
    def filter_params_map(self):
        '''{
            'UserFilterSet: {
                'init_kwargs': {},
                'data': {},
                'queryset': User.objects.all(), # optional
            },
        }
        '''
        return {}

    def init_form_kwargs(self, form_class, default={}):
        '''{
            UserForm: {'user': self.get_generated_obj(User)},
        }
        '''
        return {}.get(form_class, self.generate_func_args(form_class.__init__, default))

    def init_filter_kwargs(self, filter_class, default={}):
        return self.generate_func_args(filter_class.__init__, default=default)

    def setUp(self):
        super(GenericBaseMixin, self).setUp()
        self.import_modules_if_needed()
        self.generate_objs()
        user = self.objs.get('superuser', self.get_generated_obj(self.user_model))
        logged_in = self.client.login(email=user.email, username=user.username, password=self.TEST_PASSWORD)
        self.assertTrue(logged_in)
        self.user = user

    def tearDown(self):
        # self.delete_ojbs()
        super(GenericBaseMixin, self).tearDown()

    def print_last_fail(self, failed):
        for k, v in failed[-1].items():
            print(k)
            print(v)



class GenericTestMixin(object):
    '''
    Only containing generic tests
    eveything else, setup methods etc., is in GenericBaseMixin
    '''
    def test_urls(self):
        raise_every_time = self.RAISE_EVERY_TIME

        models = self.get_models()
        fields = [(f, model) for model in models for f in model._meta.get_fields() if f.concrete and not f.auto_created]
        failed = []
        tested = []
        for module_name, module_params in self.get_url_views_by_module().items():
            module_namespace = module_name.replace('.urls', '').split('.')[-1]

            for path_params in module_params:
                print(path_params)
                app_name = path_params['app_name']
                path_name = path_params['path_name']
                # path_namespace, path_name = path_params['path_name'].split(':')

                namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                              namespace.endswith(module_namespace) and path_name in namespace_path_names]

                if not namespaces:
                    namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                                  namespace.endswith(app_name) and path_name in namespace_path_names]

                if len(namespaces) != 1:
                    failed.append(OrderedDict({
                        'location': 'NAMESPACE',
                        'url name': path_params["path_name"],
                        'module': module_name,
                        'matching namespaces': namespaces,
                        'traceback': 'Namespace matching failed'
                    }))
                    if raise_every_time:
                        self.print_last_fail(failed)
                        raise
                    continue

                path_name = '{}:{}'.format(namespaces[0], path_name)

                if self.RUN_ONLY_THESE_URL_NAMES and path_name not in self.RUN_ONLY_THESE_URL_NAMES:
                    continue

                if path_name.endswith(tuple(self.IGNORE_URL_NAMES_CONTAINING)) or path_name.startswith(tuple(self.IGNORE_URL_NAMES_CONTAINING)):
                    continue

                tested.append(path_params)
                url_pattern = path_params["url_pattern"]
                args = re.findall(r'<([:\w]+)>', url_pattern)
                params_maps = self.url_params_map.get(path_name, {'default': {}})

                for map_name, params_map in params_maps.items():
                    parsed_args = params_map.get('args', [])
                    view_class = path_params['view_class']

                    if args and not parsed_args:
                        params_map['parsed'] = []
                        # parse args from path params
                        view_model = view_class.model if hasattr(view_class, 'model') else None

                        if view_model is None:
                            matching_models = [model for model in models if
                                               path_name.split(':')[-1].startswith(model._meta.label_lower.split(".")[-1])]

                            if len(matching_models) == 1:
                                view_model = matching_models[0]

                        for arg in args:
                            matching_fields = []

                            if arg in ['int:pk', 'pk']:
                                matching_fields = [('pk', view_model)]
                            else:
                                type, name = arg.split(':') if ':' in arg else ('int', arg)

                                if type not in ['int', 'str']:
                                    failed.append(OrderedDict({
                                        'location': 'URL ARG TYPE',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'arg': arg,
                                        'traceback': 'Cant handle this arg type'
                                    }))
                                    if raise_every_time:
                                        self.print_last_fail(failed)
                                        raise
                                    continue

                                if name.endswith('_pk'):
                                    matching_fields = [('pk', model) for model in models if
                                                       name == '{}_pk'.format(model._meta.label_lower.split(".")[-1])]
                                else:
                                    # full name and type match
                                    matching_fields = [(field, model) for field, model in fields if
                                                       field.name == name and isinstance(field,
                                                                                         IntegerField if type == 'int' else (CharField, BooleanField))]

                                    if len(matching_fields) > 1:
                                        # match field  model
                                        matching_fields = [(field, model) for field, model in matching_fields if
                                                           model == view_model]

                                    elif not matching_fields:
                                        # match name in form model_field to model and field
                                        matching_fields = [(field, model) for field, model in fields if
                                                           name == '{}_{}'.format(model._meta.label_lower.split(".")[-1], field.name)]

                                        if not matching_fields:
                                            # this might make problems as only partial match is made
                                            matching_fields = [(p[0], view_model) for p in
                                                               inspect.getmembers(view_model,
                                                                                  lambda o: isinstance(o, property)) if
                                                               p[0].startswith(name)]

                            if len(matching_fields) != 1 or matching_fields[0][1] is None:
                                failed.append(OrderedDict({
                                    'location': 'URL ARG MATCH',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'arg': arg,
                                    'matching fields': matching_fields,
                                    'traceback': 'Url arg mathcing failed'
                                }))
                                if raise_every_time:
                                    self.print_last_fail(failed)
                                    raise
                                continue

                            attr_name, model = matching_fields[0]

                            if not isinstance(attr_name, str):
                                # its Field object
                                attr_name = attr_name.name

                            obj = self.get_generated_obj(model)

                            if obj is None:
                                obj = self.generate_model_objs(model)

                            obj = self.get_generated_obj(model)
                            arg_value = getattr(obj, attr_name, None)

                            if arg_value in [True, False]:
                                arg_value = str(arg_value)

                            if arg_value is None:
                                failed.append(OrderedDict({
                                    'location': 'URL ARG PARSE',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'arg': arg,
                                    'parsed arg': arg_value,
                                    'traceback': 'Url arg parsing failed'
                                }))
                                if raise_every_time:
                                    self.print_last_fail(failed)
                                    raise
                                continue

                            parsed_args.append(arg_value)
                            params_map['parsed'].append({'obj': obj, 'attr_name': attr_name, 'value': arg_value})

                    if len(args) != len(parsed_args):
                        failed.append(OrderedDict({
                            'location': 'URL ARGS PARSED',
                            'url name': path_name,
                            'url': path,
                            'url pattern': url_pattern,
                            'args': args,
                            'parsed args': parsed_args,
                            'traceback': 'Url args parsing failed'
                        }))
                        if raise_every_time:
                            self.print_last_fail(failed)
                            raise
                        continue

                    path = reverse(path_name, args=parsed_args)
                    data = params_map.get('data', {})
                    kwargs = params_map.get('kwargs', {})

                    if kwargs:
                        kwargs = '&'.join([f'{key}={value}' for key, value in kwargs.items()])
                        path = f'{path}?{kwargs}'

                    # GET url
                    if not path_name in self.POST_ONLY_URLS:
                        try:
                            get_response = self.client.get(path=path, data=data, follow=True)
                            self.assertEqual(get_response.status_code, 200)
                        except Exception as e:
                            failed.append(OrderedDict({
                                'location': 'GET',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'view class': view_class,
                                'traceback': traceback.format_exc()
                            }))
                            if raise_every_time:
                                self.print_last_fail(failed)
                                raise
                            continue

                        if hasattr(view_class, 'sorting_options'):  # and isinstance(view_class.sorting_options, dict):
                            for sorting, label in view_class.sorting_options.items():
                                data['sorting'] = sorting

                                try:
                                    response = self.client.get(path=path, data=data, follow=True)
                                    self.assertEqual(response.status_code, 200)
                                except Exception as e:
                                    failed.append(OrderedDict({
                                        'location': 'SORTING',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'parsed args': parsed_args,
                                        'data': data,
                                        'traceback': traceback.format_exc()
                                    }))
                                    if raise_every_time:
                                        self.print_last_fail(failed)
                                        raise


                        if hasattr(view_class, 'displays'):
                            # self.check_display_options(view, path, params)
                            for display in view_class.displays:
                                data['display'] = display

                                try:
                                    response = self.client.get(path=path, data=data, follow=True)
                                    self.assertEqual(response.status_code, 200)
                                except Exception as e:
                                    failed.append(OrderedDict({
                                        'location': 'DISPLAY',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'parsed args': parsed_args,
                                        'data': data,
                                        'traceback': traceback.format_exc()
                                    }))
                                    if raise_every_time:
                                        self.print_last_fail(failed)
                                        raise
                                else:
                                    if hasattr(response, 'template_name'):
                                        template = response.template_name[-1] if isinstance(response.template_name,
                                                                                            list) else response.template_name

                                        try:
                                            self.assertTrue(template.endswith('{}.html'.format(display)))
                                        except Exception as e:
                                            failed.append(OrderedDict({
                                                'location': 'TEMPLATE',
                                                'url name': path_name,
                                                'url': path,
                                                'url pattern': url_pattern,
                                                'parsed args': parsed_args,
                                                'data': data,
                                                'template': template,
                                                'traceback': traceback.format_exc()
                                            }))
                                            if raise_every_time:
                                                self.print_last_fail(failed)
                                                raise

                    # POST url
                    if path_name not in self.GET_ONLY_URLS and getattr(view_class, 'form_class', None):
                        form_class = view_class.form_class
                        form_kwargs = params_map.get('form_kwargs', self.generate_func_args(form_class.__init__))
                        form_kwargs = {key: value(self) if callable(value) else value for key,value in form_kwargs.items()}
                        form_kwargs['data'] = data
                        init_form_kwargs = self.init_form_kwargs(form_class)
                        form = None

                        try:
                            form = form_class(**init_form_kwargs)
                        except Exception as e:
                            if not isinstance(form, form_class) or not hasattr(form, 'fields'):
                                # as long as there is form instance with fields its enough to generate data
                                failed.append(OrderedDict({
                                    'location': 'POST FORM INIT',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'parsed args': parsed_args,
                                    'form class': form_class,
                                    'form kwargs': init_form_kwargs,
                                    'traceback': traceback.format_exc()
                                }))
                                if raise_every_time:
                                    self.print_last_fail(failed)
                                    raise
                                continue

                        query_dict_data = QueryDict('', mutable=True)

                        try:
                            query_dict_data.update(self.generate_form_data(form, data))
                        except Exception as e:
                            failed.append(OrderedDict({
                                'location': 'POST GENERATING FORM DATA',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'form class': form_class,
                                'default form data': data,
                                'traceback': traceback.format_exc()
                            }))

                            if raise_every_time:
                                self.print_last_fail(failed)
                                raise
                            continue

                        form_kwargs['data'] = query_dict_data
                        obj_count_before = 0

                        if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
                            obj_count_before = view_class.model.objects.all().count()

                        try:
                            response = self.client.post(path=path, data=form_kwargs['data'], follow=True)
                            self.assertEqual(response.status_code, 200)
                        except ValidationError as e:
                            if e.message == 'ManagementForm data is missing or has been tampered with':
                                post_data = None

                                try:
                                    post_data = self.create_formset_post_data(get_response, form_kwargs['data'], form_kwargs.get('formset_data', []))
                                    response = self.client.post(path=path, data=post_data, follow=True)
                                    self.assertEqual(response.status_code, 200)
                                except Exception as e:
                                    failed.append(OrderedDict({
                                        'location': 'POST FORMSET',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'parsed args': parsed_args,
                                        'form class': form_class,
                                        'data': form_kwargs['data'],
                                        'post data': post_data,
                                        'form': form,
                                        'traceback': traceback.format_exc()
                                    }))
                                    if raise_every_time:
                                        self.print_last_fail(failed)
                                        raise
                                    continue
                            else:
                                raise
                        except Exception as e:
                            failed.append(OrderedDict({
                                'location': 'POST',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'form class': form_class,
                                'data': form_kwargs['data'],
                                'form': form,
                                'traceback': traceback.format_exc()
                            }))
                            if raise_every_time:
                                self.print_last_fail(failed)
                                raise
                            continue



                        if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
                            obj_count_after = view_class.model.objects.all().count()

                            try:
                                if issubclass(view_class, CreateView):
                                    self.assertEqual(obj_count_after, obj_count_before + 1)
                                elif issubclass(view_class, UpdateView):
                                    self.assertEqual(obj_count_after, obj_count_before)
                                elif issubclass(view_class, DeleteView):
                                    self.assertEqual(obj_count_after, obj_count_before - 1)
                                    # recreate obj
                                    self.generate_model_objs(view_class.model)

                            except Exception as e:
                                # for key, value in init_form_kwargs.items():
                                #     if key not in form_kwargs:
                                #         form_kwargs[key] = value

                                # form = form_class(**form_kwargs)
                                form = response.context_data.get('form', None)

                                failed.append(OrderedDict({
                                    'location': 'POST COUNT',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'parsed args': parsed_args,
                                    'view model': view_class.model,
                                    'form class': form_class,
                                    # 'form': form,
                                    'form valid': form.is_valid() if form else None,
                                    'form errors': form.errors if form else None,
                                    'data': form_kwargs['data'],
                                    'traceback': traceback.format_exc()
                                }))
                                if raise_every_time:
                                    self.print_last_fail(failed)
                                    raise

        if failed:
            # append failed count at the end of error list
            failed.append('{}/{} urls FAILED'.format(len(failed), len(tested)))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

    def test_querysets(self):
        models_querysets = [model.objects.all() for model in self.get_models()]
        failed = []

        for qs in models_querysets:
            qs_class = qs.__class__

            if not qs_class == QuerySet:
                qs_class_label = qs_class.__name__
                queryset_methods = [(name, func) for name, func in qs_class.__dict__.items()
                                    if not name.startswith('_')
                                    and name != 'mro'
                                    and inspect.isfunction(func)]

                params_map = self.queryset_params_map.get(qs_class, {})

                for name, func in queryset_methods:
                    print('{}.{}'.format(qs_class_label, name))
                    result = None
                    kwargs = {}

                    if name in params_map:
                        # provided arguments
                        kwargs = params_map[name]

                        try:
                            result = getattr(qs, name)(**kwargs)
                        except Exception as e:
                            failed.append([{
                                'location': 'DEFAULT KWARGS',
                                'queryset method': '{}.{}'.format(qs_class_label, name),
                                'kwargs': kwargs,
                                'traceback': traceback.format_exc(),
                            }])
                    elif func.__code__.co_argcount == 1:
                        # no arguments except self
                        try:
                            result = getattr(qs, name)()
                        except Exception as e:
                            failed.append([{
                                'location': 'NO KWARGS',
                                'queryset method': '{}.{}'.format(qs_class_label, name),
                                'traceback': traceback.format_exc(),
                            }])
                    else:
                        func = getattr(qs, name)

                        try:
                            kwargs = self.generate_func_args(func)
                        except Exception as e:
                            failed.append([{
                                'location': 'GENERATING KWARGS',
                                'queryset method': '{}.{}'.format(qs_class_label, name),
                                'traceback': traceback.format_exc(),
                            }])
                        else:
                            try:
                                result = getattr(qs, name)(**kwargs)
                            except Exception as e:
                                failed.append([{
                                    'location': 'GENERATED KWARGS',
                                    'queryset method': '{}.{}'.format(qs_class_label, name),
                                    'kwargs': kwargs,
                                    'traceback': traceback.format_exc(),
                                }])

        if failed:
            failed.append('{} qeuryset methods FAILED'.format(len(failed)))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

    def test_filters(self):
        raise_every_time = self.RAISE_EVERY_TIME

        module_names = self.get_submodule_names(self.CHECK_MODULES, ['filters', 'forms'], self.EXCLUDE_MODULES)
        filter_classes = set()
        failed = []

        # get filter classes
        for module_name in module_names:
            module = sys.modules[module_name]

            filter_classes |= {
                cls for cls in self.get_module_classes(module) if issubclass(cls, (FilterSet,))
            }

        filter_classes = sorted(filter_classes, key=lambda x: x.__name__)

        for i, filter_class in enumerate(filter_classes):
            print(filter_class)
            params_map = self.filter_params_map.get(filter_class, {})
            init_kwargs = self.init_filter_kwargs(filter_class, default=params_map.get('init_kwargs', {}))

            try:
                filter = filter_class(**init_kwargs)
            except:
                failed.append(OrderedDict({
                    'location': 'FILTER INIT',
                    'filter class': filter_class,
                    'init_kwargs': init_kwargs,
                    'params map': params_map,
                    'traceback': traceback.format_exc()
                }))
                if raise_every_time:
                    self.print_last_fail(failed)
                    raise
                continue

            query_dict_data = QueryDict('', mutable=True)

            try:
                query_dict_data.update(self.generate_form_data(filter.form, params_map.get('data', {})))
            except:
                failed.append(OrderedDict({
                    'location': 'FILTER DATA',
                    'filter class': filter_class,
                    'data': query_dict_data,
                    'params map': params_map,
                    'traceback': traceback.format_exc()
                }))
                if raise_every_time:
                    self.print_last_fail(failed)
                    raise
                continue

            try:
                queryset = params_map.get('queryset', filter_class._meta.model.objects.all())
            except Exception as e:
                failed.append(OrderedDict({
                    'location': 'FILTER QUERYSET',
                    'filter class': filter_class,
                    'params map': params_map,
                    'traceback': traceback.format_exc()
                }))
                if raise_every_time:
                    self.print_last_fail(failed)
                    raise
                continue

            try:
                filter = filter_class(data=query_dict_data, queryset=queryset, **init_kwargs)
                qs = filter.qs.all().values()
            except Exception as e:
                failed.append(OrderedDict({
                    'location': 'FILTER',
                    'filter class': filter_class,
                    'data': query_dict_data,
                    'params map': params_map,
                    'traceback': traceback.format_exc()
                }))
                if raise_every_time:
                    self.print_last_fail(failed)
                    raise
                continue

        if failed:
            failed.append('{} filters FAILED'.format(len(failed)))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

import ast
import functools
import importlib
import inspect
import itertools
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
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as gis_models
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.geos import Point, MultiPoint
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.postgres import fields as postgres_fields
from django.contrib.postgres import forms as postgres_forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import transaction, IntegrityError
from django.db.models import NOT_PROVIDED, BooleanField, TextField, CharField, SlugField, EmailField, DateTimeField, \
    DateField, FileField, PositiveSmallIntegerField, DecimalField, IntegerField, QuerySet, PositiveIntegerField, \
    SmallIntegerField, BigIntegerField, FloatField, ImageField, GenericIPAddressField, JSONField, URLField
from django.db.models.fields.related import RelatedField, ManyToManyField, ForeignKey, OneToOneField
from django_filters import fields as django_filter_fields, FilterSet
from django.forms import fields as django_form_fields
from django.forms import models as django_form_models
from django.http import QueryDict
from django.test import RequestFactory
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from internationalflavor import iban as if_iban
from internationalflavor import vat_number as if_vat
from internationalflavor import countries as if_countries

from pragmatic import fields as pragmatic_fields

if 'gm2m' in getattr(settings, 'INSTALLED_APPS'):
    from gm2m import GM2MField


class GenericBaseMixin(object):
    # USER_MODEL = User # there is possibility to manualy specify user model to be used, see user_model()
    objs = OrderedDict()
    TEST_PASSWORD = 'testpassword'
    IGNORE_MODEL_FIELDS = {}    # values for these model fields will not be generated, use for fields with automatically assigned values, for example {MPTTModel: ['lft', 'rght', 'tree_id', 'level']}

    # params for GenericTestMixin.test_urls
    RUN_ONLY_THESE_URL_NAMES = []  # if not empty will run tests only for provided urls, for debug purposes to save time
    RUN_URL_NAMES_CONTAINING = []  # if not empty will run tests only for urls containing at least one of provided patterns
    IGNORE_URL_NAMES_CONTAINING = []    # contained urls will not be tested
    POST_ONLY_URLS = [] # run only post request tests for these urls
    GET_ONLY_URLS = []  # run only get request tests for these urls

    @classmethod
    def manual_model_dependency(cls):
        '''
        Use to manually specify model dependency which are not accounted for by default (check get_sorted_models_dependency output),
        for example if generating objs with provided m2m values, or otherwise required in model_field_values_map
        return {
            User: {Group}
        }
        '''

        return {}

    @classmethod
    def model_field_values_map(cls):
        '''
        Enables generate objects with specific values, for example for User model:

        {
            User: {
                'user_1': lambda cls: {
                    'username': f'user.{cls.next_id(User)}@example.com',
                    'email': f'user.{cls.next_id(User)}@example.com',
                    'password': 'testpassword',
                    'is_superuser': True,
                },
                'user_2': lambda cls: {
                    'username': f'user.{cls.next_id(User)}@example.com',
                    'email': f'user.{cls.next_id(User)}@example.com',
                    'password': 'testpassword',
                    'is_superuser': False,
                }
            },
        }
        '''
        return {}

    @classmethod
    def user_model(cls):
        '''
        User model used for login and permissions
        '''
        try:
            return cls.USER_MODEL
        except:
            return get_user_model()

    @classmethod
    def default_field_name_map(cls):
        '''
        field values by field name used to generate objects, this has priority before default_field_map,
        values can be callables with field variable, extend in subclass as needed
        '''
        return {
            'year': now().year,
            'month': now().month,
        }

    @classmethod
    def default_field_map(cls):
        '''
        field values by field class used to generate objects, values can be callables with field variable,
        extend in subclass as needed
        '''
        return {
            ForeignKey: lambda f: cls.get_generated_obj(f.related_model),
            OneToOneField: lambda f: cls.get_generated_obj(f.related_model),
            BooleanField: False,
            TextField: lambda f: '{}_{}'.format(f.model._meta.label_lower, f.name),
            CharField: lambda f: list(f.choices)[0][0] if f.choices else '{}'.format(f.name)[:f.max_length],
            SlugField: lambda f: '{}_{}'.format(f.name, cls.next_id(f.model)),
            EmailField: lambda f: '{}.{}@example.com'.format(f.model._meta.label_lower, cls.next_id(f.model)),
            gis_models.PointField: Point(0.1276, 51.5072),
            gis_models.MultiPointField: MultiPoint(Point(0.1276, 51.5072), Point(0.1276, 51.5072)),
            DateTimeField: lambda f: now(),
            DateField: lambda f: now().date(),
            postgres_fields.DateTimeRangeField: (now(), now() + timedelta(days=1)),
            postgres_fields.DateRangeField: (now().date(), now() + timedelta(days=1)),
            FileField: lambda f: cls.get_pdf_file_mock(),
            IntegerField: lambda f: cls.get_num_field_mock_value(f),
            PositiveSmallIntegerField: lambda f: cls.get_num_field_mock_value(f),
            DecimalField: lambda f: cls.get_num_field_mock_value(f),
            PositiveIntegerField: lambda f: cls.get_num_field_mock_value(f),
            SmallIntegerField: lambda f: cls.get_num_field_mock_value(f),
            BigIntegerField: lambda f: cls.get_num_field_mock_value(f),
            FloatField: lambda f: cls.get_num_field_mock_value(f),
            ImageField: lambda f: cls.get_image_file_mock(),
            GenericIPAddressField: '127.0.0.1',
            postgres_fields.JSONField: {},
            postgres_fields.ArrayField: lambda f: [cls.default_field_map()[f.base_field.__class__](f.base_field)],
            JSONField: {},
            URLField: lambda f: f'www.google.com',
            if_countries.CountryField: 'LU',
            if_iban.IBANField: 'LU28 0019 4006 4475 0000',
            if_vat.VATNumberField: lambda f: 'LU{}'.format(random.randint(10000000, 99999999)),  # 'GB904447273',
        }

    @classmethod
    def default_form_field_map(cls):
        '''
        field values by form field class used to generate form values, values can be callables with field variable,
        extend in subclass as needed
        '''
        return {
            django_filter_fields.ModelChoiceField: lambda f: f.queryset.first().id,
            django_filter_fields.ModelMultipleChoiceField: lambda f: f.queryset.first().id,
            django_filter_fields.MultipleChoiceField: lambda f: [list(f.choices)[-1][0]] if f.choices else ['{}'.format(f.label)],
            django_filter_fields.ChoiceField: lambda f: list(f.choices)[-1][0],
            django_filter_fields.RangeField: lambda f: [1, 100],
            django_filter_fields.DateRangeField: lambda f: (now().date(), now() + timedelta(days=1)),
            django_form_fields.EmailField: lambda f: cls.get_new_email(),
            django_form_fields.CharField: lambda f: '{}_{}'.format(f.label, random.randint(1, 999))[:f.max_length],
            django_form_fields.TypedChoiceField: lambda f: list(f.choices)[-1][1][0][0] if f.choices and isinstance(list(f.choices)[-1][1], list) else list(f.choices)[-1][0] if f.choices else '{}'.format(f.label)[:f.max_length],
            django_form_fields.ChoiceField: lambda f: list(f.choices)[-1][1][0][0] if f.choices and isinstance(list(f.choices)[-1][1], list) else list(f.choices)[-1][0] if f.choices else '{}'.format(f.label)[:f.max_length],
            django_form_fields.ImageField: lambda f: cls.get_image_file_mock(),
            django_form_fields.FileField: lambda f: cls.get_pdf_file_mock(),
            django_form_fields.DateTimeField: lambda f: now().strftime(list(f.input_formats)[-1]) if hasattr(f, 'input_formats') else now(),
            django_form_fields.DateField: now().date(),
            django_form_fields.IntegerField: lambda f: cls.get_num_field_mock_value(f),
            django_form_fields.DecimalField: lambda f: cls.get_num_field_mock_value(f),
            django_form_models.ModelMultipleChoiceField: lambda f: [f.queryset.first().id],
            django_form_models.ModelChoiceField: lambda f: f.queryset.first().id,
            django_form_fields.BooleanField: True,
            django_form_fields.NullBooleanField: True,
            django_form_fields.MultipleChoiceField: lambda f: [list(f.choices)[-1][0]] if f.choices else ['{}'.format(f.label)],
            django_form_fields.URLField: lambda f: f'www.google.com',
            django_form_fields.DurationField: 1,
            django_form_fields.JSONField: '',
            django_form_fields.SplitDateTimeField: lambda f: [now().date(), now().time()],
            django_form_fields.GenericIPAddressField: '127.0.0.1',
            django_form_fields.FloatField: lambda f: cls.get_num_field_mock_value(f),
            gis_forms.PointField: 'POINT (0.1276 51.5072)',
            postgres_forms.HStoreField: '',
            postgres_forms.SimpleArrayField: lambda f: [cls.default_form_field_map()[f.base_field.__class__](f.base_field)],
            postgres_forms.DateTimeRangeField: lambda f: [now().strftime(list(f.input_formats)[-1]) if hasattr(f, 'input_formats') else now(), now().strftime(list(f.input_formats)[-1]) if hasattr(f, 'input_formats') else now()],
            pragmatic_fields.AlwaysValidChoiceField: lambda f: list(f.choices)[-1][0] if f.choices else '{}'.format(f.label),
            pragmatic_fields.AlwaysValidMultipleChoiceField: lambda f: f'{list(f.choices)[-1][0]}' if f.choices else '{}'.format(f.label),
            pragmatic_fields.SliderField: lambda f: f'{f.min},{f.max}' if f.has_range else f'{f.min}',
            if_countries.CountryFormField: 'LU',  # random.choice(UN_RECOGNIZED_COUNTRIES),
            if_iban.IBANFormField: 'LU28 0019 4006 4475 0000',
            if_vat.VATNumberFormField: lambda f: 'LU{}'.format(random.randint(10000000, 99999999)),  # 'GB904447273',
        }

    @classmethod
    def import_modules_if_needed(cls):
        '''
        import all modules encountered if some where not yet imported, for example when searching for models dependency or urls in source code
        '''
        module_names = cls.get_submodule_names(cls.CHECK_MODULES, cls.CHECK_MODULES, cls.EXCLUDE_MODULES)

        for module_name in module_names:
            try:
                if module_name not in sys.modules.keys():
                    importlib.import_module(module_name)
            except Exception as e:
                print('Failed to import module: {}'.format(module_name))
                raise e

    @classmethod
    def get_source_code(cls, modules, lines=True):
        module_names = sorted(cls.get_submodule_names(cls.CHECK_MODULES, modules, cls.EXCLUDE_MODULES))

        if lines:
            return OrderedDict(
                ((module_name, inspect.getsourcelines(sys.modules[module_name])) for module_name in module_names))

        return OrderedDict(((module_name, inspect.getsource(sys.modules[module_name])) for module_name in module_names))

    @classmethod
    def apps_to_check(cls):
        '''
        return all the apps to to be tested, or used to look for models dependency
        '''
        return [app for app in apps.get_app_configs() if app.name.startswith(tuple(cls.CHECK_MODULES))]

    @classmethod
    def get_module_class_methods(cls, module):
        classes = cls.get_module_classes(module)    # get not imported classes defined in module
        methods = set()

        for cls in classes:
            methods |= {value for value in cls.__dict__.values() if callable(value)}

        return methods

    @classmethod
    def get_module_classes(cls, module):
        '''
        returns only not imported classes defined in module
        '''
        return {m[1] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == module.__name__}

    @classmethod
    def get_module_functions(cls, module):
        '''
        returns only not imported functions defined in module
        '''
        return {m[1] for m in inspect.getmembers(module, inspect.isfunction) if m[1].__module__ == module.__name__}

    @classmethod
    def get_submodule_names(cls, parent_module_names, submodule_names, exclude_names=[]):
        '''
        looks for submodules of parent_module containing submodule_name and not containing any of exclude_names,
        which are not package (files, not dirs)
        '''
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

    @classmethod
    def parse_args(cls, args, eval_args=True, eval_kwargs=True):
        '''
        parsing args and kwargs as specified
        '''
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

    @classmethod
    def get_generated_email(cls, model=None):
        '''
        shortuct to get genrated email
        '''
        if model is None:
            model = cls.user_model()

        return cls.get_generated_obj(model).email

    @classmethod
    def get_new_email(cls):
        return 'email.{}@example.com'.format(random.randint(1, 999))

    @classmethod
    def get_mock_request(cls, **kwargs):
        return cls.get_request('/', **kwargs)

    @classmethod
    def get_request(cls, path='/', **kwargs):
        request = RequestFactory().get(path)

        for key, value in kwargs.items():
            setattr(request, key, value)

        return request

    @classmethod
    def get_response(cls, **kwargs):
        # return view_class.as_view(**view_kwargs)(request) response for request=RequestFactory.get() with additional request_attributes
        path = kwargs.get('path', '/')
        view_class = kwargs.get('view_class', None)
        view_kwargs = kwargs.get('view_kwargs', {})
        request_kwargs = kwargs.get('request_atrributes', {})

        if view_class is None:
            # get from urls.py
            raise ValueError('view_class not specified')

        request = cls.get_request(path, **request_kwargs)
        return view_class.as_view(**view_kwargs)(request)

    @classmethod
    def get_response_view(cls, **kwargs):
        response = cls.get_response(**kwargs)
        return response.context_data['view']

    @classmethod
    def get_response_view_as_filter_function(cls, **kwargs):
        # returns function for specific response view as function of filter kwargs in url,
        def filter_function(**filter_kargs):
            kwargs['path'] = kwargs.get('path', '/') + '?' + '&'.join([f'{key}={value}' for key, value in filter_kargs.items()])
            return cls.get_response_view(**kwargs)

        return filter_function

    @classmethod
    def generate_kwargs(cls, args=[], kwargs={}, func=None, default={}):
        # maching kwarg names with
        # 1. model names and assigns generated objs acordingly,
        # 2. field names of instance.model if exists such that instance.func
        models = {model._meta.label_lower.split('.')[-1]: model for model in cls.get_models()}
        result_kwargs = {**default}

        try:
            for name, value in kwargs.items():
                if name in default:
                    # result_kwargs[name] = default[name]
                    pass
                elif name == 'email':
                    result_kwargs[name] = cls.get_generated_email()
                else:
                    matching_models = [model for model_name, model in models.items() if model_name == name]

                    if len(matching_models) == 1:
                        result_kwargs[name] = cls.get_generated_obj(matching_models[0])
                    elif not func is None:
                        model = None

                        if hasattr(func, 'im_self') and hasattr(func.im_self, 'model'):
                            model = func.im_self.model

                        if not model is None:
                            try:
                                result_kwargs[name] = getattr(cls.get_generated_obj(model), name)
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
                result_kwargs[arg] = cls.get_generated_email()
            else:
                matching_models = [model for name, model in models.items() if name == arg]

                if len(matching_models) == 1:
                    result_kwargs[arg] = cls.get_generated_obj(matching_models[0])
                elif not func is None:
                    model = None

                    if hasattr(func, 'im_self') and hasattr(func.im_self, 'model'):
                        model = func.im_self.model

                    if not model is None:
                        try:
                            result_kwargs[arg] = getattr(cls.get_generated_obj(model), arg)
                        except AttributeError:
                            pass

        return result_kwargs

    @classmethod
    def generate_func_args(cls, func, default={}):
        source = inspect.getsource(func)
        args = r'([^\)]*)'
        args = re.findall('def {}\({}\):'.format(func.__name__, args), source)
        args = [args[0].replace(' *,', '')] # dont really get why would someone use this but it happened
        return cls.generate_kwargs(*cls.parse_args(args[0], eval_args=False, eval_kwargs=False), func=func, default=default)

    @classmethod
    def generate_form_data(cls, form, default_data):
        if inspect.isclass(form):
            # if class is passed try to get instance
            form = form(**cls.init_form_kwargs(form, {}))

        data = {}

        for name, field in default_data.items():
            value = default_data[name]
            data[name] = value(cls) if callable(value) else value

        for name, field in form.fields.items():
            if name not in data and not isinstance(field, django_form_models.InlineForeignKeyField): # inline fk is is sued in inline formsets
                value = cls.default_form_field_map()[field.__class__]
                data[name] = value(field) if callable(value) else value

        return data

    @classmethod
    def get_url_namespace_map(cls):
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

    @classmethod
    def get_url_namespaces(cls):
        source_by_module = cls.get_source_code(['urls'], lines=False)
        namespace_map = OrderedDict()

        for module_name, source_code in source_by_module.items():
            regex_paths = re.findall(r'app_name=["\']([\w_]+)["\'], ?namespace=["\']([\w_]+)["\']', source_code)
            namespace_map.update({})

    @classmethod
    def get_url_views_by_module(cls):
        source_by_module = cls.get_source_code(['urls'], lines=False)
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
                'view_params': cls.parse_args(regex_path[4], eval_args=False, eval_kwargs=False),
            } for regex_path in regex_paths if '#' not in regex_path[0]]

        return paths_by_module

    @classmethod
    def get_apps_by_name(cls, app_name=[]):
        if isinstance(app_name, str):
            app_name = [app_name]

        return [app for app in apps.get_app_configs() if app.name.startswith(tuple(app_name))]

    @classmethod
    def get_models_from_app(cls, app):
        if isinstance(app, str):
            apps = cls.get_apps_by_name(app_name=app)

            if len(apps) > 1:
                raise ValueError('App name "{}" is ambiguous'.format(app))

            app = apps[0]

        return [model for model in app.get_models()]

    @classmethod
    def get_models(cls):
        models = [model for app in cls.apps_to_check() for model in app.get_models()]

        for module_name, module_params in cls.get_url_views_by_module().items():
            for path_params in module_params:
                model = getattr(path_params['view_class'], 'model', None)
                if model and model not in models:
                    models.append(model)

        proxied_models = [model._meta.concrete_model for model in models if model._meta.proxy]
        proxied_apps = {apps.get_app_config(model._meta.app_label) for model in proxied_models}

        for app in proxied_apps:
            models.extend([model for model in app.get_models() if model not in models])

        return models

    @classmethod
    def get_models_with_required_fields(cls):
        return OrderedDict({
            model: [f for f in model._meta.get_fields() if
                    not getattr(f, 'blank', False) and f.concrete and not f.auto_created]
            for model in cls.get_models()
        })

    @classmethod
    def get_models_dependency(cls, required_only=True):
        models = cls.get_models()

        # find direct dependencies
        dependency = OrderedDict({
            model: {
                'required': {f.related_model for f in model._meta.get_fields()
                             if not getattr(f, 'blank', False) and isinstance(f,
                                                                              RelatedField) and f.concrete and not f.auto_created},
                'not_required': {} if required_only else {f.related_model for f in model._meta.get_fields()
                                                          if getattr(f, 'blank', False) and isinstance(f,
                                                                                                       RelatedField) and f.concrete and not f.auto_created},
            } for model in cls.get_models()
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
        for model, relations in cls.manual_model_dependency().items():
            dependency[model]['required'] |= relations

        # add deeper level dependencies
        for i in range(2):
            # include 2nd and 3rd level dependencies, increase range to increase depth level
            for model in dependency.keys():
                for necesary_model in set(dependency[model]['required']):
                    if necesary_model in dependency.keys():
                        dependency[model]['required'] |= dependency[necesary_model]['required']

        return dependency

    @classmethod
    def get_sorted_models_dependency(cls, required_only=False, reverse=False):
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

        sorted_models = sorted(cls.get_models_dependency(required_only).items(), key=lambda x: x[0]._meta.label,
                               reverse=reverse)
        sorted_models = OrderedDict(
            sorted(sorted_models, key=functools.cmp_to_key(compare_models_dependency), reverse=reverse))

        # pprint(sorted_models)
        return sorted_models

    @classmethod
    def generate_objs(cls):
        models_hierarchy = cls.get_sorted_models_dependency(required_only=False)
        generated_objs = OrderedDict()
        models = models_hierarchy.keys()

        for model in models:
            if model._meta.proxy:
                continue

            generated_objs[model] = cls.generate_model_objs(model)

        return generated_objs

    @classmethod
    def delete_ojbs(cls):
        models_hierarchy = cls.get_sorted_models_dependency(required_only=False, reverse=True)

        for model in models_hierarchy.keys():
            model.objects.all().delete()

    @classmethod
    def get_models_fields(cls, model, required=None, related=None):
        is_required = lambda f: not getattr(f, 'blank', False) if required is True else getattr(f, 'blank', False) if required is False else True
        is_related = lambda f: isinstance(f, RelatedField) if related is True else not isinstance(f, RelatedField) if related is False else True
        is_gm2m = lambda f: isinstance(f, GM2MField) if 'gm2m' in getattr(settings, 'INSTALLED_APPS') and related is True else False
        return [f for f in model._meta.get_fields() if (is_required(f) and is_related(f) and f.concrete and not f.auto_created) or (is_required(f) and is_gm2m(f))]

    @classmethod
    def generate_model_field_values(cls, model, field_values={}):
        not_related_fields = cls.get_models_fields(model, related=False)
        related_fields = cls.get_models_fields(model, related=True)
        ignore_model_fields = cls.IGNORE_MODEL_FIELDS.get(model, [])
        field_values = dict(field_values)
        m2m_values = {}
        unique_fields = list(itertools.chain(*model._meta.unique_together))

        for field in not_related_fields:
            if field.name not in ignore_model_fields and field.name not in field_values and (not isinstance(field, ManyToManyField)):
                field_value = field.default

                if inspect.isclass(field.default) and issubclass(field.default, NOT_PROVIDED) or field.default is None or field_value in [list]:
                    field_value = cls.default_field_name_map().get(field.name, None)

                    if field_value is None:
                        field_value = cls.default_field_map().get(field.__class__, None)

                    if callable(field_value):
                        field_value = field_value(field)

                else:
                    if callable(field_value):
                        field_value = field_value()

                if field_value is None:
                    raise ValueError(
                        'Don\'t know ho to generate {}.{} value {}'.format(model._meta.label, field.name, field_value))

                if isinstance(field, CharField) and (field.name in unique_fields or field.unique) and not field.choices:
                    field_value = f'{field_value}_{cls.next_id(model)}'

                field_values[field.name] = field_value

        m2m_classes = (ManyToManyField, GM2MField) if 'gm2m' in getattr(settings, 'INSTALLED_APPS') else ManyToManyField

        for field in related_fields:
            if isinstance(field, m2m_classes):
                if field.name in field_values:
                    m2m_values[field.name] = field_values[field.name]
                    del field_values[field.name]
            elif field.name not in ignore_model_fields and field.name not in field_values and field.related_model.objects.exists():
                field_value = field.default

                if inspect.isclass(field.default) and issubclass(field.default,
                                                                 NOT_PROVIDED) or field.default is None:
                    field_value = cls.default_field_map().get(field.__class__, None)

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

    @classmethod
    def generate_model_objs(cls, model):
        # required_fields = cls.get_models_fields(model, required_only=True)
        # related_fields = cls.get_models_fields(model, related_only=True)
        model_obj_values_map = cls.model_field_values_map().get(model, {cls.default_object_name(model): {}})
        new_objs = []

        for obj_name, obj_values in model_obj_values_map.items():
            obj = cls.objs.get(obj_name, None)

            if obj and obj._meta.model != model:
                obj_name = model._meta.label_lower
                obj = cls.objs.get(obj_name, None)

            if obj:
                try:
                    obj.refresh_from_db()
                except model.DoesNotExist:
                    obj = None

            if not obj:
                obj = cls.generate_obj(model, obj_values)
                new_objs.append(obj)
                cls.objs[obj_name] = obj

        return new_objs

    @classmethod
    def generate_obj(cls, model, field_values=None, **kwargs):
        if field_values is None:
            # use kwargs for values if dict is not passed
            if not kwargs:
                field_values = {}
            else:
                field_values = kwargs

        field_values = field_values(cls) if callable(field_values) else field_values
        field_values, m2m_values = cls.generate_model_field_values(model, field_values)
        post_save = field_values.pop('post_save', [])

        if model == cls.user_model():
            if hasattr(cls, 'create_user'):
                obj = cls.create_user(**field_values)
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

        for action in post_save:
            action(obj)

        return obj

    @classmethod
    def default_object_name(cls, model):
        # app_name, default_name = model._meta.label.split('.')
        # default_name = re.findall(r'.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', default_name)
        # default_name = '_'.join(default_name).lower()
        return model._meta.label_lower.split('.')[-1]

    @classmethod
    def get_generated_obj(cls, model=None, obj_name=None):
        if model is None and obj_name is None:
            raise Exception(f'At least one argument is necessary')

        if obj_name is None:
            if model._meta.proxy:
                model = model._meta.concrete_model

            if model in cls.model_field_values_map().keys():
                if model == cls.user_model() and 'superuser' in cls.model_field_values_map()[model].keys():
                    obj_name = 'superuser'
                elif isinstance(cls.model_field_values_map()[model], OrderedDict):
                    obj_name = list(cls.model_field_values_map()[model].keys())[0]
                else:
                    obj_name = sorted(list(cls.model_field_values_map()[model].keys()))[0]

            if obj_name not in cls.objs.keys():
                obj_name = cls.default_object_name(model)

        obj = cls.objs.get(obj_name, None)

        if obj:
            model = obj._meta.model

            try:
                obj.refresh_from_db()
            except model.DoesNotExist:
                obj = None

        if not obj:
            if model is None:
                for obj_model, objs in cls.model_field_values_map().items():
                    if obj_name in objs.keys():
                        model = obj_model
                        break

            cls.generate_model_objs(model)
            obj = cls.objs.get(obj_name, None)

        if not obj:
            if obj_name:
                raise Exception(f'{model} object with name {obj_name} doesn\'t exist')

            raise Exception('Something\'s fucked')

        return obj
        # return cls.objs.get(obj_name, model.objects.first())

    @classmethod
    def next_id(cls, model):
        return model.objects.order_by('id').last().id + 1 if model.objects.exists() else 0

    @classmethod
    def get_pdf_file_mock(cls, name='test.pdf'):
        file_path = os.path.join(os.path.dirname(__file__), 'blank.pdf')
        file = open(file_path, 'rb')
        file_mock = SimpleUploadedFile(
            name,
            file.read(),
            content_type='application/pdf'
        )
        return file_mock

    @classmethod
    def get_image_file_mock(cls, name='test.jpg', file_path=None):
        if file_path is None:
            file_path = os.path.join(os.path.dirname(__file__), 'blank.jpg')
        file = open(file_path, 'rb')
        file_mock = SimpleUploadedFile(
            name,
            file.read(),
            content_type='image/png'
        )
        return file_mock

    @classmethod
    def get_num_field_mock_value(cls, field):
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

    @classmethod
    def init_form_kwargs(cls, form_class, default={}):
        '''{
            UserForm: {'user': cls.get_generated_obj(User)},
        }
        '''
        return {}.get(form_class, cls.generate_func_args(form_class.__init__, default))

    @classmethod
    def init_filter_kwargs(cls, filter_class, default={}):
        '''{
            UserFitler: {'queryset': User.objects.all()}
        }
        '''
        return {}.get(filter_class, cls.generate_func_args(filter_class.__init__, default=default))

    @classmethod
    def setUpTestData(cls):
        super(GenericBaseMixin, cls).setUpTestData()

        cls.import_modules_if_needed()
        cls.generate_objs()

    def setUp(self):
        user = self.objs.get('superuser', self.get_generated_obj(self.user_model()))
        credentials = {'password': self.TEST_PASSWORD}

        if hasattr(user, 'email'):
            credentials['email'] = user.email

        if hasattr(user, 'username'):
            credentials['username'] = user.username

        logged_in = self.client.login(**credentials)
        self.assertTrue(logged_in)
        self.user = user

    @classmethod
    def print_last_fail(cls, failed):
        for k, v in failed[-1].items():
            print(k)
            print(v)

    @classmethod
    def create_formset_post_data(cls, response, post_data={}):
        post_data = {**post_data}
        formset_keys = [key for key in response.context.keys() if 'formset' in key and response.context[key]]

        for formset_key in formset_keys:
            formset = response.context[formset_key]
            # prefix_template = formset.empty_form.prefix # default is 'form-__prefix__'
            prefix = f'{formset.prefix}-'
            # extract initial formset data
            management_form_data = formset.management_form.initial

            # add properly prefixed management form fields
            for key, value in management_form_data.items():
                # prefix = prefix_template.replace('__prefix__', '')
                post_data[prefix + key] = value

            # generate individual forms data
            for index, form in enumerate(formset.forms):
                form_prefix = f'{prefix}{index}-'
                default_form_data = {key.replace(form_prefix, ''): value for key, value in post_data.items() if key.startswith(form_prefix)}
                post_data.update({f'{form_prefix}{key}': value for key, value in cls.generate_form_data(form, default_form_data).items()})

        return post_data


class GenericTestMixin(object):
    '''
    Only containing generic tests
    eveything else, setup methods etc., is in GenericBaseMixin
    '''

    def prepare_url(self, path_name, path_params, params_map, models, fields):
        '''
        generates url arguments if not provided, saves them in params_map['parsed'],
        returns url with args and list of fail messages
        '''
        fails = []
        path = path_name
        url_pattern = path_params["url_pattern"]
        args = re.findall(r'<([:\w]+)>', url_pattern)
        view_class = path_params['view_class']
        parsed_args = params_map.get('args', None)

        if parsed_args is None or not args:
            parsed_args = []

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

                    if type not in ['int', 'str', 'slug']:
                        fails.append(OrderedDict({
                            'location': 'URL ARG TYPE',
                            'url name': path_name,
                            'url pattern': url_pattern,
                            'arg': arg,
                            'traceback': 'Cant handle this arg type'
                        }))
                        continue

                    if name.endswith('_pk'):
                        # model name
                        matching_fields = [('pk', model) for model in models if
                                           name == '{}_pk'.format(model._meta.label_lower.split(".")[-1])]

                        if len(matching_fields) != 1:
                            # match field  model
                            matching_fields = [('pk', model) for model in models if name == '{}_pk'.format(
                                model._meta.verbose_name.lower().replace(' ', '_'))]

                    else:
                        # full name and type match
                        matching_fields = [(field, model) for field, model in fields if
                                           field.name == name and isinstance(field, IntegerField if type == 'int' else (
                                           CharField, BooleanField))]

                        if len(matching_fields) > 1:
                            # match field  model
                            matching_fields = [(field, model) for field, model in matching_fields if
                                               model == view_model]

                        elif not matching_fields:
                            # full name match
                            matching_fields = [(field, model) for field, model in fields if
                                               field.name == name and not model._meta.proxy]

                            if not matching_fields:
                                # match name in form model_field to model and field
                                matching_fields = [(field, model) for field, model in fields if
                                                   name == '{}_{}'.format(model._meta.label_lower.split(".")[-1],
                                                                          field.name)]

                            if not matching_fields:
                                # this might make problems as only partial match is made
                                matching_fields = [(p[0], view_model) for p in
                                                   inspect.getmembers(view_model, lambda o: isinstance(o, property)) if
                                                   p[0].startswith(name)]

                            if not matching_fields:
                                # name is contained in field.name of view model
                                matching_fields = [(field, model) for field, model in fields if
                                                   model == view_model and name in field.name]

                if len(matching_fields) != 1 or matching_fields[0][1] is None:
                    fails.append(OrderedDict({
                        'location': 'URL ARG MATCH',
                        'url name': path_name,
                        'url pattern': url_pattern,
                        'arg': arg,
                        'matching fields': matching_fields,
                        'traceback': 'Url arg mathcing failed'
                    }))
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
                    fails.append(OrderedDict({
                        'location': 'URL ARG PARSE',
                        'url name': path_name,
                        'url pattern': url_pattern,
                        'arg': arg,
                        'parsed arg': arg_value,
                        'traceback': 'Url arg parsing failed'
                    }))
                    continue

                parsed_args.append(arg_value)
                params_map['parsed'].append({'obj': obj, 'attr_name': attr_name, 'value': arg_value})

        if len(args) != len(parsed_args):
            fails.append(OrderedDict({
                'location': 'URL ARGS PARSED',
                'url name': path_name,
                'url pattern': url_pattern,
                'args': args,
                'parsed args': parsed_args,
                'traceback': 'Url args parsing failed'
            }))
        else:
            path = reverse(path_name, args=parsed_args)
            kwargs = params_map.get('kwargs', {})

            if kwargs:
                kwargs = '&'.join([f'{key}={value}' for key, value in kwargs.items()])
                path = f'{path}?{kwargs}'

        return path, parsed_args, fails

    def get_namespace(self, path_params, module_name):
        module_namespace = module_name.replace('.urls', '').split('.')[-1]
        app_name = path_params['app_name']
        path_name = path_params['path_name']
        fails = []

        namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                      namespace.endswith(module_namespace) and path_name in namespace_path_names]

        if not namespaces:
            namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                          namespace.endswith(app_name) and path_name in namespace_path_names]

        if not namespaces:
            namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                          path_name in namespace_path_names]

        if len(namespaces) != 1:
            fails.append(OrderedDict({
                'location': 'NAMESPACE',
                'url name': path_params["path_name"],
                'app_name': app_name,
                'module': module_name,
                'matching namespaces': namespaces,
                'traceback': 'Namespace matching failed'
            }))

        return namespaces[0], fails

    def skip_url(self, url_name):
        if self.RUN_ONLY_THESE_URL_NAMES and url_name not in self.RUN_ONLY_THESE_URL_NAMES:
            # print('SKIP')
            return True

        if self.RUN_URL_NAMES_CONTAINING and not url_name.endswith(
                tuple(self.RUN_URL_NAMES_CONTAINING)) and not url_name.startswith(
                tuple(self.RUN_URL_NAMES_CONTAINING)):
            # print('SKIP')
            return True

        if url_name.endswith(tuple(self.IGNORE_URL_NAMES_CONTAINING)) or url_name.startswith(
                tuple(self.IGNORE_URL_NAMES_CONTAINING)):
            # print('SKIP')
            return True

        return False

    def get_url_tes(self, path_name, path, parsed_args, url_pattern, view_class, params_map):
        fails = []
        data = params_map.get('data', {})

        try:
            get_response = self.client.get(path=path, data=data, follow=True)
            self.assertEqual(get_response.status_code, 200)
        except Exception as e:
            fails.append(OrderedDict({
                'location': 'GET',
                'url name': path_name,
                'url': path,
                'url pattern': url_pattern,
                'parsed args': parsed_args,
                'view class': view_class,
                'traceback': traceback.format_exc()
            }))
            return None, fails

        if hasattr(view_class, 'sorting_options'):  # and isinstance(view_class.sorting_options, dict):
            sorting_options = params_map.get('sorting_options', [])

            if not sorting_options:
                sorting_options = view_class.sorting_options.keys()

            for sorting in sorting_options:
                data['sorting'] = sorting

                try:
                    response = self.client.get(path=path, data=data, follow=True)
                    self.assertEqual(response.status_code, 200)
                except Exception as e:
                    fails.append(OrderedDict({
                        'location': 'SORTING',
                        'url name': path_name,
                        'url': path,
                        'url pattern': url_pattern,
                        'parsed args': parsed_args,
                        'data': data,
                        'traceback': traceback.format_exc()
                    }))

        if hasattr(view_class, 'displays'):
            displays = params_map.get('displays', view_class.displays)

            for display in displays:
                data['display'] = display

                try:
                    response = self.client.get(path=path, data=data, follow=True)
                    self.assertEqual(response.status_code, 200)
                except Exception as e:
                    fails.append(OrderedDict({
                        'location': 'DISPLAY',
                        'url name': path_name,
                        'url': path,
                        'url pattern': url_pattern,
                        'parsed args': parsed_args,
                        'data': data,
                        'traceback': traceback.format_exc()
                    }))
                else:
                    if hasattr(response, 'template_name'):
                        template = response.template_name[-1] if isinstance(response.template_name,
                                                                            list) else response.template_name

                        try:
                            self.assertTrue(template.endswith('{}.html'.format(display)))
                        except Exception as e:
                            fails.append(OrderedDict({
                                'location': 'TEMPLATE',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'data': data,
                                'template': template,
                                'traceback': traceback.format_exc()
                            }))
        return get_response, fails

    def post_url_test(self, path_name, path, parsed_args, url_pattern, view_class, params_map, get_response):
        fails = []
        data = params_map.get('data', {})

        try:
            with transaction.atomic():
                form_class = view_class.form_class
                view_model = view_class.model if hasattr(view_class, 'model') else form_class.model if hasattr(
                    form_class, 'model') else None
                form_kwargs = params_map.get('form_kwargs', self.generate_func_args(form_class.__init__))
                form_kwargs = {key: value(self) if callable(value) else value for key, value in form_kwargs.items()}
                form_kwargs['data'] = data
                form = None

                if path_name not in self.POST_ONLY_URLS and 'form' in get_response.context_data:
                    form = get_response.context_data['form']
                else:
                    init_form_kwargs = self.init_form_kwargs(form_class)

                    try:
                        form = form_class(**init_form_kwargs)
                    except Exception as e:
                        if not isinstance(form, form_class) or not hasattr(form, 'fields'):
                            # as long as there is form instance with fields its enough to generate data
                            fails.append(OrderedDict({
                                'location': 'POST FORM INIT',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'form class': form_class,
                                'form kwargs': init_form_kwargs,
                                'traceback': traceback.format_exc()
                            }))
                            return fails

                query_dict_data = QueryDict('', mutable=True)

                try:
                    query_dict_data.update(self.generate_form_data(form, data))
                except Exception as e:
                    fails.append(OrderedDict({
                        'location': 'POST GENERATING FORM DATA',
                        'url name': path_name,
                        'url': path,
                        'url pattern': url_pattern,
                        'parsed args': parsed_args,
                        'form class': form_class,
                        'default form data': data,
                        'traceback': traceback.format_exc()
                    }))
                    return fails

                if not view_model:
                    return fails

                form_kwargs['data'] = query_dict_data
                obj_count_before = 0

                if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
                    obj_count_before = view_model.objects.all().count()

                try:
                    response = self.client.post(path=path, data=form_kwargs['data'], follow=True)
                    self.assertEqual(response.status_code, 200)
                except ValidationError as e:
                    if e.message == ugettext_lazy('ManagementForm data is missing or has been tampered with'):
                        post_data = QueryDict('', mutable=True)

                        try:
                            post_data.update(self.create_formset_post_data(get_response, data))
                        except Exception as e:
                            fails.append(OrderedDict({
                                'location': 'POST GENERATING FORMSET DATA',
                                'url name': path_name,
                                'url': path,
                                'url pattern': url_pattern,
                                'parsed args': parsed_args,
                                'form class': form_class,
                                'default form data': data,
                                'post data': post_data,
                                'traceback': traceback.format_exc()
                            }))
                            return fails

                        try:
                            response = self.client.post(path=path, data=post_data, follow=True)
                            self.assertEqual(response.status_code, 200)
                        except Exception as e:
                            fails.append(OrderedDict({
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
                            return fails
                    else:
                        fails.append(OrderedDict({
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
                        return fails

                except Exception as e:
                    fails.append(OrderedDict({
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
                    return fails

                if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
                    obj_count_after = view_model.objects.all().count()

                    try:
                        if issubclass(view_class, CreateView):
                            self.assertEqual(obj_count_after, obj_count_before + 1)
                        elif issubclass(view_class, UpdateView):
                            self.assertEqual(obj_count_after, obj_count_before)
                        elif issubclass(view_class, DeleteView):
                            self.assertEqual(obj_count_after, obj_count_before - 1)
                            # recreate obj is not necessary because of transaction rollback

                    except Exception as e:
                        # for key, value in init_form_kwargs.items():
                        #     if key not in form_kwargs:
                        #         form_kwargs[key] = value

                        # form = form_class(**form_kwargs)
                        form = response.context_data.get('form', None)

                        fails.append(OrderedDict({
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
                        return fails

                # rollback post action
                raise IntegrityError('No problem')

        except IntegrityError as e:
            if e.args[0] != 'No problem':
                raise
        except Exception:
            raise

        return fails

    def test_urls(self):
        models = self.get_models()
        fields = [(f, model) for model in models for f in model._meta.get_fields() if f.concrete and not f.auto_created]
        failed = []
        tested = []
        for module_name, module_params in self.get_url_views_by_module().items():
            for path_params in module_params:
                # print(path_params)
                path = path_name = path_params['path_name']

                namespace, fails = self.get_namespace(path_params, module_name)

                if fails:
                    failed.extend(fails)
                    continue

                path = path_name = '{}:{}'.format(namespace, path_name) if namespace else path_params['path_name']

                if self.skip_url(path_name):
                    continue

                print(path_params)
                tested.append(path_params)
                url_pattern = path_params["url_pattern"]
                view_class = path_params['view_class']
                params_maps = self.url_params_map.get(path_name, {'default': {}})

                for map_name, params_map in params_maps.items():
                    parsed_args = params_map.get('args', None)
                    data = params_map.get('data', {})

                    path, parsed_args, fails = self.prepare_url(path_name, path_params, params_map, models, fields)

                    if fails:
                        failed.extend(fails)
                        continue

                    # GET url
                    if not path_name in self.POST_ONLY_URLS:
                        get_response, fails = self.get_url_tes(path_name, path, parsed_args, url_pattern, view_class, params_map)

                        if fails:
                            failed.extend(fails)
                            continue

                    # POST url
                    if path_name not in self.GET_ONLY_URLS and getattr(view_class, 'form_class', None):
                        fails = self.post_url_test(path_name, path, parsed_args, url_pattern, view_class, params_map, get_response)

                        if fails:
                            failed.extend(fails)
                            continue

        if failed:
            # append failed count at the end of error list
            failed.append('{}/{} urls FAILED: {}'.format(len(failed), len(tested), ', '.join([f['url name'] for f in failed])))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

    def test_querysets(self):
        models_querysets = [model._default_manager.all() for model in self.get_models()]
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
                                'model': qs.model,
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
                                'model': qs.model,
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
                                'model': qs.model,
                                'queryset method': '{}.{}'.format(qs_class_label, name),
                                'traceback': traceback.format_exc(),
                            }])
                        else:
                            try:
                                result = getattr(qs, name)(**kwargs)
                            except Exception as e:
                                failed.append([{
                                    'location': 'GENERATED KWARGS',
                                    'model': qs.model,
                                    'queryset method': '{}.{}'.format(qs_class_label, name),
                                    'kwargs': kwargs,
                                    'traceback': traceback.format_exc(),
                                }])

        if failed:
            failed.append('{} qeuryset methods FAILED'.format(len(failed)))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

    def test_filters(self):
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
            params_maps = self.filter_params_map.get(filter_class, {'default': {}})

            for map_name, params_map in params_maps.items():
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
                    continue

                try:
                    queryset = init_kwargs.get('queryset', filter_class._meta.model._default_manager.all() if filter_class._meta.model else None)
                except Exception as e:
                    failed.append(OrderedDict({
                        'location': 'FILTER QUERYSET',
                        'filter class': filter_class,
                        'params map': params_map,
                        'traceback': traceback.format_exc()
                    }))
                    continue

                if queryset:
                    init_kwargs['queryset'] = queryset

                try:
                    filter = filter_class(data=query_dict_data, **init_kwargs)
                    qs = filter.qs.all().values()
                except Exception as e:
                    failed.append(OrderedDict({
                        'location': 'FILTER',
                        'filter class': filter_class,
                        'data': query_dict_data,
                        'queryset': queryset,
                        'params map': params_map,
                        'traceback': traceback.format_exc()
                    }))
                    continue

        if failed:
            failed.append('{} filters FAILED'.format(len(failed)))

        self.assertFalse(failed, msg=pformat(failed, indent=4))

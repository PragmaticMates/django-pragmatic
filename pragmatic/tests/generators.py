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

from allauth.account.forms import PasswordField, SetPasswordField
from django import urls
from django.apps import apps
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models as gis_models
from django.contrib.gis import forms as gis_forms
from django.contrib.gis.geos import Point
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.postgres.fields import DateTimeRangeField, DateRangeField
from django.contrib.postgres import forms as postgress_forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import NOT_PROVIDED, BooleanField, TextField, CharField, SlugField, EmailField, DateTimeField, \
    DateField, FileField, PositiveSmallIntegerField, DecimalField, IntegerField, QuerySet
from django.db.models.fields.related import RelatedField, ManyToManyField, ForeignKey, OneToOneField
from django.forms import fields as django_form_fields
from django.forms import models as django_form_models
from django.http import QueryDict
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import CreateView, UpdateView, DeleteView
import django_countries.fields as django_countries_fields
from django_iban.fields import IBANField, IBANFormField, SWIFTBICField
from internationalflavor.countries import CountryField, CountryFormField
from internationalflavor.countries.data import UN_RECOGNIZED_COUNTRIES
from internationalflavor.vat_number import VATNumberField, VATNumberFormField
from phonenumber_field.formfields import PhoneNumberField
from taggit.forms import TagField


class GenericTestMixin(object):
    USER_MODEL = User
    objs = OrderedDict()

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
            return get_user_model()
        except:
            return self.USER_MODEL

    @property
    def default_field_map(self):
        # values can be callables with with field variable
        return {
            ForeignKey: lambda f: self.get_generated_obj(f.related_model),
            OneToOneField: lambda f: self.get_generated_obj(f.related_model),
            BooleanField: False,
            TextField: lambda f: f'{f.model._meta.label_lower}_{f.name}',
            CharField: lambda f: list(f.choices)[0][0] if f.choices else f'{f.model._meta.label_lower}_{f.name}'[
                                                                         :f.max_length],
            SlugField: lambda f: f'{f.name}_{self.next_id(f.model)}',
            EmailField: lambda f: f'{f.model._meta.label_lower}.{self.next_id(f.model)}@example.com',
            django_countries_fields.CountryField: 'LU',
            CountryField: 'LU',
            IBANField: 'LU28 0019 4006 4475 0000',
            SWIFTBICField: 'BCEELULL',
            gis_models.PointField: Point(0.1276, 51.5072),
            VATNumberField: lambda f: f'LU{random.randint(10000000, 99999999)}',  # 'GB904447273',
            DateTimeField: now(),
            DateField: now().date(),
            DateTimeRangeField: (now(), now() + timedelta(days=1)),
            DateRangeField: (now().date(), now() + timedelta(days=1)),
            FileField: self.get_pdf_file_mock(),
            IntegerField: self.get_num_field_mock_value,
            PositiveSmallIntegerField: self.get_num_field_mock_value,
            DecimalField: self.get_num_field_mock_value,
        }

    @property
    def default_form_field_map(self):
        # values can be callables with with field variable
        return {
            django_form_fields.EmailField: lambda f: self.get_new_email(),
            django_form_fields.CharField: lambda f: f'{f.label} {random.random()}'[:f.max_length],
            django_form_fields.TypedChoiceField: lambda f: list(f.choices)[-1][0] if f.choices else f'{f.label}'[
                                                                                                    :f.max_length],
            django_form_fields.ChoiceField: lambda f: list(f.choices)[-1][0] if f.choices else f'{f.label}'[:f.max_length],
            django_form_fields.MultipleChoiceField: lambda f: [list(f.choices)[-1][0]] if f.choices else [f'{f.label}'[:f.max_length]],
            PhoneNumberField: '+420723270884',
            PasswordField: self.TEST_PASSWORD,
            SetPasswordField: self.TEST_PASSWORD,
            CountryFormField: 'LU',  # random.choice(UN_RECOGNIZED_COUNTRIES),
            django_countries_fields.LazyTypedChoiceField: 'LU',  # random.choice(UN_RECOGNIZED_COUNTRIES),
            VATNumberFormField: lambda f: f'LU{random.randint(10000000, 99999999)}',  # 'GB904447273',
            django_form_fields.URLField: 'www.example.com',
            django_form_fields.ImageField: self.get_image_file_mock(),
            django_form_fields.FileField: self.get_pdf_file_mock(),
            django_form_fields.DateTimeField: now(),
            django_form_fields.DateField: now().date(),
            django_form_fields.IntegerField: lambda f: self.get_num_field_mock_value(f),
            django_form_fields.DecimalField: lambda f: self.get_num_field_mock_value(f),
            django_form_models.ModelMultipleChoiceField: lambda f: [f.queryset.first().id],
            django_form_models.ModelChoiceField: lambda f: f.queryset.first().id,
            django_form_fields.BooleanField: True,
            IBANFormField: 'LU28 0019 4006 4475 0000',
            TagField: lambda f: 'tag',
            gis_forms.PointField: 'POINT (0.1276 51.5072)',
            django_form_fields.DurationField: 1,
            postgress_forms.SimpleArrayField: lambda f: [self.default_form_field_map[f.base_field.__class__](f.base_field)]
        }

    def import_modules_if_needed(self):
        module_names = self.get_submodule_names(self.CHECK_MODULES, self.CHECK_MODULES, self.EXCLUDE_MODULES)

        for module_name in module_names:
            try:
                if module_name not in sys.modules.keys():
                    importlib.import_module(module_name)
            except Exception as e:
                print(f'Failed to import module: {module_name}')
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

        return args, kwargs

    def get_generated_email(self, model=None):
        if model is None:
            model = self.user_model

        return self.get_generated_obj(model).email

    def get_new_email(self):
        return f'email.{random.random()}@example.com'

    def generate_kwargs(self, args=[], kwargs={}):
        # so far only matching model names with kwargs names and assigning generated objects accordingly
        models = {model._meta.label_lower.split('.')[-1]: model for model in self.get_models()}
        result_kwargs = {}
        try:
            for name, value in kwargs.items():
                if name == 'email':
                    result_kwargs[name] = self.get_generated_email()
                else:
                    matching_models = [model for model_name, model in models.items() if model_name == name]

                    if len(matching_models) == 1:
                        result_kwargs[name] = self.get_generated_obj(matching_models[0])

        except:
            raise
            kwargs = {}

        for arg in args:
            if arg in ['self', '*args', '**kwargs']:
                continue

            if arg == 'email':
                result_kwargs[arg] = self.get_generated_email()
            else:
                matching_models = [model for name, model in models.items() if name == arg]

                if len(matching_models) == 1:
                    result_kwargs[arg] = self.get_generated_obj(matching_models[0])

        return result_kwargs

    def generate_func_args(self, func):
        source = inspect.getsource(func)
        args = r'([^\)]*)'
        args = re.findall(f'def {func.__name__}\({args}\):', source)
        return self.generate_kwargs(*self.parse_args(args[0], eval_args=False, eval_kwargs=False))

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
                namespaces[f'{key_1}:{key_2}'] = [key for key in resolver_2[1].reverse_dict.keys() if not callable(key)]

                for key_3, resolver_3 in resolver_2[1].namespace_dict.items():
                    namespaces[f'{key_1}:{key_2}:{key_3}'] = [key for key in resolver_3[1].reverse_dict.keys() if
                                                              not callable(key)]

        return namespaces

    def get_url_views_by_module(self):
        source_by_module = self.get_source_code(['urls'], lines=False)
        paths_by_module = OrderedDict()

        skip_comments = r'(?:[^# ])(?:[ \t]*)'
        pgettext_str = r'(?:pgettext_lazy\(["\']url["\'],)? ?'
        url_pattern = r'["\'](.*)["\']'
        view_class = r'(\w+)'
        view_params = r'([^\)]*)'
        path_name = r'["\']([\w-]+)["\']'

        for module_name, source_code in source_by_module.items():
            regex_paths = re.findall(
                f'{skip_comments}path\({pgettext_str}{url_pattern}\)?, ?{view_class}.as_view\({view_params}\), ?name={path_name}',
                source_code)
            imported_classes = dict(inspect.getmembers(sys.modules[module_name], inspect.isclass))
            app_name = re.findall(f'app_name *= *\'(\w+)\'', source_code)

            paths_by_module[module_name] = [{
                'path_name': f'{app_name[0]}:{regex_path[3]}',
                'url_pattern': regex_path[0],
                'view_class': imported_classes.get(regex_path[1], None),
                'view_params': self.parse_args(regex_path[2], eval_args=False, eval_kwargs=False),
            } for regex_path in regex_paths]

        return paths_by_module

    def get_apps_by_name(self, app_name=[]):
        if isinstance(app_name, str):
            app_name = [app_name]

        return [app for app in apps.get_app_configs() if app.name.startswith(tuple(app_name))]

    def get_models_from_app(self, app):
        if isinstance(app, str):
            apps = self.get_apps_by_name(app_name=app)

            if len(apps) > 1:
                raise ValueError(f'App name "{app}" is ambiguous')

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
                raise ValueError(f'Circular dependency of models {x[0]}, {y[0]}')

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

    def get_models_fields(self, model, required_only=False, related_only=False):
        required = lambda f: not getattr(f, 'blank', False) if required_only else True
        related = lambda f: isinstance(f, RelatedField) if related_only else True
        return [f for f in model._meta.get_fields() if required(f) and related(f) and f.concrete and not f.auto_created]

    def generate_model_objs(self, model):
        required_fields = self.get_models_fields(model, required_only=True)
        related_fields = self.get_models_fields(model, related_only=True)
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

                for field in required_fields:
                    if field.name not in field_values:
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
                                f'Don\'t know ho to generate {model._meta.label}.{field.name} value {field_value}')

                        field_values[field.name] = field_value

                # generate non required field values
                for field in related_fields:
                    if field.name not in field_values and not isinstance(field,
                                                                         ManyToManyField) and field.related_model.objects.exists():
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
                                f'Don\'t know ho to generate {model._meta.label}.{field.name} value {field_value}')

                        field_values[field.name] = field_value

                obj = getattr(model.objects, 'create_user' if model == self.user_model else 'create')(**field_values)
                new_objs.append(obj)
                self.objs[obj_name] = obj

        return new_objs


    def get_generated_obj(self, model):
        obj_name = None

        if model._meta.proxy:
            model = model._meta.concrete_model

        if model in self.model_field_values_map.keys():
            obj_name = list(self.model_field_values_map[model].keys())[0]

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

    def get_image_file_mock(self, name='test.jpg'):
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
                value = (field.validators[0].limit_value + field.validators[1].limit_value) / 2

                if isinstance(field, IntegerField):
                    return int(value)

                return value

            validator = field.validators[0]

            if isinstance(validator, MinValueValidator):
                return validator.limit_value + 1

            if isinstance(validator, MaxValueValidator):
                return validator.limit_value - 1

        return 1



class GenericTestCase(GenericTestMixin, TestCase):
    '''IGNORE_URL_NAMES_CONTAINING = [
        'select2',
    ]
    '''
    IGNORE_URL_NAMES_CONTAINING = []
    TEST_PASSWORD = 'testpassword'

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

    def init_form_kwargs(self, form_class):
        '''{
            UserForm: {'user': self.get_generated_obj(User)},
        }
        '''
        return {}.get(form_class, self.generate_func_args(form_class.__init__))

    def setUp(self):
        super().setUp()
        self.generate_objs()
        user = self.get_generated_obj(self.user_model)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        logged_in = self.client.login(email=user.email, username=user.username, password=self.TEST_PASSWORD)
        self.assertTrue(logged_in)
        self.user = user

    def tearDown(self):
        self.delete_ojbs()
        super().tearDown()

    def test_urls(self):
        models = self.get_models()
        fields = [(f, model) for model in models for f in model._meta.get_fields() if f.concrete and not f.auto_created]
        failed_urls = []

        for module_name, module_params in self.get_url_views_by_module().items():
            for path_params in module_params:
                path_namespace, path_name = path_params['path_name'].split(':')
                namespaces = [namespace for namespace, namespace_path_names in self.get_url_namespace_map().items() if
                              namespace.endswith(path_namespace) and path_name in namespace_path_names]

                if len(namespaces) > 1:
                    failed_urls.append(OrderedDict({
                        'location': 'NAMESPACE',
                        'url name': path_params["path_name"],
                        'module': module_name,
                        'matching namespaces': namespaces,
                        'traceback': 'Namespace matching failed'
                    }))
                    continue

                path_name = f'{namespaces[0]}:{path_name}'

                if path_name.endswith(tuple(self.IGNORE_URL_NAMES_CONTAINING)):
                    continue

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
                                    failed_urls.append(OrderedDict({
                                        'location': 'URL ARG TYPE',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'arg': arg,
                                        'traceback': 'Cant handle this arg type'
                                    }))
                                    continue

                                if name.endswith('_pk'):
                                    matching_fields = [('pk', model) for model in models if
                                                       name == f'{model._meta.label_lower.split(".")[-1]}_pk']
                                else:
                                    # full name and type match
                                    matching_fields = [(field, model) for field, model in fields if
                                                       field.name == name and isinstance(field,
                                                                                         IntegerField if type == 'int' else CharField)]

                                    if len(matching_fields) > 1:
                                        # match field  model
                                        matching_fields = [(field, model) for field, model in matching_fields if
                                                           model == view_model]

                                    elif not matching_fields:
                                        # match name in form model_field to model and field
                                        matching_fields = [(field, model) for field, model in fields if
                                                           name == f'{model._meta.label_lower.split(".")[-1]}_{field.name}']

                                        if not matching_fields:
                                            # this might make problems as only partial match is made
                                            matching_fields = [(property[0], view_model) for property in
                                                               inspect.getmembers(view_model,
                                                                                  lambda o: isinstance(o, property)) if
                                                               property[0].startswith(name)]

                            if len(matching_fields) != 1:
                                failed_urls.append(OrderedDict({
                                    'location': 'URL ARG MATCH',
                                    'url name': path_name,
                                    'url': path,
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

                            if arg_value is None:
                                failed_urls.append(OrderedDict({
                                    'location': 'URL ARG PARSE',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'arg': arg,
                                    'parsed arg': arg_value,
                                    'traceback': 'Url arg parsing failed'
                                }))
                                continue

                            parsed_args.append(arg_value)
                            params_map['parsed'].append({'obj': obj, 'attr_name': attr_name, 'value': arg_value})

                    path = reverse(path_name, args=parsed_args, kwargs=params_map.get('kwargs', {}))
                    data = params_map.get('data', {})

                    # GET url
                    try:
                        response = self.client.get(path=path, data=data, follow=True)
                        self.assertEqual(response.status_code, 200)
                    except Exception as e:
                        failed_urls.append(OrderedDict({
                            'location': 'GET',
                            'url name': path_name,
                            'url': path,
                            'url pattern': url_pattern,
                            'parsed args': parsed_args,
                            'traceback': traceback.format_exc()
                        }))
                    else:
                        if hasattr(view_class, 'sorting_options'):  # and isinstance(view_class.sorting_options, dict):
                            for sorting, label in view_class.sorting_options.items():
                                data['sorting'] = sorting

                                try:
                                    response = self.client.get(path=path, data=data, follow=True)
                                    self.assertEqual(response.status_code, 200)
                                except Exception as e:
                                    failed_urls.append(OrderedDict({
                                        'location': 'SORTING',
                                        'url name': path_name,
                                        'url': path,
                                        'url pattern': url_pattern,
                                        'parsed args': parsed_args,
                                        'data': data,
                                        'traceback': traceback.format_exc()
                                    }))

                        if hasattr(view_class, 'displays'):
                            # self.check_display_options(view, path, params)
                            for display in view_class.displays:
                                data['display'] = display

                                try:
                                    response = self.client.get(path=path, data=data, follow=True)
                                    self.assertEqual(response.status_code, 200)
                                except Exception as e:
                                    failed_urls.append(OrderedDict({
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
                                            self.assertTrue(template.endswith(f'{display}.html'))
                                        except Exception as e:
                                            failed_urls.append(OrderedDict({
                                                'location': 'TEMPLATE',
                                                'url name': path_name,
                                                'url': path,
                                                'url pattern': url_pattern,
                                                'parsed args': parsed_args,
                                                'data': data,
                                                'template': template,
                                                'traceback': traceback.format_exc()
                                            }))

                        # POST url
                        if getattr(view_class, 'form_class', None):
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
                                    raise

                            query_dict_data = QueryDict('', mutable=True)
                            query_dict_data.update(self.generate_form_data(form, data))
                            form_kwargs['data'] = query_dict_data

                            obj_count_before = 0

                            if issubclass(view_class, (CreateView, UpdateView, DeleteView)):
                                obj_count_before = view_class.model.objects.all().count()

                            try:
                                response = self.client.post(path=path, data=form_kwargs['data'], follow=True)
                                self.assertEqual(response.status_code, 200)

                            except Exception as e:
                                failed_urls.append(OrderedDict({
                                    'location': 'POST',
                                    'url name': path_name,
                                    'url': path,
                                    'url pattern': url_pattern,
                                    'parsed args': parsed_args,
                                    'form': form,
                                    'data': form_kwargs['data'],
                                    'traceback': traceback.format_exc()
                                }))
                            else:
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
                                        # most likely form error need to recreate form, use generated objs
                                        # double check with request params if it seems ok

                                        for key, value in init_form_kwargs.items():
                                            if key not in form_kwargs:
                                                form_kwargs[key] = value

                                        form = form_class(**form_kwargs)

                                        failed_urls.append(OrderedDict({
                                            'location': 'POST COUNT',
                                            'url name': path_name,
                                            'url': path,
                                            'url pattern': url_pattern,
                                            'parsed args': parsed_args,
                                            'form': form,
                                            'form vaid': form.is_valid(),
                                            'form errors': form.errors,
                                            'data': form_kwargs['data'],
                                            'traceback': traceback.format_exc()
                                        }))

        if failed_urls:
            # append failed count at the end of error list
            failed_urls.append(f'{len(failed_urls)} urls FAILED')

        self.assertFalse(failed_urls, msg=pformat(failed_urls, indent=4))

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
                    result = None
                    kwargs = {}

                    if func.__code__.co_argcount == 1:
                        # no arguments except self
                        try:
                            result = getattr(qs, name)()
                        except Exception as e:
                            failed.append([{
                                'location': 'NO KWARGS',
                                'queryset method': f'{qs_class_label}.{name}',
                                'traceback': traceback.format_exc(),
                            }])

                    elif name in params_map:
                        kwargs = params_map[name]

                        try:
                            result = getattr(qs, name)(**kwargs)
                        except Exception as e:
                            failed.append([{
                                'location': 'DEFAULT KWARGS',
                                'queryset method': f'{qs_class_label}.{name}',
                                'kwargs': kwargs,
                                'traceback': traceback.format_exc(),
                            }])
                    else:
                        kwargs = self.generate_func_args(func)

                        try:
                            result = getattr(qs, name)(**kwargs)
                        except Exception as e:
                            failed.append([f'{qs_class_label}.{name}({args[0]})', f'Failed to generate kwargs {kwargs}',
                                           traceback.format_exc()])
                            failed.append([{
                                'location': 'GENERATED KWARGS',
                                'queryset method': f'{qs_class_label}.{name}({args[0]})',
                                'kwargs': kwargs,
                                'traceback': traceback.format_exc(),
                            }])

        if failed:
            failed.append(f'{len(failed)} qeuryset methods FAILED')

        self.assertFalse(failed, msg=pformat(failed, indent=4))


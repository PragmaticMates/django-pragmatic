from functools import wraps

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import pre_save, pre_delete, post_save, post_delete, pre_init, post_init, pre_migrate, post_migrate, m2m_changed
from django.utils.timezone import now


def add_apm_custom_context(type, value):
    from elasticapm.traces import execution_context
    transaction = execution_context.get_transaction()

    if not transaction:
        return

    if 'custom' not in transaction.context:
        transaction.context['custom'] = {}

    if type not in transaction.context['custom']:
        transaction.context['custom'][type] = [value]
    else:
        transaction.context['custom'][type].append(value)


def apm_custom_context(type, instance_attr='instance'):
    """
    A decorator for connecting functions to APM. Used by passing the context type:

        @apm_custom_context('signals')
        def my_custom_signal(sender, instance, **kwargs):
            ...

        @apm_custom_context('tasks')
        def my_custom_task(arg1, arg2):
            ...
    """
    def _decorator(func):
        """
        Decorator to send custom information to APM.
        """

        def wrapper(*args, **kwargs):
            try:
                from elasticapm.traces import execution_context

                apm_message = None

                if type == 'signals':
                    instance = kwargs.get(instance_attr, None)

                    if instance:
                        prefix = ''

                        signal = kwargs.get('signal')

                        if signal == pre_migrate:
                            prefix = '[pre_migrate]\t'
                        elif signal == pre_init:
                            prefix = '[pre_init]\t'
                        elif signal == pre_save:
                            prefix = '[pre_save]\t'
                        elif signal == pre_delete:
                            prefix = '[pre_delete]\t'
                        elif signal == post_migrate:
                            prefix = '[post_migrate]\t'
                        elif signal == post_init:
                            prefix = '[post_init]\t'
                        elif signal == post_save:
                            prefix = '[post_save]\t'
                        elif signal == post_delete:
                            prefix = '[post_delete]\t'
                        elif signal == m2m_changed:
                            prefix = '[m2m_changed]\t'

                        apm_message = f'{prefix}{func.__module__}.{func.__qualname__}({instance.__class__.__name__}: {instance.id})'.strip()

                elif type == 'tasks':
                    # execute task with given arguments

                    arguments = str(args)
                    apm_message = f'{func.__module__}.{func.__qualname__}{arguments}'

                if apm_message:
                    if settings.APM_DEBUG:
                        print(f'apm_message [{type}]:', apm_message)

                    add_apm_custom_context(type, apm_message)

                return func(*args, **kwargs)
            except ImportError:
                # elasticapm is not installed
                return func(*args, **kwargs)

        # return wrapper
        return wraps(func)(wrapper)  # important to preserve function signature!

    return _decorator


class SignalsHelper(object):
    @staticmethod
    def add_task_to_instance(instance, func, arguments, attr_name):
        # get existing tasks
        tasks = getattr(instance, attr_name, [])

        # prepare task
        task = (func, arguments)

        # add task to the list
        tasks.append(task)

        # save tasks into instance
        setattr(instance, attr_name, tasks)

    @staticmethod
    def add_task_and_connect(sender, instance, func, arguments, signal_type='post_save'):
        attr_name = f'{signal_type}_signal_tasks'
        receiver_name = f'{signal_type}_tasks_receiver'

        if signal_type == 'post_save':
            signal = post_save
        elif signal_type == 'post_delete':
            signal = post_delete
        else:
            raise NotImplementedError()

        receiver = getattr(SignalsHelper, receiver_name)

        SignalsHelper.add_task_to_instance(instance, func, arguments, attr_name)
        signal.connect(receiver=receiver, sender=sender, weak=True)

    @staticmethod
    @apm_custom_context('signals')
    def post_save_tasks_receiver(sender, instance, **kwargs):
        SignalsHelper.execute_instance_tasks(instance, 'post_save_signal_tasks')

    @staticmethod
    @apm_custom_context('signals')
    def post_delete_tasks_receiver(sender, instance, **kwargs):
        SignalsHelper.execute_instance_tasks(instance, 'post_delete_signal_tasks')

    @staticmethod
    def execute_task(task):
        # execute task with given arguments
        func = task[0]
        arguments = task[1]
        func(*arguments)

    @staticmethod
    def execute_instance_tasks(instance, attr_name):
        # start timer
        start = now()

        # get instance tasks
        tasks = getattr(instance, attr_name, [])
        total_tasks = len(tasks)

        if settings.APM_DEBUG:
            SignalsHelper._print('>>> SignalsHelper instance tasks [{} in total]: {}'.format(total_tasks, tasks), total_tasks > 0)
        else:
            SignalsHelper._print('>>> SignalsHelper instance tasks [{} in total]'.format(total_tasks), total_tasks > 0)

        # clean instance tasks: this allows calling own save() for model instances
        setattr(instance, attr_name, [])

        for task in tasks:
            SignalsHelper.execute_task(task)

        # end timer
        duration = (now() - start).total_seconds()
        SignalsHelper._print('SignalsHelper.process_response took {} seconds'.format(duration))

    @staticmethod
    def get_db_instance(instance):
        try:
            model = type(instance)
            return model._default_manager.get(pk=instance.pk)
        except ObjectDoesNotExist:
            # object did not exist before
            return None

    @staticmethod
    def attribute_changed(instance, diff_fields):
        obj = SignalsHelper.get_db_instance(instance)

        if not obj:
            # new object
            return True

        # object existed before, check difference
        for field in diff_fields:
            saved_value = getattr(obj, field)
            instance_value = getattr(instance, field)

            if saved_value != instance_value:
                return True

        return False

    @staticmethod
    def _print(message, force_print=False):
        if (settings.DEBUG or force_print) and getattr(settings, 'TEST_PRINT_TASKS', True):
            print(message)


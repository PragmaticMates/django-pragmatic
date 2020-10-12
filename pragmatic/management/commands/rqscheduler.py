import django_rq
from django.apps.registry import Apps, apps
from django.conf import settings
from django_rq.management.commands.rqscheduler import Command as RQSchedulerCommand


class Command(RQSchedulerCommand):
    """
    Runs regular RQ scheduler but deletes all cron jobs at first
    """
    def handle(self, *args, **options):
        self.delete_scheduled_jobs()
        self.schedule_jobs()
        super().handle(*args, **options)

    def delete_scheduled_jobs(self):
        scheduler_name = 'cron'
        print(f'Deleting scheduled jobs [scheduler name = {scheduler_name}]')
        scheduler = django_rq.get_scheduler(scheduler_name)

        # Delete any existing jobs in the scheduler when the app starts up
        for job in scheduler.get_jobs():
            job.delete()

        print('Scheduled jobs deleted.')

    def schedule_jobs(self):
        # for app in [a for a in settings.INSTALLED_APPS if not a.startswith("django.")]:
        #     print(app)

        for app in apps.get_app_configs():
            if hasattr(app, 'schedule_jobs'):
                print(f'Scheduling jobs for app {app.verbose_name} ({app.name})...')
                app.schedule_jobs()

        print('Jobs scheduled')

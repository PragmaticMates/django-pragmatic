# Generated by Django 4.2.3 on 2023-08-16 08:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('pragmatic', '0002_auto_20201207_1214'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deletedobject',
            options={'default_permissions': ('add', 'change', 'delete', 'view'), 'get_latest_by': 'datetime', 'ordering': ('datetime',), 'verbose_name': 'deleted object', 'verbose_name_plural': 'deleted objects'},
        ),
        migrations.AlterField(
            model_name='deletedobject',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='datetime'),
        ),
        migrations.AlterField(
            model_name='deletedobject',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='deletedobject',
            name='object_id',
            field=models.PositiveIntegerField(verbose_name='object ID'),
        ),
        migrations.AlterField(
            model_name='deletedobject',
            name='object_str',
            field=models.CharField(max_length=300, verbose_name='object representation'),
        ),
    ]

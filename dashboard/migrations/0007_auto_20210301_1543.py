# Generated by Django 3.1.6 on 2021-03-01 15:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_auto_20210301_1528'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='slide',
            name='Tag',
        ),
        migrations.AddField(
            model_name='slide',
            name='Filesize',
            field=models.FloatField(default=0),
        ),
    ]
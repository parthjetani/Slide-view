# Generated by Django 2.2.26 on 2022-03-11 11:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_slide_caseno'),
    ]

    operations = [
        migrations.AddField(
            model_name='folder',
            name='organization',
            field=models.CharField(max_length=100, null=True),
        ),
    ]

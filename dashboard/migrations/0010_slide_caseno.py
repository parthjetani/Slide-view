# Generated by Django 2.2.26 on 2022-01-25 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_slide_copyof'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='CaseNo',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]